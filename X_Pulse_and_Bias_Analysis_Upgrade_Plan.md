# News-Copilot: X Pulse & Bias Analysis Upgrade Plan

## 1. Introduction and Goals

This document outlines the plan to implement two major upgrades to the News-Copilot extension:

1.  **X Pulse Feature**: Replace the current "Expert Opinions" module with a dynamic "X Pulse" module. This feature will analyze and summarize discussions on X (formerly Twitter) related to the news article being viewed, providing users with a snapshot of public discourse, key themes, and prevalent viewpoints. This is inspired by the multi-stage LLM approach for real-time analysis, adapted for News-Copilot's architecture using Grok's search and analysis capabilities.
2.  **Enhanced Bias and Language Analysis**: Refine the existing "Bias and Language Analysis" module to:
    *   Implement a more nuanced political spectrum mapping relevant to the Greek political scene, moving beyond a simple left-right scale.
    *   Improve the presentation and explanation of loaded language and framing techniques.

The primary goal is to provide users with richer, more transparent, and less biased contextual information to augment their news reading experience.

## 2. Phase 1: X Pulse Implementation

This phase focuses on building the "X Pulse" feature. Unlike a direct real-time X stream, News-Copilot will leverage Grok's ability to search X and analyze the findings.

### Step 2.1: Article Topic and Keyword Extraction

*   **Objective**: Identify the core topic, key entities, and relevant keywords from the input news article to fuel the X search.
*   **Process**:
    1.  The existing `fetch_text(article_url)` function in `api/analysis_handlers.py` will provide the article content.
    2.  A new prompt will be designed for Grok to extract these key elements.
*   **Prompt Design (`get_article_topic_extraction_instruction` - to be added to `api/prompt_utils.py`):**
    ```python
    def get_article_topic_extraction_instruction(article_text: str) -> str:
        return f"""Analyze the provided news article text.
    Identify and extract the following:
    1. Main Topic: A concise phrase describing the core subject of the article.
    2. Key Entities: A list of important people, organizations, locations, or specific terms mentioned.
    3. Search Keywords: A list of 3-5 keywords or short phrases suitable for searching for related discussions on X (Twitter). Prioritize terms that are likely to yield relevant public discourse in Greek.

    Article Text:
    {article_text}
    """
    ```
*   **Schema (`get_article_topic_extraction_schema` - to be added to `api/prompt_utils.py`):**
    ```python
    def get_article_topic_extraction_schema() -> dict:
        return {
            "type": "object",
            "properties": {
                "main_topic": {"type": "string", "description": "Core subject of the article."},
                "key_entities": {"type": "array", "items": {"type": "string"}},
                "x_search_keywords": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["main_topic", "key_entities", "x_search_keywords"]
        }
    ```
*   **API Call (Conceptual within `AnalysisHandler`):**
    A dedicated Grok call or integrated into the main X Pulse analysis. For efficiency, this could be the first step within a larger X Pulse prompt.

### Step 2.2: X Discussion Analysis (Simulating Filtering & In-depth Analysis)

This step combines the idea of filtering high-signal posts and performing in-depth analysis, adapted for a single powerful Grok call based on its search results from X.

*   **Objective**: Use Grok to search X for discussions relevant to the extracted topic/keywords and then analyze these discussions to identify themes, representative viewpoints, and overall discourse sentiment.
*   **Process**:
    1.  The keywords from Step 2.1 will be used to construct targeted search parameters for Grok, focusing on X as a source.
    2.  A comprehensive prompt will instruct Grok to perform the search, internally identify the most relevant/substantive X posts from its search results, and then analyze this selection.
