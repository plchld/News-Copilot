┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR AGENT                       │
│         (Manages prompts & aggregates perspectives)          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│            PHASE 1: TOPIC DISCOVERY & VALIDATION             │
├─────────────────────────────────────────────────────────────┤
│  Discovery Agents (Parallel)                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ Global   │ │  Greek   │ │ Science  │ (etc...)          │
│  │ Politics │ │ Politics │ │   Tech   │                    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                   │
│       │            │            │                            │
│       ▼            ▼            ▼                            │
│  Returns: Topic + Why Important + Key Facts                  │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         PHASE 2: MULTI-PERSPECTIVE DEEP DIVE                 │
│              (For each selected story)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 2.1: GREEK PERSPECTIVE AGENT                       │    │
│  │   - Searches Greek sources independently           │    │
│  │   - Summarizes Greek media consensus              │    │
│  │   - Notes unique Greek angles                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 2.2: INTERNATIONAL PERSPECTIVE AGENT              │    │
│  │   - Searches int'l sources (region-appropriate)   │    │
│  │   - Summarizes global consensus                   │    │
│  │   - Identifies different framings                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 2.3: OPPOSING VIEW AGENT                          │    │
│  │   - Explicitly seeks contrarian sources           │    │
│  │   - Finds what mainstream misses                  │    │
│  │   - Devil's advocate perspective                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 2.4: FACT VERIFICATION AGENT                      │    │
│  │   - Searches for primary sources                  │    │
│  │   - Verifies key claims                          │    │
│  │   - Identifies contested facts                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           PHASE 3: SYNTHESIS & ENRICHMENT                    │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐    │
│  │ 3.1: NARRATIVE SYNTHESIS AGENT                     │    │
│  │   Input: All perspective summaries                 │    │
│  │   Output: Unified story with clear attribution    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 3.2: JARGON & CONTEXT AGENT                       │    │
│  │   Input: Synthesized narrative                     │    │
│  │   Task: Identify & explain complex terms          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 3.3: TIMELINE AGENT                               │    │
│  │   Input: Story topic                              │    │
│  │   Task: Independent historical research           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 4: SOCIAL PULSE (Grok)                    │
└─────────────────────────────────────────────────────────────┘

Detailed Agent Specifications
PHASE 1: Discovery Agents
Each agent independently searches and analyzes:
pythonclass DiscoveryAgent:
    def __init__(self, category):
        self.category = category
        self.search_prompt = f"""
        Find the TOP 5 most important {category} stories for today.
        
        For each story:
        1. Search current news about {category}
        2. Identify why this matters (impact, urgency, relevance)
        3. Extract 3-5 key facts
        4. Note if this has special relevance to Greece
        
        Return structured data, not full articles.
        Focus on: WHO, WHAT, WHEN, WHERE, WHY, IMPACT
        """
    
    def discover(self):
        # Returns distilled insights, not articles
        return {
            "headline": "...",
            "why_important": "...",
            "key_facts": ["fact1", "fact2", "fact3"],
            "greek_relevance": 0.8,
            "initial_sources_found": 12  # Just count, not content
        }
PHASE 2: Multi-Perspective Agents
Each agent independently researches the same topic from different angles:
pythonclass GreekPerspectiveAgent:
    def analyze(self, topic_summary):
        prompt = f"""
        Research how GREEK media is covering: {topic_summary}
        
        Tasks:
        1. Search Greek news sources (mainstream + alternative)
        2. Identify the dominant Greek narrative
        3. Find uniquely Greek concerns/angles
        4. Note what Greek media emphasizes vs ignores
        5. Detect any Greek political spin
        
        Synthesize findings into a 200-word Greek perspective summary.
        Include source diversity (left/right/center).
        """
        # Returns perspective summary, not articles

class InternationalPerspectiveAgent:
    def analyze(self, topic_summary, story_category):
        # Adapts search based on story type
        if story_category == "global_economics":
            search_regions = ["US financial press", "London markets", "EU coverage"]
        elif story_category == "middle_east":
            search_regions = ["Arabic sources", "Israeli press", "Western coverage"]
        
        prompt = f"""
        Research INTERNATIONAL coverage of: {topic_summary}
        Search in: {search_regions}
        
        Tasks:
        1. Find how different regions frame this story
        2. Identify what each region emphasizes
        3. Note cultural/political biases in coverage
        4. Find facts that appear globally vs locally
        
        Synthesize into 200-word international perspective.
        """

class OpposingViewAgent:
    def analyze(self, topic_summary):
        prompt = f"""
        Find CONTRARIAN and ALTERNATIVE views on: {topic_summary}
        
        Tasks:
        1. Search for opposing narratives
        2. Find what mainstream media might be missing
        3. Look for independent journalists' takes
        4. Check fact-checker sites for disputed claims
        5. Find reasonable skepticism (not conspiracy theories)
        
        Synthesize alternative perspectives in 150 words.
        """

class FactVerificationAgent:
    def verify(self, topic_summary, claimed_facts):
        prompt = f"""
        VERIFY key claims about: {topic_summary}
        
        Tasks:
        1. Find primary sources (official statements, data)
        2. Check multiple reliable sources for each fact
        3. Identify which facts are contested
        4. Note confidence level for each claim
        5. Find what we definitively know vs speculation
        
        Return fact verification report.
        """
