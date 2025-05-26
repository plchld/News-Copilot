"""
Tests for Pydantic schema validation and agent integration with structured outputs.
"""
import pytest
import pytest_asyncio # For async fixtures and tests
from unittest.mock import AsyncMock, MagicMock # For mocking Grok client

from pydantic import ValidationError

# Import all Pydantic models from the schemas module
from api.agents.schemas import (
    GreekContent,
    JargonTerm, JargonAnalysis,
    NewsSource, Viewpoint, ViewpointsAnalysis,
    Verdict, FactSource, FactClaim, FactCheckAnalysis,
    PoliticalPosition, BiasIndicator, BiasAnalysis,
    TimelineEvent, TimelineAnalysis,
    ExpertCredentials, ExpertOpinion, ExpertAnalysis,
    Sentiment, XPost, DiscussionTheme, XPulseAnalysis
)

# Import agent classes
from api.agents import (
    JargonAgent,
    ViewpointsAgent,
    FactCheckAgent,
    BiasAnalysisAgent,
    TimelineAgent,
    ExpertOpinionsAgent,
    # XPulseAgent and its sub-agents will be imported if defined in api.agents.__init__
    # For now, let's assume they might need to be imported directly if not in __init__
)
# Assuming XPulse sub-agents might be defined within x_pulse_agent.py and need specific import
# from api.agents.x_pulse_agent import KeywordExtractorAgent, XSearchAgent, ThemeAnalyzerAgent, XPulseAgent
# For now, let's try to get them via api.agents, if they are exposed.
# If not, the test file for x_pulse_agent might be separate or require direct path imports.

# Placeholder for XPulseAgent and its sub-models if they are not in schemas.py
# These were defined locally in x_pulse_agent.py in a previous step.
# For testing, they ideally should be importable or redefined here.
# To avoid making this file too long, I will focus on schemas from schemas.py first.
# Testing local models from x_pulse_agent.py would require either:
# 1. Moving them to schemas.py
# 2. Importing them directly: from api.agents.x_pulse_agent import KeywordExtractionResult, ...
# 3. Redefining them here for test purposes (less ideal).
# For now, I will assume the main schemas are the priority as per the task.

# --- Mock Grok Client and Response Objects ---
class MockGrokMessage:
    def __init__(self, parsed_model_instance):
        self.parsed = parsed_model_instance

class MockGrokChoice:
    def __init__(self, parsed_model_instance):
        self.message = MockGrokMessage(parsed_model_instance)

class MockGrokUsage:
    def __init__(self, total_tokens=100):
        self.total_tokens = total_tokens

class MockGrokResponse:
    def __init__(self, parsed_model_instance):
        self.choices = [MockGrokChoice(parsed_model_instance)]
        self.usage = MockGrokUsage()

@pytest.fixture
def mock_grok_client():
    """Fixture to create a mock Grok client."""
    client = MagicMock()
    # The method to mock is async_client.beta.chat.completions.parse
    client.async_client = MagicMock()
    client.async_client.beta = MagicMock()
    client.async_client.beta.chat = MagicMock()
    client.async_client.beta.chat.completions = MagicMock()
    client.async_client.beta.chat.completions.parse = AsyncMock()
    return client

