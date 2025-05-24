# Grok Live Search & Prompt Engineering Enhancements for News-Copilot

This document outlines a series of proposed enhancements to News-Copilot's integration with Grok Live Search and its prompt engineering strategies. The goal is to maximize the utility of Grok's new features, improve the reliability and accuracy of AI-generated analyses, and ultimately build greater trust with our users.

## Part 1: Leveraging Grok Live Search Advanced Features

Currently, News-Copilot utilizes a basic implementation of Grok Live Search. We can significantly improve our service by leveraging its more advanced capabilities.

### 1.1. Current State

*   All Grok calls use hard-coded `search_parameters`: `{mode:"on", return_citations:true, sources:[web,news]}`.
*   Advanced features like date ranges, country filtering, `safe_search`, X (Twitter) handle specific searches, RSS feed integration, `max_search_results`, and `excluded_websites` are not used.
*   UI/API clients have limited control over search parameters, primarily for "mode" and "sources" in deep analysis.

### 1.2. Proposed Enhancements & Immediate Opportunities

**A. Geo-targeted Greek Coverage:**
*   **Action:** Add `country:"GR"` by default to all web/news search sources.
*   **Benefit:** Higher relevance for local Greek news outlets.
*   **UI:** Toggle to "widen" search (remove country filter).
*   **Grok API `search_parameters` Example:**
    ```json
    {
      "mode": "auto",
      "sources": [
        { "type": "web", "country": "GR" },
        { "type": "news", "country": "GR" }
      ]
    }
    ```

**B. Precision Time Windows:**
*   **Action:**
    *   Timeline/breaking news: Inject `{from_date: "YYYY-MM-DD", to_date: "YYYY-MM-DD"}`.
    *   Fact-checking historical articles: Allow user-defined date ranges.
*   **Benefit:** More focused and relevant search results for time-sensitive analyses.
*   **Grok API `search_parameters` Example (for news in the last 24 hours):**
    ```json
    {
      "mode": "on",
      "from_date": "2023-10-26", // Replace with dynamic date
      "to_date": "2023-10-27",   // Replace with dynamic date
      "sources": [
        { "type": "news", "country": "GR" }
      ]
    }
    ```

**C. Strategic X (Twitter) Integration for Unique Insights (Key USP):**
*   **Note:** Direct X integration is a powerful USP, allowing access to real-time commentary, official statements, and expert discussions not always captured by traditional news cycles.
*   **Action:**
    *   Utilize `sources: [{ "type": "x", "x_handles": ["handle1", "handle2"] }]` with curated lists of Greek academics, ministries, journalists, public figures, and relevant organizations.
    *   UI: Allow power-users to input additional X handles for specific investigations.
    *   Use for tracking official announcements, expert debates, and the unfolding of events in real-time.
*   **Benefit:** More targeted and credible expert opinions, official statements, and real-time information flow directly from X.
*   **Grok API `search_parameters` Example (search specific X handles):**
    ```json
    {
      "mode": "auto",
      "sources": [
        { "type": "x", "x_handles": ["grok", "xai"] }
      ]
    }
    ```

**D. Noise / Propaganda Filtering:**
*   **Action:**
    *   Maintain a list (e.g., YAML file) of low-credibility sites mapped to `excluded_websites` (max 5 per source type per request).
    *   UI: "Strict mode" ( `safe_search:true` + exclusions) vs. "Investigative mode" ( `safe_search:false`, results labeled accordingly).
*   **Benefit:** Improved quality of information and user control over content filtering.
*   **Grok API `search_parameters` Example (excluding a website from web search):**
    ```json
    {
      "mode": "auto",
      "sources": [
        { "type": "web", "excluded_websites": ["exampledomain.com"], "safe_search": true }
      ]
    }
    ```