*   **Search Parameter Configuration (in `analysis_handlers.py` when calling `grok_client.create_completion` for X Pulse):**
    *   Dynamically construct `search_params` using keywords from Step 2.1.
    *   Specify X as a primary source.
    *   Target Greek language posts (`language: "el"`).
    *   Example `search_params` structure to be built:
        ```python
        # Example, actual keywords from topic extraction
        keywords = extracted_keywords # ["keyword1", "keyword2"]
        search_query_for_x = " OR ".join(keywords) + " lang:el" # Adjust for Grok syntax if needed

        search_params = build_search_params(
            # query=search_query_for_x, # If Grok supports direct query override for sources
            sources=["x"], # Prioritize X
            language="el",
            country="GR",
            # Potentially use keywords in a more structured way if API supports
            # custom_filters_for_x_source=f"({search_query_for_x}) -is:retweet"
        )
        ```
        *Note: The exact method to make Grok focus its X search on these keywords needs to align with Grok API's capabilities for source-specific queries. The `XAI_API_KEY` and `grok_client` are already in use; this is about tailoring the `search_params` for the `expert` analysis type, which will be repurposed for "X Pulse".*

*   **Prompt Design (`get_x_pulse_analysis_task_instruction` - to replace/modify `get_expert_opinions_task_instruction` in `api/prompt_utils.py`):**
    ```python
    def get_x_pulse_analysis_task_instruction(article_text: str, article_main_topic: str, article_x_keywords: List[str]) -> str:
        keyword_str = ", ".join(article_x_keywords)
        return f"""You are an AI news analysis assistant. Your task is to provide an "X Pulse" analysis for the following news article.
    The main topic of the article is: '{article_main_topic}'.
    Focus your X (Twitter) search and analysis on discussions related to these keywords: {keyword_str}.
    The primary language for X posts should be Greek.

    Instructions:
    1.  Based on your Live Search of X (Twitter) using the topic and keywords, identify relevant public discussions in Greek.
    2.  From these discussions, identify 3-5 dominant themes or distinct viewpoints.
    3.  For each theme/viewpoint:
        a.  Provide a concise title (2-5 words).
        b.  Write a 1-2 sentence summary explaining the theme/viewpoint.
        c.  Extract or summarize 1-2 representative X posts (tweets) that clearly illustrate this theme/viewpoint. Attribute them generally (e.g., "an X user stated...") unless the source is a verified public figure or organization explicitly making a statement. Focus on the content of the discourse.
        d.  Briefly describe the general sentiment or tone surrounding this theme on X (e.g., "Critical concern", "Strongly supportive", "Mixed reactions", "Informative discussion").
    4.  Provide an overall summary of the X discourse related to the article's topic.

    Original Article for Context (do not summarize the article itself in the output, use it for context only):
    {article_text}

    Return ALL output in Greek.
    """
    ```

*   **Schema (`get_x_pulse_analysis_schema` - to replace/modify `get_expert_opinions_schema` in `api/prompt_utils.py`):**
    ```python
    def get_x_pulse_analysis_schema() -> dict:
        return {
            "type": "object",
            "properties": {
                "overall_discourse_summary": {
                    "type": "string",
                    "description": "Συνολική περίληψη της συζήτησης στο X σχετικά με το θέμα του άρθρου."
                },
                "discussion_themes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme_title": {"type": "string", "description": "Τίτλος θέματος/άποψης (π.χ., 'Ανησυχίες για οικονομικές επιπτώσεις')"},
                            "theme_summary": {"type": "string", "description": "Περίληψη 1-2 προτάσεων του θέματος/άποψης."},
                            "representative_posts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "post_content": {"type": "string", "description": "Αντιπροσωπευτικό απόσπασμα ή περίληψη ανάρτησης από το X."},
                                        "post_source_description": {"type": "string", "description": "Περιγραφή πηγής (π.χ., 'Ανάρτηση χρήστη X', 'Δήλωση από [Όνομα Οργανισμού στο X]')"}
                                    },
                                    "required": ["post_content", "post_source_description"]
                                },
                                "description": "Αντιπροσωπευτικές αναρτήσεις ή περιλήψεις."
                            },
                            "sentiment_around_theme": {"type": "string", "description": "Γενικό συναίσθημα/τόνος (π.χ., 'Έντονη κριτική', 'Θετική υποδοχή', 'Μικτές αντιδράσεις')"}
                        },
                        "required": ["theme_title", "theme_summary", "representative_posts", "sentiment_around_theme"]
                    }
                },
                "data_caveats": {
                    "type": "string",
                    "description": "Προειδοποίηση σχετικά με τη φύση των δεδομένων από το X.",
                    "default": "Η ανάλυση αυτή αντικατοπτρίζει ένα στιγμιότυπο των συζητήσεων στο X και ενδέχεται να μην είναι αντιπροσωπευτική της ευρύτερης κοινής γνώμης ή επαληθευμένων γεγονότων. Οι απόψεις που εκφράζονται ανήκουν στους χρήστεES του X."
                }
            },
            "required": ["overall_discourse_summary", "discussion_themes", "data_caveats"]
        }
    ```