# --- Test Class for Pydantic Schema Validation ---
class TestSchemaValidation:
    """Validates Pydantic schemas defined in api.agents.schemas.py"""

    def test_greek_content_validator(self):
        class TestModel(GreekContent):
            text: str
        
        tm = TestModel(text="Αυτό είναι ελληνικό περιεχόμενο.")
        assert tm.text == "Αυτό είναι ελληνικό περιεχόμενο."
        # The validator currently passes all strings, actual Greek char validation is optional
    
    # --- JargonAnalysis Schemas ---
    def test_jargon_term_valid(self):
        data = {"term": "ΕΚΤ", "explanation": "Ευρωπαϊκή Κεντρική Τράπεζα", "category": "οικονομικός"}
        term = JargonTerm(**data)
        assert term.term == data["term"]
        assert term.explanation == data["explanation"]
        assert term.category == data["category"]

    def test_jargon_term_invalid_explanation_short(self):
        with pytest.raises(ValidationError):
            JargonTerm(term="ΕΚΤ", explanation="Τράπεζα") # Too short

    def test_jargon_analysis_valid(self):
        data = {
            "terms": [
                {"term": "ΑΕΠ", "explanation": "Ακαθάριστο Εγχώριο Προϊόν", "category": "οικονομικός"}
            ],
            "summary": "Απλή ανάλυση ορολογίας."
        }
        analysis = JargonAnalysis(**data)
        assert len(analysis.terms) == 1
        assert analysis.summary == data["summary"]

    def test_jargon_analysis_invalid_no_terms(self):
        with pytest.raises(ValidationError): # terms is min_items=1
            JargonAnalysis(terms=[], summary="Test")
            
    def test_jargon_analysis_invalid_term_object(self):
        with pytest.raises(ValidationError):
            JargonAnalysis(terms=[{"term": "ΑΕΠ"}]) # Missing explanation

    # --- ViewpointsAnalysis Schemas ---
    def test_viewpoint_valid(self):
        data = {
            "perspective": "Κυβερνητική άποψη",
            "argument": "Η κυβέρνηση υποστηρίζει ότι τα μέτρα είναι απαραίτητα για την ανάπτυξη της οικονομίας και την προσέλκυση επενδύσεων.",
            "source": NewsSource.KATHIMERINI,
            "source_url": "https://kathimerini.gr/article1",
            "key_difference": "Τονίζει τα θετικά των μέτρων."
        }
        vp = Viewpoint(**data)
        assert vp.perspective == data["perspective"]
        assert vp.source == NewsSource.KATHIMERINI

    def test_viewpoint_invalid_source(self):
        with pytest.raises(ValidationError):
            Viewpoint(perspective="Test", argument="Test argument min length fifty chars.", source="Invalid Source", key_difference="Test diff")

    def test_viewpoints_analysis_valid(self):
        vp_data = {
            "perspective": "Αντιπολιτευτική κριτική",
            "argument": "Η αντιπολίτευση ασκεί κριτική για τις κοινωνικές επιπτώσεις των νέων οικονομικών μέτρων που προωθούνται.",
            "source": NewsSource.EFSYN,
            "key_difference": "Εστιάζει στις αρνητικές κοινωνικές επιπτώσεις."
        }
        data = {
            "viewpoints": [vp_data, {**vp_data, "perspective": "Άλλη οπτική"}], # min_items=2
            "consensus_points": ["Όλοι συμφωνούν ότι η οικονομία είναι δύσκολη."]
        }
        analysis = ViewpointsAnalysis(**data)
        assert len(analysis.viewpoints) == 2
        assert len(analysis.consensus_points) == 1

    # --- FactCheckAnalysis Schemas ---
    def test_fact_source_valid(self):
        data = {"description": " επίσημη ιστοσελίδα", "url": "https://example.gov", "reliability": "High"}
        fs = FactSource(**data)
        assert fs.url == data["url"]

    def test_fact_claim_valid(self):
        data = {
            "claim": "Ο πληθωρισμός μειώθηκε κατά 5%",
            "verdict": Verdict.MOSTLY_TRUE,
            "explanation": "Ο πληθωρισμός μειώθηκε σημαντικά, αλλά τα στοιχεία δείχνουν 4.8% και όχι ακριβώς 5%, οπότε είναι κυρίως αληθές.",
            "evidence": ["Στατιστικά στοιχεία από την ΕΛΣΤΑΤ.", "Δηλώσεις οικονομολόγων."],
            "sources": [{"description": "ΕΛΣΤΑΤ", "url": "https://statistics.gr", "reliability": "High"}]
        }
        fc = FactClaim(**data)
        assert fc.verdict == Verdict.MOSTLY_TRUE

    def test_fact_claim_invalid_verdict(self):
        with pytest.raises(ValidationError):
            FactClaim(claim="Test", verdict="Maybe True", explanation="x"*100, evidence=[], sources=[{"description":"d","url":"u","reliability":"h"}])

    def test_factcheck_analysis_valid(self):
        claim_data = {
            "claim": "Test claim", "verdict": Verdict.TRUE, 
            "explanation": "This is a detailed explanation that is definitely over one hundred characters long to satisfy the validation requirements.",
            "evidence": ["e1"], 
            "sources": [{"description":"s1","url":"http://s1.com","reliability":"High"}]
        }
        data = {
            "claims": [claim_data], # min_items=1
            "overall_credibility": "Μέτρια",
            "red_flags": ["Κάποια σημεία χωρίς πηγές"],
            "missing_context": "Λείπει η διεθνής διάσταση."
        }
        analysis = FactCheckAnalysis(**data)
        assert len(analysis.claims) == 1
        assert analysis.overall_credibility == "Μέτρια"

    # --- BiasAnalysis Schemas ---
    def test_bias_indicator_valid(self):
        data = {"indicator": "Loaded Language", "example": "Η 'βάρβαρη' επίθεση...", "impact": "Creates negative sentiment."}
        bi = BiasIndicator(**data)
        assert bi.indicator == data["indicator"]

    def test_bias_analysis_valid(self):
        indicator_data = {"indicator": "TestInd", "example": "TestEx", "impact": "TestImp"}
        data = {
            "political_leaning": PoliticalPosition.CENTER_LEFT,
            "economic_position": "Κοινωνική δημοκρατία",
            "bias_indicators": [indicator_data], # min_items=1
            "missing_perspectives": ["Δεν αναφέρεται η άποψη των μικρομεσαίων επιχειρήσεων."],
            "objectivity_score": 6,
            "reasoning": "Η ανάλυση βασίζεται στους δείκτες προκατάληψης και στις ελλείπουσες προοπτικές που εντοπίστηκαν στο άρθρο. Η οικονομική θέση προκύπτει από τις προτεινόμενες λύσεις του αρθρογράφου. Η βαθμολογία αντικειμενικότητας είναι 6 λόγω αυτών των παραγόντων."
        }
        analysis = BiasAnalysis(**data)
        assert analysis.objectivity_score == 6
        assert len(analysis.reasoning) >= 200

    def test_bias_analysis_invalid_score(self):
        with pytest.raises(ValidationError):
            BiasAnalysis(political_leaning=PoliticalPosition.CENTER, economic_position="Test", bias_indicators=[], missing_perspectives=[], objectivity_score=11, reasoning="x"*200)

    # --- TimelineAnalysis Schemas ---
    def test_timeline_event_valid(self):
        data = {
            "date": "2023-01-15", "title": "Νέα νομοθεσία", 
            "description": "Ψηφίστηκε ο νέος νόμος.", 
            "importance": "Κρίσιμο", "source": "Εφημερίδα της Κυβερνήσεως", "verified": True
        }
        event = TimelineEvent(**data)
        assert event.importance == "Κρίσιμο"

    def test_timeline_analysis_valid(self):
        event_data = {
            "date": "2023-01-01", "title": "Event 1", "description": "Desc 1", 
            "importance": "Σημαντικό", "source": "Source 1", "verified": True
        }
        data = {
            "story_title": "Η πορεία προς τις εκλογές",
            "events": [event_data, {**event_data, "date":"2023-01-02"}, {**event_data, "date":"2023-01-03"}], # min_items=3
            "duration": "1 μήνας",
            "key_turning_points": ["Η ανακοίνωση της νέας συμμαχίας"],
            "future_implications": "Αναμένονται εντάσεις."
        }
        analysis = TimelineAnalysis(**data)
        assert len(analysis.events) == 3

    # --- ExpertAnalysis Schemas ---
    def test_expert_credentials_valid(self):
        data = {"name": "Γιάννης Παπαδόπουλος", "title": "Καθηγητής Οικονομικών", "affiliation": " Πανεπιστήμιο Αθηνών", "expertise_area": "Δημόσια Οικονομικά"}
        ec = ExpertCredentials(**data)
        assert ec.name == data["name"]
        
    def test_expert_opinion_valid(self):
        cred_data = {"name": "Ελένη Ιωάννου", "title": "Ερευνήτρια", "affiliation": "ΕΛΚΕΘΕ", "expertise_area": "Κλιματική Αλλαγή"}
        data = {
            "expert": cred_data,
            "stance": "Υπέρ",
            "main_argument": "Η μετάβαση σε ανανεώσιμες πηγές ενέργειας είναι κρίσιμη και πρέπει να επιταχυνθεί άμεσα για την αντιμετώπιση της κλιματικής κρίσης.",
            "key_quote": "Δεν υπάρχει χρόνος για χάσιμο.",
            "source_url": "https://example.com/interview",
            "date": "2023-05-10"
        }
        eo = ExpertOpinion(**data)
        assert eo.stance == "Υπέρ"
        assert len(eo.main_argument) >= 100

    def test_expert_analysis_valid(self):
        cred_data = {"name": "Nikos", "title": "Dr", "affiliation": "Uni", "expertise_area": "AI"}
        op_data = {"expert": cred_data, "stance": "Κατά", "main_argument": "Argument against something very specific and well explained to meet the minimum length requirement for this particular field."}
        data = {
            "topic_summary": "Συζήτηση για την τεχνητή νοημοσύνη.",
            "experts": [op_data, {**op_data, "stance": "Ουδέτερος"}], # min_items=2
            "consensus_level": "Μερική",
            "key_debates": ["Ηθικά ζητήματα", "Ρυθμιστικό πλαίσιο"],
            "emerging_perspectives": ["AI και τέχνη"]
        }
        analysis = ExpertAnalysis(**data)
        assert len(analysis.experts) == 2

    # --- XPulseAnalysis Schemas ---
    def test_xpost_valid(self):
        data = {
            "content": "Πολύ ενδιαφέρουσα εξέλιξη στο θέμα Χ.", 
            "author_description": "Δημοσιογράφος", 
            "engagement_level": "High", 
            "timestamp_relative": "1 ώρα πριν"
        }
        post = XPost(**data)
        assert post.engagement_level == "High"

    def test_discussion_theme_valid(self):
        post_data1 = {"content": "Post 1", "author_description": "UserA", "engagement_level": "Low"}
        post_data2 = {"content": "Post 2", "author_description": "UserB", "engagement_level": "Medium"}
        data = {
            "theme_title": "Ανησυχία για οικονομία",
            "theme_summary": "Πολλοί χρήστες εκφράζουν ανησυχία για τις τρέχουσες οικονομικές εξελίξεις και τον αντίκτυπο στην καθημερινότητά τους.",
            "sentiment": Sentiment.NEGATIVE,
            "representative_posts": [post_data1, post_data2], # min_items=2
            "prevalence": "Κυρίαρχο"
        }
        dt = DiscussionTheme(**data)
        assert dt.sentiment == Sentiment.NEGATIVE
        assert len(dt.representative_posts) == 2

    def test_xpulse_analysis_valid(self):
        post_data = {"content": "Sample post", "author_description": "Citizen", "engagement_level": "Medium"}
        theme_data = {
            "theme_title": "Theme 1", 
            "theme_summary": "Summary for theme 1, ensuring it is long enough to pass validation criteria of minimum length one hundred characters.",
            "sentiment": Sentiment.NEUTRAL,
            "representative_posts": [post_data, {**post_data, "content":"Another post"}],
            "prevalence": "Συχνό"
        }
        data = {
            "overall_discourse_summary": "Γενική σύνοψη της συζήτησης στο Χ.",
            "total_posts_analyzed": 1500,
            "discussion_themes": [theme_data, {**theme_data, "theme_title":"Theme 2"}], # min_items=2
            "trending_hashtags": ["#οικονομια", "#αναπτυξη"],
            "overall_sentiment": Sentiment.MIXED,
            "key_influencers": ["@influencer1 (ανώνυμο προφίλ)", "Ομάδα Πολιτών Χ"],
            "data_caveats": "Η ανάλυση περιορίζεται σε δημόσια posts."
        }
        analysis = XPulseAnalysis(**data)
        assert analysis.total_posts_analyzed == 1500
        assert len(analysis.discussion_themes) == 2
        assert analysis.overall_sentiment == Sentiment.MIXED

    def test_xpulse_analysis_invalid_sentiment(self):
        with pytest.raises(ValidationError):
            XPulseAnalysis(overall_discourse_summary="s", total_posts_analyzed=1, discussion_themes=[], overall_sentiment="MaybePositive", data_caveats="c")


