# api/prompt_utils.py
"""
Prompt engineering utilities for hardened, reliable Grok responses.
Implements scratchpad technique and strict citation requirements.
"""

import json
from typing import Dict, Optional, Any, List

# System-level instructions for all prompts
SYSTEM_PREFIX = """
You are News-Copilot, an AI news analysis assistant that:
* Works for Greek readers and MUST provide ALL output in Greek language
* MUST process thoughts in a private scratchpad before the final answer
* MUST output ONLY the final answer in Greek after the scratchpad
* If evidence is insufficient, respond with "Άγνωστο" (Unknown) rather than speculating
* ALL final output text MUST be in Greek, including JSON string values
"""

# Trust and quality guardrails
TRUST_GUARDRAILS = """
CRITICAL QUALITY RULES:
1. For every factual claim, mention WHERE you found this information (e.g., "according to Kathimerini", "as reported by SKAI")
2. DO NOT invent URLs - just mention the source name/publication
3. If no reliable source is found, explicitly state: "Δεν βρέθηκαν αξιόπιστες πηγές για αυτήν την πληροφορία."
4. DO NOT invent statistics, dates, or quotes
5. Think step-by-step in Greek within ⧼SCRATCHPAD⧽ ... ⧼END_SCRATCHPAD⧽ tags
   - Delete the scratchpad before the final answer
   - The user-facing answer starts after the label: ### ΑΠΟΤΕΛΕΣΜΑΤΑ ###
6. Remember: ALL output text values MUST be in Greek language
7. Citations will be automatically collected from your search - focus on mentioning sources naturally in your text
"""


def get_jargon_response_schema() -> dict:
    """
    Get JSON schema for jargon/term explanations.
    Aligns with api.models.JargonResponse
    """
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
                        "source_mention": {"type": "string"}  # Where info came from
                    },
                    "required": ["term", "explanation"]
                }
            }
        },
        "required": ["terms"]
    }


def get_alternative_viewpoints_schema() -> dict:
    """
    Get JSON schema for alternative viewpoints response.
    """
    return {
        "type": "object",
        "properties": {
            "viewpoints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "perspective": {"type": "string", "description": "The main perspective or angle"},
                        "argument": {"type": "string", "description": "The detailed argument or explanation"},
                        "source": {"type": "string", "description": "The source of this viewpoint"},
                        "source_url": {"type": "string", "description": "URL of the source"},
                        "key_difference": {"type": "string", "description": "The key difference in approach"}
                    },
                    "required": ["perspective", "argument"]
                }
            },
            "consensus_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Points of consensus on undisputed facts"
            }
        },
        "required": ["viewpoints"]
    }


def get_fact_check_schema() -> dict:
    """
    Get JSON schema for fact-checking response.
    """
    return {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "evidence_assessment": {
                            "type": "string",
                            "enum": [
                                "ισχυρά τεκμηριωμένο",      # strongly supported
                                "μερικώς τεκμηριωμένο",     # partially supported
                                "αμφιλεγόμενο",             # disputed/contested
                                "ελλιπώς τεκμηριωμένο",     # poorly supported
                                "χωρίς επαρκή στοιχεία",    # insufficient evidence
                                "εκτός πλαισίου"            # out of context
                            ]
                        },
                        "context": {"type": "string"},  # Important context/nuance
                        "complexity_note": {"type": "string"},  # Why this is complex
                        "sources": {
                            "type": "array",
                            "items": {"type": "string", "format": "url"},
                            "minItems": 1
                        }
                    },
                    "required": ["claim", "evidence_assessment", "context", "sources"]
                }
            },
            "source_quality": {
                "type": "object",
                "properties": {
                    "primary_sources": {"type": "integer", "minimum": 0},
                    "secondary_sources": {"type": "integer", "minimum": 0},
                    "source_diversity": {
                        "type": "string",
                        "enum": ["πολύ ποικίλες", "μέτρια ποικιλία", "περιορισμένες", "μονομερείς"]
                    }
                },
                "required": ["primary_sources", "secondary_sources", "source_diversity"]
            }
        },
        "required": ["claims", "source_quality"]
    }