*   **API Call and Integration (`api/analysis_handlers.py`):**
    1.  Modify the `get_deep_analysis` method in `AnalysisHandler`.
    2.  When `analysis_type` is `'expert'` (this will be renamed to `'x-pulse'` conceptually, or the frontend request type will change):
        *   (Optional first call, if topic extraction is separate) Extract topic/keywords from `article_text`.
        *   Prepare `search_params` for Grok, emphasizing X and Greek language, using extracted keywords.
        *   Use `build_prompt` with the new `get_x_pulse_analysis_task_instruction` and `get_x_pulse_analysis_schema`.
        *   The `article_text`, `article_main_topic`, and `article_x_keywords` will need to be passed to `get_x_pulse_analysis_task_instruction`.
        *   The `citation_processor.validate_citations` part for experts will likely be removed or heavily adapted, as we are no longer focusing on specific pre-defined "experts" but rather on themes from the discourse. Citations will still be important to know *which* X posts Grok considered.
*   **File Changes:**
    *   `api/analysis_handlers.py`: Modify `get_deep_analysis` for the new "X Pulse" logic. Change `analysis_type == 'expert'` handling.
    *   `api/prompt_utils.py`:
        *   Add `get_article_topic_extraction_instruction` and `get_article_topic_extraction_schema` (if used as a separate step).
        *   Replace `get_expert_opinions_task_instruction` with `get_x_pulse_analysis_task_instruction`.
        *   Replace `get_expert_opinions_schema` with `get_x_pulse_analysis_schema`.
    *   `prompts.py`: The `GROK_EXPERT_OPINIONS_PROMPT` will be deprecated/removed as its logic moves to `prompt_utils.py` for dynamic construction.
    *   Frontend: Update UI to display X Pulse data. The request to the backend for `deep-analysis` might change its `analysisType` parameter from `"expert"` to `"x-pulse"`.

## 3. Phase 2: Bias and Language Analysis Enhancements

This phase refines the existing bias analysis module.

### Step 3.1: Design and Integrate Greek Political Spectrum Matrix

*   **Objective**: Replace the simple left-right political lean assessment with a more nuanced matrix reflecting the Greek political landscape (e.g., Economic axis: Left-Right; Social axis: Progressive-Conservative).
*   **Research & Design (Potentially Offline Task)**:
    1.  Define the axes for the Greek political spectrum (e.g., Economic, Social, stance on EU, stance on national issues). This requires expertise in Greek politics.
    2.  For each axis, define key characteristics, ideologies, and potentially associated political parties or figures in Greece that represent different points on that axis.
    3.  Develop a descriptive framework for how the LLM should map article content to this matrix.