# --- Test Class for Agent Integration with Structured Outputs ---
@pytest.mark.asyncio # Mark this class for asyncio tests
class TestAgentStructuredOutputIntegration:
    """
    Tests agent execution with mocked Grok client to ensure structured output
    is correctly generated and validated against Pydantic models.
    """

    async def test_jargon_agent_structured_output(self, mock_grok_client):
        """Test JargonAgent returns valid JargonAnalysis structured output."""
        agent = JargonAgent.create(mock_grok_client)
        
        # Prepare the Pydantic model instance that the mock Grok will return
        expected_jargon_analysis = JargonAnalysis(
            terms=[
                JargonTerm(term="ΕΚΤ", explanation="Ευρωπαϊκή Κεντρική Τράπεζα", category="Οικονομικός Οργανισμός"),
                JargonTerm(term="QE", explanation="Ποσοτική Χαλάρωση, ένα μέτρο νομισματικής πολιτικής.", category="Οικονομικός Όρος")
            ],
            summary="Η ανάλυση περιέχει οικονομικούς όρους."
        )
        mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_jargon_analysis)
        
        context = {
            "article_text": "Η ΕΚΤ ανακοίνωσε QE μέτρα για την τόνωση του ΑΕΠ.",
            "article_url": "https://example.com/article_with_jargon",
        }
        
        result = await agent.execute(context)
        
        assert result.success
        assert result.data is not None
        # Validate that result.data (which is model_dump() from base_agent) can be parsed back into the Pydantic model
        try:
            validated_data = JargonAnalysis(**result.data)
            assert len(validated_data.terms) == 2
            assert validated_data.terms[0].term == "ΕΚΤ"
        except ValidationError as e:
            pytest.fail(f"JargonAgent output failed Pydantic validation: {e}")

    async def test_viewpoints_agent_structured_output(self, mock_grok_client):
        agent = ViewpointsAgent.create(mock_grok_client)
        expected_viewpoints_analysis = ViewpointsAnalysis(
            viewpoints=[
                Viewpoint(perspective="Κυβερνητική Άποψη", argument="Τα μέτρα είναι θετικά και θα τονώσουν την οικονομία άμεσα.", source=NewsSource.KATHIMERINI, key_difference=" θετική"),
                Viewpoint(perspective="Αντιπολιτευτική Κριτική", argument="Τα μέτρα είναι ανεπαρκή και δεν αντιμετωπίζουν τις ρίζες του προβλήματος ουσιαστικά.", source=NewsSource.EFSYN, key_difference="αρνητική")
            ],
            consensus_points=["Η οικονομία χρειάζεται στήριξη."]
        )
        mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_viewpoints_analysis)
        context = {"article_text": "Κείμενο άρθρου για απόψεις.", "article_url": "http://example.com/opinions"}
        result = await agent.execute(context)
        assert result.success
        assert result.data is not None
        try:
            validated_data = ViewpointsAnalysis(**result.data)
            assert len(validated_data.viewpoints) == 2
            assert validated_data.consensus_points[0] == "Η οικονομία χρειάζεται στήριξη."
        except ValidationError as e:
            pytest.fail(f"ViewpointsAgent output failed Pydantic validation: {e}")

    async def test_factcheck_agent_structured_output(self, mock_grok_client):
        agent = FactCheckAgent.create(mock_grok_client)
        expected_factcheck_analysis = FactCheckAnalysis(
            claims=[
                FactClaim(claim="Ο ήλιος ανατέλλει από την δύση.", verdict=Verdict.FALSE, 
                          explanation="Αυτό είναι λάθος. Ο ήλιος ανατέλλει πάντα από την ανατολή λόγω της περιστροφής της Γης.",
                          evidence=["Γενικές γνώσεις αστρονομίας."],
                          sources=[FactSource(description="Βιβλίο Φυσικής", url="http://example.com/physics", reliability="High")])
            ],
            overall_credibility="Χαμηλή λόγω βασικών ανακριβειών.",
            red_flags=["Περιέχει προφανώς ψευδείς ισχυρισμούς."],
        )
        mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_factcheck_analysis)
        context = {"article_text": "Το άρθρο ισχυρίζεται ότι ο ήλιος ανατέλλει από την δύση.", "article_url": "http://example.com/facts"}
        result = await agent.execute(context)
        assert result.success
        assert result.data is not None
        try:
            validated_data = FactCheckAnalysis(**result.data)
            assert validated_data.claims[0].verdict == Verdict.FALSE
        except ValidationError as e:
            pytest.fail(f"FactCheckAgent output failed Pydantic validation: {e}")

    async def test_bias_analysis_agent_structured_output(self, mock_grok_client):
        agent = BiasAnalysisAgent.create(mock_grok_client)
        expected_bias_analysis = BiasAnalysis(
            political_leaning=PoliticalPosition.CENTER,
            economic_position="Μεικτή οικονομία με έμφαση στον ιδιωτικό τομέα.",
            bias_indicators=[
                BiasIndicator(indicator=" επιλεκτική παρουσίαση", example="Παράδειγμα επιλεκτικής παρουσίασης γεγονότων.", impact="Μερική εικόνα της πραγματικότητας.")
            ],
            missing_perspectives=["Δεν αναλύεται η κοινωνική διάσταση επαρκώς."],
            objectivity_score=5,
            reasoning="Η ανάλυση έδειξε μέτρια αντικειμενικότητα λόγω της επιλεκτικής παρουσίασης ορισμένων γεγονότων και της παράλειψης σημαντικών κοινωνικών προοπτικών που θα μπορούσαν να προσφέρουν μια πιο ολοκληρωμένη εικόνα της κατάστασης που περιγράφεται."
        )
        mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_bias_analysis)
        context = {"article_text": "Ένα άρθρο με κεντρώα πολιτική τοποθέτηση.", "article_url": "http://example.com/bias_article"}
        result = await agent.execute(context)
        assert result.success
        assert result.data is not None
        try:
            validated_data = BiasAnalysis(**result.data)
            assert validated_data.objectivity_score == 5
        except ValidationError as e:
            pytest.fail(f"BiasAnalysisAgent output failed Pydantic validation: {e}")

    async def test_timeline_agent_structured_output(self, mock_grok_client):
        agent = TimelineAgent.create(mock_grok_client)
        expected_timeline_analysis = TimelineAnalysis(
            story_title="Εξέλιξη ενός σημαντικού γεγονότος",
            events=[
                TimelineEvent(date="2023-01-01", title="Έναρξη", description="Το γεγονός ξεκίνησε.", importance="Κρίσιμο", source="Πηγή Α", verified=True),
                TimelineEvent(date="2023-01-15", title="Κορύφωση", description="Το γεγονός έφτασε στην κορύφωσή του.", importance="Κρίσιμο", source="Πηγή Β", verified=True),
                TimelineEvent(date="2023-02-01", title="Λήξη", description="Το γεγονός έληξε.", importance="Σημαντικό", source="Πηγή Γ", verified=True)
            ],
            duration="1 μήνας",
            key_turning_points=["Η απόφαση της 10ης Ιανουαρίου."]
        )
        mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_timeline_analysis)
        context = {"article_text": "Αυτό το άρθρο περιγράφει την εξέλιξη ενός γεγονότος.", "article_url": "http://example.com/timeline_story"}
        result = await agent.execute(context)
        assert result.success
        assert result.data is not None
        try:
            validated_data = TimelineAnalysis(**result.data)
            assert len(validated_data.events) == 3
        except ValidationError as e:
            pytest.fail(f"TimelineAgent output failed Pydantic validation: {e}")

    async def test_expert_opinions_agent_structured_output(self, mock_grok_client):
        agent = ExpertOpinionsAgent.create(mock_grok_client)
        expert_cred = ExpertCredentials(name="Δρ. Άννα Εμπειρογνώμων", title="Καθηγήτρια Πανεπιστημίου", affiliation=" Πανεπιστήμιο Αιγαίου", expertise_area="Τεχνητή Νοημοσύνη")
        expected_expert_analysis = ExpertAnalysis(
            topic_summary="Οι προκλήσεις της ηθικής στην Τεχνητή Νοημοσύνη και οι πιθανές επιπτώσεις στην κοινωνία.",
            experts=[
                ExpertOpinion(expert=expert_cred, stance="Μικτός", main_argument="Η ΤΝ προσφέρει τεράστιες δυνατότητες αλλά εγείρει σοβαρά ηθικά διλήμματα που χρήζουν άμεσης αντιμετώπισης και νομοθετικού πλαισίου για την προστασία.", key_quote="Η πρόοδος πρέπει να συμβαδίζει με την ηθική.")
            ],
            consensus_level="Μερική Συναίνεση",
            key_debates=["Αυτονομία των συστημάτων ΤΝ.", "Προστασία ιδιωτικότητας."]
        )
        # Need to ensure the main_argument is > 100 chars.
        current_len = len(expected_expert_analysis.experts[0].main_argument)
        if current_len < 100:
            padding = " " * (100 - current_len)
            expected_expert_analysis.experts[0].main_argument += padding
            
        mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_expert_analysis)
        context = {"article_text": "Το άρθρο συζητά για την ΤΝ.", "article_url": "http://example.com/ai_experts"}
        result = await agent.execute(context)
        assert result.success
        assert result.data is not None
        try:
            validated_data = ExpertAnalysis(**result.data)
            assert len(validated_data.experts) == 1
            assert validated_data.experts[0].expert.name == "Δρ. Άννα Εμπειρογνώμων"
        except ValidationError as e:
            pytest.fail(f"ExpertOpinionsAgent output failed Pydantic validation: {e}")

    # XPulseAgent test would be more complex due to its nested nature.
    # It would involve mocking sub-agent executions and then the final _post_process LLM call.
    # For now, this provides a good base for the other agents.
    # A full XPulseAgent test would look like:
    # 1. Mock KeywordExtractorAgent.execute() to return valid KeywordExtractionResult
    # 2. Mock XSearchAgent.execute() to return valid XSearchResults
    # 3. Mock ThemeAnalyzerAgent.execute() to return valid SubAgentThemeList
    # 4. Then mock the grok_client.async_client.beta.chat.completions.parse for XPulseAgent's _post_process call to return XPulseAnalysis
    # This is significantly more involved.
    
    # Example for a sub-agent of XPulse, assuming KeywordExtractorAgent is importable
    # and uses a Pydantic model `KeywordExtractionResult` (defined in x_pulse_agent.py or schemas.py)
    # async def test_keyword_extractor_agent_output(self, mock_grok_client):
    #     from api.agents.x_pulse_agent import KeywordExtractorAgent, KeywordExtractionResult # Assuming these are importable
    #     agent = KeywordExtractorAgent.create(mock_grok_client)
    #     expected_keywords = KeywordExtractionResult(
    #         main_topic="Κύριο Θέμα",
    #         key_entities=["Οντότητα1", "Οργανισμός2"],
    #         x_search_keywords=["λέξη1", "φράση2"]
    #     )
    #     mock_grok_client.async_client.beta.chat.completions.parse.return_value = MockGrokResponse(expected_keywords)
    #     context = {"article_text": "Δείγμα κειμένου για εξαγωγή λέξεων κλειδιών."}
    #     result = await agent.execute(context)
    #     assert result.success
    #     assert result.data is not None
    #     try:
    #         KeywordExtractionResult(**result.data)
    #     except ValidationError as e:
    #         pytest.fail(f"KeywordExtractorAgent output failed Pydantic validation: {e}")

