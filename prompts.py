# prompts.py

# --- Prompts for Grok --- 

GROK_CONTEXT_JARGON_PROMPT_SCHEMA = """Read the news article below.
Identify ONLY the NON-obvious technical terms, organizations, or historical references that an average reader might not be familiar with.
For each term, provide an explanation of 1-2 sentences IN GREEK.

Return the results as a JSON object containing a "terms" array with objects that have:
- "term": the term as it appears in the article
- "explanation": the explanation in Greek

IMPORTANT: Use Live Search with GREEK search terms when possible. ALL explanations must be written in GREEK. Only use English search terms when the specific term requires it (e.g., English technical terms, international organizations).
"""

GROK_ALTERNATIVE_VIEWPOINTS_PROMPT = """Using Live Search, find other credible news articles that cover the SAME story as the original article provided below.
Summarize in 4-8 bullet points how their coverage differs or adds to the original story.
Mention new facts, different perspectives, missing details, or conflicting statements.
CRITICAL LANGUAGE REQUIREMENTS:
- Conduct searches primarily in GREEK to find Greek news sources
- The response MUST be exclusively in GREEK
- For each bullet point, please cite the source at the end of the point

X/TWITTER LINKS: If you reference X posts or X users, include @usernames in the text and full links where available.

IMPORTANT: The response must be objective and approach the story without bias.
"""

# --- Progressive Analysis Prompts for Deep Intelligence ---

GROK_FACT_CHECK_PROMPT = """Analyze the news article below for fact-checking.

Using Live Search, verify the main claims, statistics, dates, and events mentioned in the article.

Return JSON with the structure:
{
  "overall_credibility": "υψηλή/μέτρια/χαμηλή",
  "claims": [
    {
      "statement": "The specific claim from the article",
      "verified": true/false,
      "explanation": "Verification explanation in Greek",
      "sources": ["source1", "source2"]
    }
  ],
  "red_flags": ["Warning 1", "Warning 2"],
  "missing_context": "Information that is missing or needs clarification"
}

Focus on the 3-5 most important claims. 

CRITICAL: Conduct searches in GREEK when possible. ALL responses must be in GREEK.
"""

GROK_BIAS_ANALYSIS_PROMPT = """Analyze the news article below for political bias, emotional tone, and presentation.

Using Live Search, compare the presentation with other sources covering the same topic.

Return JSON with the structure:
{
  "political_lean": "αριστερά/κεντροαριστερά/κέντρο/κεντροδεξιά/δεξιά/ουδέτερο",
  "confidence": "υψηλή/μέτρια/χαμηλή",
  "emotional_tone": "θετικός/ουδέτερος/αρνητικός/ανάμεικτος",
  "language_analysis": {
    "loaded_words": ["word1", "word2"],
    "framing": "How the story is presented",
    "missing_perspectives": "Missing viewpoints"
  },
  "comparison": "Comparison with other sources",
  "recommendations": "Recommendations for balanced understanding"
}

CRITICAL: Conduct searches in GREEK when possible for Greek sources. ALL responses must be in GREEK with objectivity.
"""

GROK_TIMELINE_PROMPT = """Create a timeline for the story presented in the article below.

Using Live Search, find previous events and developments that led to the current situation.

Return JSON with the structure:
{
  "story_title": "Brief title of the story",
  "events": [
    {
      "date": "YYYY-MM-DD or date description",
      "title": "Brief event title (include @usernames if referencing X users)",
      "description": "Event description (include @usernames if referencing X users)",
      "importance": "υψηλή/μέτρια/χαμηλή",
      "source": "Information source (include @usernames if referencing X users)"
    }
  ],
  "context": "Historical context and significance (include @usernames if referencing X users)",
  "future_implications": "Potential future developments (include @usernames if referencing X users)"
}

X/TWITTER LINKS: If you reference X posts or X users, include @usernames in the text.

Sort events chronologically (oldest to newest). 

CRITICAL: Conduct searches primarily in GREEK to find Greek news sources. ALL responses must be in GREEK.
"""

GROK_EXPERT_OPINIONS_PROMPT = """Find expert opinions and specialist viewpoints on the topic of the article below.

Using Live Search (particularly X/Twitter and news sources), identify:
- Academics and researchers
- Analysts and journalists
- Former officials or field experts
- Organization representatives

CRITICAL: For each expert you reference:
1. Ensure that the "source_url" actually contains the "quote" or "opinion" you reference
2. If you cannot find the specific URL containing the quote, leave "source_url" empty ("")
3. Only include actual quotes, not paraphrases or interpretations
4. FOR X/TWITTER POSTS: When referencing X posts, include the FULL direct link in the format https://x.com/username/status/1234567890
5. When referring to X users, include the @username in the text

Return JSON with the structure:
{
  "topic_summary": "Topic summary (include @usernames if referencing X users)",
  "experts": [
    {
      "name": "Expert name",
      "credentials": "Title/position/organization",
      "opinion": "Expert's opinion (include @usernames if referencing X users)",
      "quote": "Direct quote only if exact text was found",
      "source": "x/news/web",
      "source_url": "ONLY if this URL contains the specific quote/opinion, otherwise empty",
      "stance": "υποστηρικτική/αντίθετη/ουδέτερη"
    }
  ],
  "consensus": "Consensus or disagreement among experts (include @usernames if referencing X users)",
  "key_debates": "Main points of disagreement (include @usernames if referencing X users)"
}

SOURCE QUALITY: Prioritize reliable sources and do not provide URLs that are not directly related to the content.

CRITICAL: Conduct searches primarily in GREEK to find Greek news sources and experts. ALL responses must be in GREEK.
"""