**E. Leaner, Cheaper Calls:**
*   **Action:** Cap `max_search_results` (e.g., 5-10) for prompts needing only a few authoritative hits. Default to 20 for deep analysis.
*   **Benefit:** Cost optimization without sacrificing quality for simpler queries.
*   **CLI:** Add a `--lite` flag.
*   **Grok API `search_parameters` Example (limiting results):**
    ```json
    {
      "mode": "on",
      "max_search_results": 5,
      "sources": [ { "type": "news" } ]
    }
    ```

**F. RSS Fast Lanes:**
*   **Action:** For high-quality, known RSS feeds, use `sources: [{ "type": "rss", "links": ["https://example.com/feed.xml"] }]`. Grok API currently supports one RSS link per RSS source entry.
*   **Benefit:** Faster and more direct access to information from trusted, specific feeds.
*   **Implementation:** Plugin list for RSS feeds, manageable without code changes.
*   **Grok API `search_parameters` Example (using an RSS feed):**
    ```json
    {
      "mode": "on",
      "sources": [
        { "type": "rss", "links": ["https://status.x.ai/feed.xml"] }
      ]
    }
    ```

**G. Auto/On Mode Intelligence:**
*   **Action:** Default to `mode:"auto"` for free-tier users (Grok decides when to search, potentially cheaper). Force `mode:"on"` for premium/admin users.
*   **Benefit:** Cost management and guaranteed freshness for premium tiers.

### 1.3. Suggested Architectural Tweaks

**1. Centralized `search_params` Builder:**
*   Create a new Python module, e.g., `api/search_params_builder.py`.
    ```python
    # api/search_params_builder.py
    import json

    def build_search_params(
        mode="auto",
        *,
        sources=None, # Expects a list of source dicts e.g. [{"type":"web"}, {"type":"x"}]
        country="GR", # Default to Greece for web/news
        from_date=None,
        to_date=None,
        max_results=20,
        safe_search=True, # Default for web/news
        excluded_websites_map=None, # e.g. {"web": ["site1.com"], "news": ["site2.com"]}
        x_handles_for_x_source=None, # List of handles for type:"x"
        rss_links_for_rss_source=None, # List containing a single URL for type:"rss"
    ) -> dict:
        """Return a fully-formed search_parameters object for Grok API."""
        processed_sources = sources if sources is not None else [{"type": "web"}, {"type": "news"}]

        def enrich_source(source_item):
            enriched = dict(source_item) # Work on a copy
            source_type = enriched.get("type")

            if source_type in ("web", "news"):
                if country:
                    enriched["country"] = country
                enriched["safe_search"] = safe_search
                if excluded_websites_map and excluded_websites_map.get(source_type):
                    enriched["excluded_websites"] = excluded_websites_map[source_type][:5] # Max 5
            
            if source_type == "x":
                if x_handles_for_x_source:
                    enriched["x_handles"] = x_handles_for_x_source
            
            if source_type == "rss":
                if rss_links_for_rss_source: # Grok API current expects a list with one link
                    enriched["links"] = rss_links_for_rss_source[:1]
            return enriched

        final_params = {
            "mode": mode,
            "return_citations": True, # Always true for our use case
            "max_search_results": max_results,
            "sources": [enrich_source(s) for s in processed_sources],
        }

        if from_date:
            final_params["from_date"] = from_date # ISO8601 format "YYYY-MM-DD"
        if to_date:
            final_params["to_date"] = to_date     # ISO8601 format "YYYY-MM-DD"

        return final_params
    ```
*   **Usage:** Import and use this builder in `GrokClient.get_default_search_params()` and wherever `search_parameters` are constructed. The `excluded_websites_map` allows specifying different exclusions for web vs. news. For `x_handles` and `rss_links`, ensure the `sources` list passed to `build_search_params` includes an entry like `{"type": "x"}` or `{"type": "rss"}` respectively for those parameters to be applied.
*   **Benefit:** Centralized logic, easier updates, allows CLI/HTTP callers to override specific fields.

**2. API Surface Update:**
*   **Action:** Extend `/augment` and `/deep-analysis` JSON request bodies to accept an optional `searchParams` object. This object's fields will be passed as arguments to `build_search_params()`.
*   **Backwards Compatibility:** If `searchParams` is omitted, use current default behaviors (enhanced by the new builder).