# TODO: Add more specific invalid data tests for each schema.
# TODO: Add integration test for XPulseAgent and its sub-agents if they are exposed and use Pydantic models.
# The current tests cover the main schemas and agents listed in the initial plan.I have created the `tests/test_structured_outputs.py` file and populated it with:
1.  **Basic Structure:** Imports, mock Grok client setup (`MockGrokResponse`, `mock_grok_client` fixture).
2.  **Pydantic Schema Validation Unit Tests (`TestSchemaValidation`):**
    *   Added initial valid and some invalid data tests for:
        *   `JargonTerm`, `JargonAnalysis`
        *   `Viewpoint`, `ViewpointsAnalysis` (including `NewsSource` enum)
        *   `FactSource`, `FactClaim`, `FactCheckAnalysis` (including `Verdict` enum)
        *   `BiasIndicator`, `BiasAnalysis` (including `PoliticalPosition` enum)
        *   `TimelineEvent`, `TimelineAnalysis`
        *   `ExpertCredentials`, `ExpertOpinion`, `ExpertAnalysis`
        *   `XPost`, `DiscussionTheme`, `XPulseAnalysis` (including `Sentiment` enum)
    *   These tests cover basic instantiation with valid data and use `pytest.raises(ValidationError)` for simple invalid cases (e.g., missing fields, enum mismatches, string length violations).