*   **Prompt Engineering (`get_bias_analysis_task_instruction` in `api/prompt_utils.py`):**
    *   The instruction needs to be updated to include the description of the Greek Political Spectrum Matrix.
    *   It must ask the LLM to:
        *   Place the article on each defined axis.
        *   Provide a detailed explanation for its placement on *each axis*, citing specific examples (phrases, arguments, sources used) from the article.
    *   Example addition to the prompt:
        ```python
        # ... (existing bias prompt instructions) ...
        
        Greek Political Spectrum Analysis:
        Analyze the article based on the following two-dimensional Greek political spectrum:
        1.  Economic Axis:
            *   Αριστερά (Κρατικός παρεμβατισμός, κοινωνικοποίηση μέσων παραγωγής, αναδιανομή πλούτου)
            *   Κεντροαριστερά (Μικτή οικονομία με ισχυρό κοινωνικό κράτος, ρύθμιση αγορών)
            *   Κέντρο (Ισορροπία μεταξύ ελεύθερης αγοράς και κοινωνικής προστασίας, δημοσιονομική υπευθυνότητα)
            *   Κεντροδεξιά (Ελεύθερη αγορά με στοχευμένες παρεμβάσεις, μείωση φορολογίας, προσέλκυση επενδύσεων)
            *   Δεξιά (Ελαχιστοποίηση κρατικής παρέμβασης, ιδιωτικοποιήσεις, πλήρης απελευθέρωση αγορών)
        2.  Social Axis:
            *   Προοδευτική (Δικαιώματα ΛΟΑΤΚΙ+, διαχωρισμός κράτους-εκκλησίας, πολυπολιτισμικότητα, ατομικές ελευθερίες)
            *   Φιλελεύθερη (Έμφαση στα ατομικά δικαιώματα, ανεκτικότητα, μεταρρυθμίσεις)
            *   Συντηρητική (Έμφαση στην παράδοση, εθνική ταυτότητα, οικογενειακές αξίες, επιφυλακτικότητα σε ραγδαίες αλλαγές)
        
        For the article provided, determine its position on BOTH the Economic and Social axes.
        Provide a detailed justification for each placement, citing specific examples from the article's text, arguments, or sources.
        If the article does not provide enough information for a clear placement on an axis, indicate "Άγνωστο" or "Δεν είναι σαφές".
        All output MUST be in Greek.
        ```
*   **Schema Update (`get_bias_analysis_schema` in `api/prompt_utils.py`):**
    *   Replace `political_lean` and `confidence` string properties.
    *   Add a new object for the matrix:
    ```python
    # In get_bias_analysis_schema properties:
    "political_spectrum_analysis_greek": {
        "type": "object",
        "properties": {
            "economic_axis_placement": {
                "type": "string",
                "description": "Τοποθέτηση στον οικονομικό άξονα (π.χ., Αριστερά, Κεντροαριστερά, Κέντρο, Κεντροδεξιά, Δεξιά, Ουδέτερο, Άγνωστο)",
                "enum": ["Αριστερά", "Κεντροαριστερά", "Κέντρο", "Κεντροδεξιά", "Δεξιά", "Ουδέτερο", "Άγνωστο/Δεν είναι σαφές"]
            },
            "economic_axis_justification": {
                "type": "string",
                "description": "Αιτιολόγηση για την τοποθέτηση στον οικονομικό άξονα, με παραδείγματα από το άρθρο."
            },
            "social_axis_placement": {
                "type": "string",
                "description": "Τοποθέτηση στον κοινωνικό άξονα (π.χ., Προοδευτική, Φιλελεύθερη, Συντηρητική, Άγνωστο)",
                "enum": ["Προοδευτική", "Φιλελεύθερη", "Μετριοπαθής", "Συντηρητική", "Άγνωστο/Δεν είναι σαφές"]
            },
            "social_axis_justification": {
                "type": "string",
                "description": "Αιτιολόγηση για την τοποθέτηση στον κοινωνικό άξονα, με παραδείγματα από το άρθρο."
            },
            "overall_confidence": {
                "type": "string",
                "description": "Συνολική βεβαιότητα για την ανάλυση του πολιτικού φάσματος (π.χ., Υψηλή, Μέτρια, Χαμηλή).",
                "enum": ["Υψηλή", "Μέτρια", "Χαμηλή"]
            }
        },
        "required": ["economic_axis_placement", "economic_axis_justification", "social_axis_placement", "social_axis_justification", "overall_confidence"]
    }
    ```

### Step 3.2: Enhance Loaded Language and Framing Analysis

*   **Objective**: Provide more context for identified loaded language and make framing analysis clearer.
*   **Prompt Engineering (`get_bias_analysis_task_instruction` in `api/prompt_utils.py`):**
    *   For loaded language: Request not just the words, but a brief explanation of *why* they are considered loaded or what emotional effect they might have in the context of the article.
    *   For framing: Ask for specific framing techniques (e.g., "appeal to emotion," "us vs. them," "problem-solution framing") with examples from the text.