**3. Prompt-Level Tuning in `analysis_handlers.py`:**
*   **Action:** Tailor `search_params` presets for different analysis types by calling `build_search_params` with specific arguments:
    *   Timeline Analysis: `build_search_params(from_date=..., to_date=..., max_results=15)`
    *   Expert Opinions: `build_search_params(sources=[{"type":"x", "x_handles":['expert1','expert2']}, {"type":"news"}])`
    *   Bias Analysis: `build_search_params(safe_search=False)` (clearly label results).

**4. Configuration & Feature Flags:**
*   **Action:** Add to `.env` (and `api/config.py`):
    *   `DEFAULT_COUNTRY_CODE="GR"`
    *   `DEFAULT_SEARCH_MODE_FREE_TIER="auto"`
    *   `DEFAULT_SEARCH_MODE_PREMIUM_TIER="on"`
    *   `EXCLUDED_SITES_CONFIG_PATH="config/low_quality_sites.yml"` (or similar for `excluded_websites_map`)
*   **Benefit:** Easy configuration of default behaviors.

**5. Caching Layer (Optional but Recommended):**
*   **Action:** Implement Redis (or similar) caching for Grok responses.
*   **Key:** `sha256(prompt_text + json.dumps(sorted_search_params_items))`
*   **Benefit:** Significant cost and latency reduction for repeated requests on the same article or similar queries.

### 1.4. UI/UX Wins

*   Extension UI: "Search Scope" dropdown (e.g., Greece / World / Custom Date Range).
*   Toggles for "Include X (Twitter) posts" (this would add/configure the X source), "Quick (cheaper) / Deep (richer)" analysis (adjusts `max_search_results`).
*   Display the number of search results/citations used.
*   On citation hover, show source type (Web, News, X, RSS) - if available in Grok's response.

### 1.5. Risk & Ethics Checklist

*   **Privacy:** Update privacy notice regarding Live Search request data sharing with xAI during beta (until June 5, 2025).
*   **Content Warning:** If `safe_search:false` is used, clearly mark results: "Προσοχή: Τα αποτελέσματα ενδέχεται να περιλαμβάνουν ακατάλληλο ή παραπλανητικό περιεχόμενο."
*   **Cost Control:** Rate-limit `mode:"on"` for free users during beta.
*   **Logging:** Anonymously log all `search_parameters` sent to Grok for future cost optimization analysis.

### 1.6. Immediate Low-Effort / High-Impact Tasks

1.  **Implement `build_search_params`** in `api/search_params_builder.py` and add unit tests.
2.  **Refactor `GrokClient.get_default_search_params`** to use the new builder.
3.  **Update API endpoints** (`/augment`, `/deep-analysis`) and CLI to accept and pass `searchParams` to the builder. Update any API documentation.
4.  **Apply `country:"GR"` and `max_search_results=10` (or similar)** as new defaults for quick augmentations using the builder.
5.  **Create a basic `low_quality_sites.yml`** (or JSON) and integrate its loading into the logic that calls `build_search_params` for the `excluded_websites_map` field.

## Part 2: Hardening Prompts for Reliability and Trust

To ensure Grok returns accurate, verifiable, and schema-compliant information, we need to refine our prompting strategies.

### 2.1. Re-usable Prompt Building Blocks