PHASE 3: Synthesis Agents
pythonclass NarrativeSynthesisAgent:
    def synthesize(self, all_perspectives):
        prompt = f"""
        Given these perspectives:
        - Greek view: {all_perspectives['greek']}
        - International view: {all_perspectives['international']}
        - Alternative view: {all_perspectives['opposing']}
        - Verified facts: {all_perspectives['facts']}
        
        Create a unified 400-word narrative that:
        1. Presents the complete picture
        2. Clearly attributes different viewpoints
        3. Highlights agreements and divergences
        4. Maintains neutral tone
        5. Prioritizes verified facts
        """

class JargonContextAgent:
    def process(self, synthesized_narrative):
        prompt = f"""
        Analyze this narrative: {synthesized_narrative}
        
        Tasks:
        1. Identify technical terms, acronyms, complex concepts
        2. Research simple explanations for each
        3. Add Greek translations where helpful
        4. Provide essential context for understanding
        
        Return jargon dictionary with explanations.
        """

class TimelineAgent:
    def build_timeline(self, topic_summary):
        prompt = f"""
        Research the history of: {topic_summary}
        
        Tasks:
        1. Find key events leading to current situation
        2. Identify cause-effect relationships
        3. Note pattern repetitions (if any)
        4. Mark crucial turning points
        5. Keep to 5-7 most important events
        
        Return chronological timeline with context.
        """
PHASE 4: Social Pulse (Grok)
pythonclass SocialPulseAgent:
    def analyze(self, topic_summary):
        # Uses Grok's real-time capability
        prompt = f"""
        Analyze X (Twitter) discussion about: {topic_summary}
        
        Tasks:
        1. Find trending discussions
        2. Identify main sentiment clusters
        3. Spot key influencer takes
        4. Detect misinformation spreading
        5. Find questions people are asking
        
        Synthesize social media pulse in 150 words.
        """
Orchestration Strategy
pythonclass NewsIntelligenceOrchestrator:
    async def generate_story_intelligence(self, topic):
        # Phase 2: Parallel perspective gathering
        perspectives = await asyncio.gather(
            self.greek_agent.analyze(topic),
            self.international_agent.analyze(topic),
            self.opposing_agent.analyze(topic),
            self.fact_agent.verify(topic)
        )
        
        # Phase 3: Sequential synthesis
        # (Each builds on previous summaries, not raw articles)
        narrative = await self.synthesis_agent.synthesize(perspectives)
        jargon = await self.jargon_agent.process(narrative)
        timeline = await self.timeline_agent.build_timeline(topic)
        
        # Phase 4: Real-time social
        social = await self.social_agent.analyze(topic)
        
        return {
            "narrative": narrative,
            "perspectives": perspectives,
            "jargon": jargon,
            "timeline": timeline,
            "social_pulse": social
        }
Key Design Principles
1. Self-Contained Agents

Each agent performs its own searches
No dependency on previous agents' raw data
Only passes distilled insights forward

2. Prompt Engineering for Search

Specific search instructions per agent
Region/language guidance built into prompts
Clear output format requirements

3. Perspective Isolation

Each perspective agent searches independently
Prevents contamination between viewpoints
Allows true multi-angle analysis

4. Progressive Refinement

Start broad (discovery)
Add perspectives (deep dive)
Synthesize (unification)
Enrich (context/timeline)

5. Graceful Degradation

If one perspective agent fails, others continue
Missing perspectives noted in final output
Quality score based on perspective completeness

Output Example
json{
  "story": {
    "headline": "EU Proposes Sweeping AI Regulations",
    "narrative": "The European Union has unveiled...[400 words synthesizing all perspectives]",
    "perspectives": {
      "greek": {
        "summary": "Greek media focuses on impact to local startups...",
        "unique_angles": ["Concern about brain drain", "Opportunity for compliance industry"],
        "source_diversity": "high"
      },
      "international": {
        "summary": "Global tech press sees this as Brussels overreach...",
        "regional_differences": {
          "US": "Innovation killer",
          "China": "Competitive advantage",
          "EU": "Necessary protection"
        }
      },
      "alternative": {
        "summary": "Critics argue regulations written by tech lobbies...",
        "key_points": ["Loopholes for big tech", "Burden on small companies"]
      }
    },
    "verified_facts": {
      "confirmed": ["Vote date: March 15", "Applies to companies over 10M users"],
      "contested": ["Implementation timeline", "Penalty amounts"],
      "confidence": 0.85
    },
    "jargon": {
      "Foundation Models": {
        "explanation": "AI systems trained on broad data...",
        "greek": "Θεμελιώδη Μοντέλα"
      }
    },
    "timeline": [
      {"date": "2021-04", "event": "First AI regulation draft"},
      {"date": "2023-06", "event": "ChatGPT triggers urgency"},
      // ...
    ],
    "social_pulse": {
      "sentiment": "mixed",
      "top_concerns": ["Innovation impact", "Compliance costs"],
      "trending_hashtags": ["#AIAct", "#BrusselsEffect"]
    }
  }
}
This architecture works without scraping by having each agent be a complete research unit, with the cascade being about building layers of understanding rather than passing article content.