def get_bias_analysis_schema() -> dict:
    """
    Get JSON schema for bias analysis response.
    """
    return {
        "type": "object",
        "properties": {
            "political_spectrum_analysis_greek": {
                "type": "object",
                "properties": {
                    "economic_axis_placement": {
                        "type": "string",
                        "description": "Τοποθέτηση στον οικονομικό άξονα",
                        "enum": ["Αριστερά", "Κεντροαριστερά", "Κέντρο", "Κεντροδεξιά", "Δεξιά", "Ουδέτερο", "Άγνωστο/Δεν είναι σαφές"]
                    },
                    "economic_axis_justification": {
                        "type": "string",
                        "description": "Αιτιολόγηση για την τοποθέτηση στον οικονομικό άξονα, με παραδείγματα από το άρθρο"
                    },
                    "social_axis_placement": {
                        "type": "string",
                        "description": "Τοποθέτηση στον κοινωνικό άξονα",
                        "enum": ["Προοδευτική", "Φιλελεύθερη", "Μετριοπαθής", "Συντηρητική", "Άγνωστο/Δεν είναι σαφές"]
                    },
                    "social_axis_justification": {
                        "type": "string",
                        "description": "Αιτιολόγηση για την τοποθέτηση στον κοινωνικό άξονα, με παραδείγματα από το άρθρο"
                    },
                    "overall_confidence": {
                        "type": "string",
                        "description": "Συνολική βεβαιότητα για την ανάλυση του πολιτικού φάσματος",
                        "enum": ["Υψηλή", "Μέτρια", "Χαμηλή"]
                    }
                },
                "required": ["economic_axis_placement", "economic_axis_justification", 
                            "social_axis_placement", "social_axis_justification", "overall_confidence"]
            },
            "language_and_framing_analysis": {
                "type": "object",
                "properties": {
                    "emotionally_charged_terms": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "term": {"type": "string", "description": "Η φορτισμένη λέξη ή φράση"},
                                "explanation": {"type": "string", "description": "Εξήγηση γιατί η λέξη/φράση είναι φορτισμένη στο συγκεκριμένο πλαίσιο"}
                            },
                            "required": ["term", "explanation"]
                        },
                        "description": "Λέξεις ή φράσεις με έντονο συναισθηματικό φορτίο"
                    },
                    "identified_framing_techniques": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "technique_name": {"type": "string", "description": "Όνομα της τεχνικής πλαισίωσης"},
                                "example_from_article": {"type": "string", "description": "Συγκεκριμένο παράδειγμα από το άρθρο"}
                            },
                            "required": ["technique_name", "example_from_article"]
                        },
                        "description": "Τεχνικές πλαισίωσης που εντοπίστηκαν"
                    },
                    "detected_tone": {
                        "type": "string",
                        "enum": ["θετικός", "αρνητικός", "ουδέτερος", "μικτός", "άγνωστος"],
                        "description": "Ο γενικός συναισθηματικός τόνος του άρθρου"
                    },
                    "missing_perspectives_summary": {
                        "type": "string",
                        "description": "Σύνοψη των οπτικών γωνιών που ενδέχεται να λείπουν από το άρθρο"
                    }
                },
                "required": ["emotionally_charged_terms", "identified_framing_techniques", 
                            "detected_tone", "missing_perspectives_summary"]
            },
            "sources_diversity": {
                "type": "string",
                "enum": ["υψηλή", "μέτρια", "χαμηλή", "μονομερής"],
                "description": "Ποικιλία πηγών που χρησιμοποιήθηκαν στο άρθρο"
            },
            "analysis_summary": {
                "type": "string",
                "description": "Συνοπτική ανάλυση της μεροληψίας και των τεχνικών του άρθρου"
            },
            "supporting_evidence": {
                "type": "array",
                "items": {"type": "string", "format": "url"},
                "description": "URLs που υποστηρίζουν την ανάλυση"
            }
        },
        "required": ["political_spectrum_analysis_greek", "language_and_framing_analysis",
                     "sources_diversity", "analysis_summary", "supporting_evidence"]
    }