*   Create a new helper module, e.g., `api/prompt_utils.py`.

    ```python
    # api/prompt_utils.py
    import json

    SYSTEM_PREFIX = """
    Είσαι το News-Copilot, ένας βοηθός ανάλυσης ειδήσεων AI που:
    * Εργάζεται για Έλληνες αναγνώστες.
    * ΠΡΕΠΕΙ να επεξεργάζεται τις σκέψεις του σε ένα ιδιωτικό πρόχειρο (scratchpad).
    * ΠΡΕΠΕΙ να εξάγει ΜΟΝΟ την τελική απάντηση στα Ελληνικά.
    * Αν τα διαθέσιμα στοιχεία δεν επαρκούν, απαντά "Άγνωστο" αντί να υποθέτει.
    """

    TRUST_GUARDRAILS = """
    ΚΡΙΤΙΚΟΙ ΚΑΝΟΝΕΣ ΠΟΙΟΤΗΤΑΣ:
    1. Κάθε πραγματική δήλωση ΠΡΕΠΕΙ να υποστηρίζεται από τουλάχιστον μία πηγή (citation).
    2. Οι πηγές (citations) ΠΡΕΠΕΙ να είναι URLs που όντως περιέχουν το κείμενο/δεδομένα που αναφέρονται.
    3. Εάν δεν βρεθεί αξιόπιστη πηγή, γράψε ρητά: "Δεν βρέθηκαν αξιόπιστες πηγές για αυτήν την πληροφορία."
    4. ΜΗΝ επινοείς στατιστικά, ημερομηνίες ή αποσπάσματα.
    5. Σκέψου βήμα-προς-βήμα στα Ελληνικά μέσα σε ⧼SCRATCHPAD⧽ ... ⧼END_SCRATCHPAD⧽. Διέγραψε το scratchpad πριν την τελική απάντηση.
       (Η απάντηση προς τον χρήστη ξεκινά μετά την ετικέτα: ### ΑΠΟΤΕΛΕΣΜΑΤΑ ###)
    """

    def get_jargon_response_schema():
        # Ensure this aligns with your Pydantic model api.models.JargonResponse
        return {
            "type": "object",
            "properties": {
                "terms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "explanation": {"type": "string"},
                            "sources": {
                                "type": "array",
                                "items": {"type": "string", "format": "url"},
                                "minItems": 1
                            }
                        },
                        "required": ["term", "explanation", "sources"]
                    }
                }
            },
            "required": ["terms"]
        }


    def get_alternative_viewpoints_schema():
        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_title": {"type": "string"},
                    "provider": {"type": "string"}, 
                    "published_date": {"type": "string"}, # Consider format: "date" or descriptive
                    "difference_summary": {"type": "string"},
                    "url": {"type": "string", "format": "url"}
                },
                "required": ["source_title", "provider", "difference_summary", "url"]
            }
        }

    JSON_ENVELOPE = lambda schema_obj: f"""### ΑΠΟΤΕΛΕΣΜΑΤΑ ###

Παρακαλώ, δώσε την απάντηση αποκλειστικά σε μορφή JSON που να ταιριάζει ακριβώς με το παρακάτω σχήμα:
```json
{json.dumps(schema_obj, ensure_ascii=False, indent=2)}
```
Μην συμπεριλάβεις markdown fences γύρω από το JSON. Δεν επιτρέπονται επιπλέον πεδία (keys) στο JSON.
"""

    def build_prompt(task_instruction: str, json_schema_definition: dict = None) -> str:
        prompt_parts = [SYSTEM_PREFIX, TRUST_GUARDRAILS, task_instruction]
        if json_schema_definition:
            prompt_parts.append(JSON_ENVELOPE(json_schema_definition))
        return "\\n\\n".join(prompt_parts)

    def inject_runtime_search_context(prompt: str, search_params: dict) -> str:
        if not search_params:
            return prompt
        
        contextual_params = {k: v for k, v in search_params.items() if v is not None}
        if not contextual_params:
            return prompt

        pretty_params = json.dumps(contextual_params, ensure_ascii=False, indent=2)
        return f"{prompt}\\n\\n### Ενεργές Παράμετροι Αναζήτησης (Live Search) για Πληροφορία ###\\n```json\\n{pretty_params}\\n```\\nΑξιοποίησε αυτές τις παραμέτρους για να καθοδηγήσεις την αναζήτησή σου."
    ```

### 2.2. Hardened Prompt Examples