3.  **Agent Integration Tests for Structured Outputs (`TestAgentStructuredOutputIntegration`):**
    *   Added asynchronous test methods for:
        *   `JargonAgent`
        *   `ViewpointsAgent`
        *   `FactCheckAgent`
        *   `BiasAnalysisAgent`
        *   `TimelineAgent`
        *   `ExpertOpinionsAgent`
    *   Each test:
        *   Initializes the respective agent with the `mock_grok_client`.
        *   Creates an instance of the agent's Pydantic `response_model` (e.g., `JargonAnalysis` for `JargonAgent`) filled with valid sample data.
        *   Configures the `mock_grok_client.async_client.beta.chat.completions.parse` method to return this Pydantic model instance wrapped in the `MockGrokResponse`.
        *   Executes the agent with a sample `context`.
        *   Asserts `result.success is True` and `result.data is not None`.
        *   **Critically, re-validates `result.data`** by parsing it back into the agent's Pydantic model (e.g., `JargonAnalysis(**result.data)`), ensuring the `model_dump()` process in the base agent produced a valid and complete dictionary.
    *   A placeholder comment and structure for testing `XPulseAgent` and its sub-agents are included, noting their complexity.

**Next Steps/Areas for Expansion (as noted by TODOs in the file):**
*   Add more comprehensive invalid data test cases for each Pydantic schema, covering a wider range of validation rules and edge cases.
*   Complete the integration tests for `XPulseAgent`, which will require mocking its sub-agent execution chain and the final LLM call in `_post_process`.
*   Add focused integration tests for `XPulseAgent`'s sub-agents (`KeywordExtractorAgent`, `XSearchAgent`, `ThemeAnalyzerAgent`) by mocking their specific LLM calls and checking their respective (locally defined) Pydantic model outputs, assuming these local models are made accessible for testing or moved to `schemas.py`.

The current state of `tests/test_structured_outputs.py` provides a solid foundation for testing the structured output functionality for the primary agents and schemas.