def get_timeline_schema() -> dict:
    """
    Get JSON schema for timeline response.
    """
    return {
        "type": "object",
        "properties": {
            "story_title": {"type": "string", "description": "Τίτλος της ιστορίας"},
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Ημερομηνία (YYYY-MM-DD)"},
                        "title": {"type": "string", "description": "Τίτλος του γεγονότος"},
                        "description": {"type": "string", "description": "Περιγραφή του γεγονότος"},
                        "importance": {"type": "string", "enum": ["υψηλή", "μέτρια", "χαμηλή"], "description": "Σημασία του γεγονότος"},
                        "source": {"type": "string", "description": "Πηγή της πληροφορίας"}
                    },
                    "required": ["date", "title", "description", "importance", "source"]
                }
            },
            "context": {"type": "string", "description": "Ιστορικό πλαίσιο"},
            "future_implications": {"type": "string", "description": "Μελλοντικές εξελίξεις"}
        },
        "required": ["events"]
    }


def get_expert_opinions_schema() -> dict:
    """
    Get JSON schema for expert opinions response.
    """
    return {
        "type": "object",
        "properties": {
            "topic_summary": {"type": "string", "description": "Περίληψη του θέματος του άρθρου"},
            "experts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Όνομα του ειδικού"},
                        "credentials": {"type": "string", "description": "Τίτλος/ιδιότητα του ειδικού"},
                        "opinion": {"type": "string", "description": "Γνώμη του ειδικού"},
                        "quote": {"type": "string", "description": "Απευθείας απόσπασμα από τον ειδικό"},
                        "source": {"type": "string", "description": "Τύπος πηγής (x, news, web)"},
                        "source_url": {"type": "string", "format": "url", "description": "URL της πηγής"},
                        "stance": {"type": "string", "enum": ["υποστηρικτική", "αντίθετη", "ουδέτερη"], "description": "Στάση απέναντι στο θέμα"}
                    },
                    "required": ["name", "credentials", "opinion", "source", "source_url"]
                }
            },
            "consensus": {"type": "string", "description": "Συναίνεση μεταξύ των ειδικών"},
            "key_debates": {"type": "string", "description": "Κύρια σημεία διαφωνίας"}
        },
        "required": ["topic_summary", "experts"]
    }


def get_article_topic_extraction_schema() -> dict:
    """
    Get JSON schema for article topic extraction response.
    """
    return {
        "type": "object",
        "properties": {
            "main_topic": {"type": "string", "description": "Κύριο θέμα του άρθρου"},
            "key_entities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Σημαντικές οντότητες (πρόσωπα, οργανισμοί, τοποθεσίες)"
            },
            "x_search_keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Λέξεις-κλειδιά για αναζήτηση στο X"
            }
        },
        "required": ["main_topic", "key_entities", "x_search_keywords"]
    }