**A. Jargon / Term Explanations:**
*   **Instruction Logic:**
    ```python
    # In prompts.py or equivalent
    # from .prompt_utils import build_prompt, get_jargon_response_schema

    def get_jargon_task_instruction(article_text: str) -> str:
        return f"""Εντόπισε ΜΟΝΟ τους μη προφανείς τεχνικούς όρους, οργανισμούς ή ιστορικές αναφορές από το παρακάτω άρθρο.
Για κάθε όρο, δώσε μια σαφή εξήγηση 1-2 προτάσεων στα Ελληνικά.
Για κάθε εξήγηση, ΠΡΕΠΕΙ να παραθέσεις τουλάχιστον μία πηγή (URL) που την υποστηρίζει στο πεδίο "sources".
Το τελικό αποτέλεσμα ΠΡΕΠΕΙ να είναι ένα JSON αντικείμενο. Το άρθρο προς ανάλυση είναι:
\\n\\nΆρθρο:\\n{article_text}"""

    # Example usage:
    # article_content = "..."
    # instruction = get_jargon_task_instruction(article_content)
    # GROK_CONTEXT_JARGON_PROMPT = build_prompt(instruction, get_jargon_response_schema())
    ```
*   **Key Changes:** Added mandatory "sources" array with `minItems: 1` to the JSON schema for each term.

**B. Alternative Viewpoints:**
*   **Instruction Logic:**
    ```python
    # from .prompt_utils import build_prompt, get_alternative_viewpoints_schema

    def get_alt_view_task_instruction(article_text: str) -> str:
        return f"""Βρες 4 έως 8 αξιόπιστες πηγές (κατά προτίμηση Ελληνικές) που καλύπτουν την ίδια είδηση με το αρχικό άρθρο.
Για κάθε πηγή, περίγραψε συνοπτικά (σε 1-3 προτάσεις) πώς η κάλυψή της διαφέρει ή προσθέτει στην αρχική ιστορία.
Ανάφερε νέα γεγονότα, διαφορετικές οπτικές, ελλιπείς λεπτομέρειες ή αντικρουόμενες δηλώσεις.
Τα υποχρεωτικά πεδία για κάθε πηγή είναι: "source_title", "provider", "published_date", "difference_summary", και "url".
Το τελικό αποτέλεσμα ΠΡΕΠEI να είναι ένας JSON πίνακας (array). Το αρχικό άρθρο είναι:
\\n\\nΠρωτότυπο Άρθρο:\\n{article_text}"""

    # Example usage:
    # article_content = "..."
    # instruction = get_alt_view_task_instruction(article_content)
    # GROK_ALT_VIEW_PROMPT = build_prompt(instruction, get_alternative_viewpoints_schema())
    ```
*   **Key Changes:** Defined a clear JSON schema for the list of alternative viewpoints.