*   **Schema Update (`get_bias_analysis_schema` in `api/prompt_utils.py`):**
    *   Modify `emotional_language` (previously `loaded_words`) and `framing_techniques` (previously `framing`).
    ```python
    # In get_bias_analysis_schema properties:
    "language_and_framing_analysis": {
        "type": "object",
        "properties": {
            "emotionally_charged_terms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "Η φορτισμένη λέξη ή φράση."},
                        "explanation": {"type": "string", "description": "Εξήγηση γιατί η λέξη/φράση είναι φορτισμένη στο συγκεκριμένο πλαίσιο."}
                    },
                    "required": ["term", "explanation"]
                },
                "description": "Λέξεις ή φράσεις με έντονο συναισθηματικό φορτίο."
            },
            "identified_framing_techniques": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "technique_name": {"type": "string", "description": "Όνομα της τεχνικής πλαισίωσης (π.χ., 'Επίκληση στο συναίσθημα')."},
                        "example_from_article": {"type": "string", "description": "Συγκεκριμένο παράδειγμα από το άρθρο."}
                    },
                    "required": ["technique_name", "example_from_article"]
                },
                "description": "Τεχνικές πλαισίωσης που εντοπίστηκαν."
            },
            "detected_tone": { # Renamed from 'tone' for clarity
                "type": "string",
                "enum": ["θετικός", "αρνητικός", "ουδέτερος", "μικτός", "άγνωστος"],
                "description": "Ο γενικός συναισθηματικός τόνος του άρθρου."
            },
            "missing_perspectives_summary": {
                "type": "string",
                "description": "Σύνοψη των οπτικών γωνιών που ενδέχεται να λείπουν από το άρθρο."
            }
        },
        "required": ["emotionally_charged_terms", "identified_framing_techniques", "detected_tone", "missing_perspectives_summary"]
    }
    # The old 'language_analysis' object would be replaced by this 'language_and_framing_analysis' object.
    # The 'comparison' and 'recommendations' fields from the old schema can be kept or re-evaluated.
    ```

*   **File Changes:**
    *   `api/prompt_utils.py`: Update `get_bias_analysis_task_instruction` and `get_bias_analysis_schema` as described.
    *   Frontend: Update UI to display the new structured bias and language information.

## 4. Future Considerations (Post V1 of X Pulse)

*   **Stakeholder Voices Module**: As discussed, this could be a V2 feature, identifying official statements or positions from relevant organizations, NGOs, government bodies, etc., related to the article's topic. This would require different search strategies and prompting than the X Pulse.
*   **Advanced X Analysis**:
    *   Identifying influential X users/communities (with strong caveats about bias and representativeness).
    *   Trend analysis of the X discussion over a short period (if feasible via Grok's search capabilities for time-series data, though less likely for single-article analysis).
*   **User Feedback Mechanism**: Allow users to provide feedback on the helpfulness and perceived bias of the analyses.

## 5. General Implementation Notes

*   **Iterative Development**: Implement and test each step/feature incrementally.
*   **Error Handling**: Robust error handling for API calls and data parsing is crucial.
*   **Localization**: All user-facing output from Grok MUST be in Greek, as already emphasized in existing prompts. This needs to be maintained for all new prompts and schema descriptions.
*   **Testing**: Thoroughly test with a diverse range of news articles to ensure robustness and quality of analysis.
*   **Performance**: Monitor the performance of Grok API calls, especially for the combined search-and-analyze prompts. The X Pulse, in particular, might be more intensive than the previous expert opinions module.
*   **Grok API Versioning**: Ensure compatibility with the Grok API versions being used (`grok-3-fast`, `grok-3-mini` or others as available/chosen). The current `News-Copilot` seems to use a generic `GrokClient` that doesn't specify model versions directly in the `create_completion` call shown in `analysis_handlers.py` but relies on the XAI console default or per-API-key settings. This plan assumes this flexibility. If specific models need to be chosen per task (like the Bitcoin example), `GrokClient` would need adaptation. For `News-Copilot`, it's more likely that one reasoning-capable model is used for deep analysis.

This plan provides a comprehensive roadmap. Modifications may be necessary based on testing and deeper exploration of Grok API capabilities for nuanced X searching and analysis. 