def get_x_pulse_analysis_schema() -> dict:
    """
    Get JSON schema for X Pulse analysis response.
    """
    return {
        "type": "object",
        "properties": {
            "overall_discourse_summary": {
                "type": "string",
                "description": "Συνολική περίληψη της συζήτησης στο X σχετικά με το θέμα του άρθρου"
            },
            "discussion_themes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "theme_title": {"type": "string", "description": "Τίτλος θέματος/άποψης"},
                        "theme_summary": {"type": "string", "description": "Περίληψη 1-2 προτάσεων του θέματος/άποψης"},
                        "representative_posts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "post_content": {"type": "string", "description": "Αντιπροσωπευτικό απόσπασμα ή περίληψη ανάρτησης από το X"},
                                    "post_source_description": {"type": "string", "description": "Περιγραφή πηγής"}
                                },
                                "required": ["post_content", "post_source_description"]
                            },
                            "description": "Αντιπροσωπευτικές αναρτήσεις ή περιλήψεις"
                        },
                        "sentiment_around_theme": {"type": "string", "description": "Γενικό συναίσθημα/τόνος"}
                    },
                    "required": ["theme_title", "theme_summary", "representative_posts", "sentiment_around_theme"]
                }
            },
            "data_caveats": {
                "type": "string",
                "description": "Προειδοποίηση σχετικά με τη φύση των δεδομένων από το X",
                "default": "Η ανάλυση αυτή αντικατοπτρίζει ένα στιγμιότυπο των συζητήσεων στο X και ενδέχεται να μην είναι αντιπροσωπευτική της ευρύτερης κοινής γνώμης ή επαληθευμένων γεγονότων. Οι απόψεις που εκφράζονται ανήκουν στους χρήστες του X."
            }
        },
        "required": ["overall_discourse_summary", "discussion_themes", "data_caveats"]
    }


def JSON_ENVELOPE(schema_obj: dict) -> str:
    """
    Create JSON output instructions with schema.
    
    Args:
        schema_obj: The JSON schema object
    
    Returns:
        String with formatted JSON output instructions
    """
    return f"""### ΑΠΟΤΕΛΕΣΜΑΤΑ ###

Please provide the answer exclusively as JSON that exactly matches the following schema.
Remember: ALL text values in the JSON MUST be in Greek language.
```json
{json.dumps(schema_obj, ensure_ascii=False, indent=2)}
```
Do not include markdown fences around the JSON. No additional fields (keys) are allowed in the JSON.
ALL string values MUST be in Greek."""


def build_prompt(task_instruction: str, json_schema_definition: Optional[dict] = None) -> str:
    """
    Build a complete prompt with system prefix, guardrails, and task instructions.
    
    Args:
        task_instruction: The specific task instructions
        json_schema_definition: Optional JSON schema for structured output
    
    Returns:
        Complete prompt string
    """
    prompt_parts = [SYSTEM_PREFIX, TRUST_GUARDRAILS, task_instruction]
    
    if json_schema_definition:
        prompt_parts.append(JSON_ENVELOPE(json_schema_definition))
    
    return "\n\n".join(prompt_parts)


def inject_runtime_search_context(prompt: str, search_params: dict) -> str:
    """
    Inject search parameters context into the prompt.
    
    Args:
        prompt: The base prompt
        search_params: The search parameters being used
    
    Returns:
        Prompt with search context injected
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[inject_runtime_search_context] Called with search_params: {search_params}")
    
    if not search_params:
        logger.info("[inject_runtime_search_context] No search params provided, returning original prompt")
        return prompt
    
    # Filter out None values
    contextual_params = {k: v for k, v in search_params.items() if v is not None}
    if not contextual_params:
        logger.info("[inject_runtime_search_context] All search params were None, returning original prompt")
        return prompt

    # Check for exclusions (transparency notice)
    exclusion_notice = ""
    if "sources" in contextual_params:
        for source in contextual_params["sources"]:
            if isinstance(source, dict) and "excluded_websites" in source and source["excluded_websites"]:
                exclusion_notice = """
TRANSPARENCY NOTICE: Some websites have been excluded from search results.
This may affect the diversity of perspectives. Users can disable exclusions if desired."""
                logger.info(f"[inject_runtime_search_context] Found exclusions: {source['excluded_websites']}")
                break

    pretty_params = json.dumps(contextual_params, ensure_ascii=False, indent=2)
    context_section = f"""
### Active Search Parameters (Live Search) Context ###
```json
{pretty_params}
```
Use these parameters to guide your search strategy.{exclusion_notice}"""
    
    logger.info(f"[inject_runtime_search_context] Added search context: {context_section[:200]}...")
    
    return f"{prompt}{context_section}"


# Task instruction generators

def get_jargon_task_instruction(article_text: str) -> str:
    """Generate task instruction for jargon/term explanations."""
    return f"""Identify ONLY the non-obvious technical terms, organizations, or historical references from the article below.