**C. Deep Analysis Prompts (Fact-check, Bias, Timeline, Expert):**
*   For existing JSON-based deep analysis prompts:
    *   **Integrate `TRUST_GUARDRAILS`**: Add this block to the beginning of each prompt by using `build_prompt`.
    *   **Mandate Sources**: Review their schemas (defined in `analysis_handlers.py`'s `_get_analysis_schemas`) to ensure every claim/data point has a corresponding "sources" array (list of URLs) and `minItems: 1` where applicable.
    *   **Enums for Ratings**: Change string types to enums: `{"type": "string", "enum": ["υψηλή", "μέτρια", "χαμηλή", "άγνωστο"]}`.
    *   **Explicit Scratchpad Usage**: Ensure `build_prompt` correctly includes these directives.

### 2.3. Parameter-Aware Prompts

*   **Action:** Before sending the prompt to Grok, inject context about the `search_parameters` being used. Use `inject_runtime_search_context` from `prompt_utils.py`.
    ```python
    # Example in analysis_handlers.py or grok_client.py
    # task_specific_instruction = get_jargon_task_instruction(article_text)
    # base_prompt = build_prompt(task_specific_instruction, get_jargon_response_schema())
    # current_search_params = build_search_params(...) # Using the builder from Part 1
    # final_prompt_for_grok = inject_runtime_search_context(base_prompt, current_search_params)
    # completion = self.grok_client.create_completion(prompt=final_prompt_for_grok, search_params=current_search_params, ...)
    ```
*   **Benefit:** Reminds the model of active filters, potentially improving its internal search strategy. Note: `search_params` is also passed directly to the Grok API via `extra_body`. The injection into the prompt is for model awareness.

### 2.4. Self-Critique Loop (Optional but Powerful)

*   **Concept:** After Grok returns a JSON response, make a second, quick Grok call to critique it.
*   **Critic Prompt:**
    ```python
    # In prompt_utils.py
    SELF_CRITIQUE_PROMPT_TEMPLATE = lambda schema_str, json_to_check_str: build_prompt(
        # Note: The critic prompt itself doesn't need a JSON schema for its *own* output if it's simple "OK" or text.
        f"""Έλεγξε το παρακάτω JSON αντικείμενο ως προς τους εξής κανόνες:
1. Συμμόρφωση με το Σχήμα: Είναι το JSON 100% συμβατό με το παρακάτω σχήμα; Έλεγξε τύπους, required πεδία, enums.
   Schema: ```json
   {schema_str}
   ```
2. Ποιότητα Πηγών: Περιέχει κάθε αντικείμενο που απαιτεί πηγές, τουλάχιστον μία έγκυρη URL στο πεδίο "sources"; (Εάν το schema απαιτεί πηγές).
3. Κανόνες Αξιοπιστίας: Υπάρχουν παραβιάσεις των ΚΡΙΤΙΚΩΝ ΚΑΝΟΝΩΝ ΠΟΙΟΤΗΤΑΣ (π.χ. ισχυρισμοί χωρίς πηγές, εφευρέσεις);

Εάν όλα είναι σωστά, απάντησε ΜΟΝΟ με τη λέξη "OK".
Αλλιώς, δώσε μια σύντομη λίστα με τα προβλήματα που εντόπισες και προτεινόμενες διορθώσεις, στα Ελληνικά.

JSON προς έλεγχο:
```json
{json_to_check_str}
```"""
    )
    ```
*   **Logic:**
    1.  Receive initial JSON from Grok.
    2.  Get the expected schema string (e.g., `json.dumps(get_jargon_response_schema())`).
    3.  Format `SELF_CRITIQUE_PROMPT_TEMPLATE` with this schema string and the received JSON string.
    4.  Call Grok with this critic prompt.
    5.  If critic's response is NOT "OK", handle accordingly (log, flag, attempt self-correction).
*   **Benefit:** Automated quality check for schema and content rules.

### 2.5. Implementation Steps for Prompt Hardening

1.  **Create `api/prompt_utils.py`**: Populate with all helper functions and constants.
2.  **Refactor `prompts.py`**: Define instruction-generating functions and use `build_prompt()` from `prompt_utils.py` to construct full prompts.
3.  **Modify `api/analysis_handlers.py` (and `api/grok_client.py`):**
    *   Call instruction-generating functions with `article_text`.
    *   Call `build_prompt()` to get the base prompt.
    *   Call `build_search_params()` (from Part 1) to get `search_parameters`.
    *   Call `inject_runtime_search_context()` to add search context to the prompt string.
    *   Pass both the final prompt string and the `search_parameters` dictionary to `grok_client.create_completion()`.
    *   (Optional) Implement the self-critique loop.
4.  **Update Pydantic Models (`api/models.py`) and Schemas:** Ensure perfect alignment between Pydantic models, JSON schemas used in `_get_analysis_schemas` (in `analysis_handlers.py`), and those defined in `prompt_utils.py`.
5.  **Thoroughly Test:** Validate prompt rendering, schema correctness, API compliance, and error handling.

By implementing these enhancements, News-Copilot can provide more reliable, verifiable, and contextually rich analyses, significantly boosting user trust and the overall value of the platform.