For each term, provide a clear explanation of 1-2 sentences in Greek.
For each explanation, you MUST provide at least one source (URL) that supports it in the "sources" field.
The final result MUST be a JSON object. Remember: ALL text values must be in Greek.

Article to analyze:
{article_text}"""


def get_alt_view_task_instruction(article_text: str) -> str:
    """Generate task instruction for alternative viewpoints."""
    return f"""Identify the CORE THEMES and CLAIMS in the article, then find alternative perspectives for EACH THEME.

STEP 1 - THEME ANALYSIS:
First identify:
- The main themes/issues raised in the article
- The key claims or positions it supports
- If it's an opinion piece: what arguments it makes

STEP 2 - SEARCH STRATEGY:
For EACH core theme:
1. Search for the THEME, not the specific article
2. Use keywords from the individual issues
3. Examples:
   - If article supports "Privatization of DEI will reduce prices"
     → Search: "DEI privatization electricity prices" AND "DEI public character"
   - If opinion "Electric cars not worth it in Greece"
     → Search: "electric cars Greece cost" AND "electrification benefits"

STEP 3 - TYPES OF ALTERNATIVE VIEWS:
Search for different approaches to THE SAME THEMES:
- Opposing positions on the same issues
- Different interpretation of the same data
- Alternative solutions to the same problem
- Different priorities (e.g., economy vs environment)
- Scientific data that contradicts claims

For each viewpoint, provide:
1. perspective: Title showing WHICH THEME it addresses
2. argument: How does it approach this SPECIFIC THEME differently?
3. source: Name of the source
4. source_url: URL if available
5. key_difference: The ESSENTIAL difference in the specific theme/claim

Also include:
consensus_points: Points of agreement ONLY on undisputed facts (not interpretations)

CRITICAL INSTRUCTIONS:
- If article is opinion/editorial, find OPPOSING OPINIONS on the same themes
- If it proposes one solution, find ALTERNATIVE SOLUTIONS
- If it makes a prediction, find DIFFERENT PREDICTIONS
- Each viewpoint must address a SPECIFIC theme/claim, not the article in general
- Search primarily in Greek language
- ALL text values must be in Greek

Original Article:
{article_text}"""


def get_fact_check_task_instruction(article_text: str) -> str:
    """Generate task instruction for fact-checking."""
    return f"""Identify the main claims in the article below and assess their evidence base.
For each claim:
- Assess the strength of available evidence (evidence_assessment)
- Provide important context that may affect interpretation (context)
- Explain why the topic might be complex or nuanced (complexity_note) - optional field
- Provide at least one reliable source

We avoid absolute "true/false" judgments because most topics have multiple dimensions.
Instead, we focus on the quality of evidence and context.

Also assess the source quality of the article (primary sources, secondary sources, diversity).
IMPORTANT: Search primarily in Greek language.
Remember: ALL text values in JSON must be in Greek.

Article to check:
{article_text}"""


def get_bias_analysis_task_instruction(article_text: str) -> str:
    """Generate task instruction for bias analysis."""
    return f"""Analyze the article below for political bias and framing techniques.

Greek Political Spectrum Analysis:
Analyze the article based on the following two-dimensional Greek political spectrum:

1. Economic Axis:
   - Αριστερά (Κρατικός παρεμβατισμός, κοινωνικοποίηση μέσων παραγωγής, αναδιανομή πλούτου)
   - Κεντροαριστερά (Μικτή οικονομία με ισχυρό κοινωνικό κράτος, ρύθμιση αγορών)
   - Κέντρο (Ισορροπία μεταξύ ελεύθερης αγοράς και κοινωνικής προστασίας, δημοσιονομική υπευθυνότητα)
   - Κεντροδεξιά (Ελεύθερη αγορά με στοχευμένες παρεμβάσεις, μείωση φορολογίας, προσέλκυση επενδύσεων)
   - Δεξιά (Ελαχιστοποίηση κρατικής παρέμβασης, ιδιωτικοποιήσεις, πλήρης απελευθέρωση αγορών)

2. Social Axis:
   - Προοδευτική (Δικαιώματα ΛΟΑΤΚΙ+, διαχωρισμός κράτους-εκκλησίας, πολυπολιτισμικότητα, ατομικές ελευθερίες)
   - Φιλελεύθερη (Έμφαση στα ατομικά δικαιώματα, ανεκτικότητα, μεταρρυθμίσεις)
   - Μετριοπαθής (Ισορροπία μεταξύ παράδοσης και αλλαγής)
   - Συντηρητική (Έμφαση στην παράδοση, εθνική ταυτότητα, οικογενειακές αξίες, επιφυλακτικότητα σε ραγδαίες αλλαγές)

For the article provided, determine its position on BOTH the Economic and Social axes.
Provide a detailed justification for each placement, citing specific examples from the article's text, arguments, or sources.
If the article does not provide enough information for a clear placement on an axis, indicate "Άγνωστο/Δεν είναι σαφές".

Also analyze:
- Emotionally charged language (with explanations of why they are charged)
- Framing techniques (with specific examples)
- Overall tone and sentiment
- Missing perspectives or viewpoints

IMPORTANT: Search primarily in Greek language.
Remember: ALL text values in JSON must be in Greek.

Article to analyze:
{article_text}"""


def get_timeline_task_instruction(article_text: str) -> str:
    """Generate task instruction for timeline construction."""
    return f"""Create a chronological timeline of events related to the topic of the article below.
Include:
- Date of each event
- Description of the event
- Significance/impact of the event
- At least one source (URL) for each event
Focus on the last 30 days unless the topic requires a longer timeframe.
IMPORTANT: Search primarily in Greek language.
Remember: ALL text values in JSON must be in Greek.

Reference article:
{article_text}"""


def get_expert_opinions_task_instruction(article_text: str) -> str:
    """Generate task instruction for expert opinions collection."""
    return f"""Find REAL expert opinions about the topic of the article below.

STRICT REQUIREMENTS:
1. ONLY include experts that you actually find through Live Search
2. DO NOT invent or imagine experts - if you can't find any, return empty array
3. Each expert MUST have been found in your search results
4. The opinion MUST come from actual search results, not speculation
5. If citing X/Twitter, the handle must exist in search results

Search for ACTUAL statements from:
- Greek academics, researchers, analysts who commented on this topic
- Government officials who made statements about this
- Industry experts or organization representatives
- Journalists or commentators with expertise

For each expert found:
- Name must be from search results
- Opinion must be what they actually said (not interpretation)
- Only include if you found them discussing THIS specific topic

IMPORTANT: 
- Search primarily in Greek language
- If no experts found, return empty experts array
- Better to have fewer real experts than many hallucinated ones
- ALL text values in JSON must be in Greek

Reference article:
{article_text}"""


def get_article_topic_extraction_instruction(article_text: str) -> str:
    """Generate task instruction for extracting article topics and keywords for X search."""
    return f"""Analyze the provided Greek news article text.
Identify and extract the following:
1. Main Topic: A concise phrase describing the core subject of the article.
2. Key Entities: A list of important people, organizations, locations, or specific terms mentioned.
3. Search Keywords: A list of 3-5 keywords or short phrases suitable for searching for related discussions on X (Twitter). Prioritize terms that are likely to yield relevant public discourse in Greek.

IMPORTANT: ALL output must be in Greek language.

Article Text:
{article_text}"""


def get_x_pulse_analysis_task_instruction(article_text: str, article_main_topic: str, article_x_keywords: List[str]) -> str:
    """Generate task instruction for X Pulse analysis."""
    keyword_str = ", ".join(article_x_keywords)
    return f"""You are News-Copilot. Your task is to provide an "X Pulse" analysis for the following news article.
The main topic of the article is: '{article_main_topic}'.
Focus your X (Twitter) search and analysis on discussions related to these keywords: {keyword_str}.
The primary language for X posts should be Greek.

IMPORTANT: Search organically based on the topic and keywords. Do NOT limit your search to pre-selected accounts.
Find diverse voices and perspectives - from citizens, experts, officials, journalists, or anyone discussing this topic.

Instructions:
1. Based on your Live Search of X (Twitter) using the topic and keywords, identify relevant public discussions in Greek.
2. From these discussions, identify 3-5 dominant themes or distinct viewpoints from diverse sources.
3. For each theme/viewpoint:
   a. Provide a concise title (2-5 words).
   b. Write a 1-2 sentence summary explaining the theme/viewpoint.
   c. Extract or summarize 1-2 representative X posts (tweets) that clearly illustrate this theme/viewpoint. Attribute them generally (e.g., "ένας χρήστης του X δήλωσε...") unless the source is a verified public figure or organization explicitly making a statement. Focus on the content of the discourse.
   d. Briefly describe the general sentiment or tone surrounding this theme on X (e.g., "Έντονη ανησυχία", "Ισχυρή υποστήριξη", "Μικτές αντιδράσεις", "Ενημερωτική συζήτηση").
4. Provide an overall summary of the X discourse related to the article's topic.

If the topic has international relevance (EU, NATO, climate, etc.), also include relevant English-language discussions.

Original Article for Context (do not summarize the article itself in the output, use it for context only):
{article_text}

Return ALL output in Greek."""


# Self-critique template
def get_task_instruction(task_type: str, article_text: str) -> str:
    """Get task instruction for a specific analysis type"""
    if task_type == "jargon":
        return get_jargon_task_instruction(article_text)
    elif task_type == "viewpoints":
        return get_alt_view_task_instruction(article_text)
    elif task_type == "fact_check":
        return get_fact_check_task_instruction(article_text)
    elif task_type == "bias":
        return get_bias_analysis_task_instruction(article_text)
    elif task_type == "timeline":
        return get_timeline_task_instruction(article_text)
    elif task_type == "expert":
        return get_expert_opinions_task_instruction(article_text)
    else:
        return f"Analyze the following article for {task_type}:\n\n{article_text}"

def build_search_params(article_url: str = "", exclude_domains: list = None) -> dict:
    """Build search parameters for Grok API"""
    return {
        "mode": "on",
        "sources": [{"type": "news"}, {"type": "web"}],
        "max_results": 15,
        "exclude_domains": exclude_domains or []
    }

def format_conversation(messages: list) -> str:
    """Format conversation messages for display"""
    formatted = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted.append(f"{role.upper()}: {content}")
    return "\n\n".join(formatted)

def get_self_critique_prompt(schema_str: str, json_to_check_str: str) -> str:
    """
    Generate a self-critique prompt to validate JSON responses.
    
    Args:
        schema_str: The expected schema as a string
        json_to_check_str: The JSON response to validate as a string
    
    Returns:
        Complete critique prompt
    """
    critique_instruction = f"""Check the JSON object below against these rules:
1. Schema Compliance: Is the JSON 100% compatible with the schema below? Check types, required fields, enums.
   Schema: ```json
   {schema_str}
   ```
2. Source Quality: Does each object requiring sources contain at least one valid URL in the "sources" field? (If the schema requires sources).
3. Reliability Rules: Are there violations of CRITICAL QUALITY RULES (e.g., claims without sources, fabrications)?
4. Language Check: Are ALL text values in Greek as required?

If everything is correct, respond ONLY with the word "OK".
Otherwise, provide a brief list of problems found and suggested fixes, in Greek.

JSON to check:
```json
{json_to_check_str}
```"""
    
    return build_prompt(critique_instruction)