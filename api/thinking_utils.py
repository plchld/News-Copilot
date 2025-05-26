# api/thinking_utils.py
"""
Utilities for leveraging Grok's thinking models to make intelligent decisions.
Uses grok-3-mini for reasoning-heavy tasks that don't require extensive domain knowledge.
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta


def get_article_analysis_prompt(article_text: str) -> str:
    """
    Generate a prompt for analyzing an article to determine optimal search parameters.
    """
    return f"""Analyze the following Greek news article and determine the optimal search parameters.

Article:
{article_text[:2000]}  # Limit to first 2000 chars for efficiency

Please determine:
1. Is this primarily a LOCAL Greek story or an INTERNATIONAL story?
2. What is the main topic/event? (in 1-2 words)
3. When did the main event occur? (approximate date or "ongoing")
4. Should we search in English as well as Greek? (yes/no)
5. What time range would be most relevant for searches? (e.g., "last 24 hours", "last week", "last month")
6. What are the main themes? Choose from: government, economy, politics, culture, sports, technology, health, education
7. Are any specific people mentioned by name? (list up to 5)

Provide your answer as a JSON object with these exact fields:
{{
    "story_scope": "local" or "international",
    "main_topic": "brief topic description",
    "event_date": "YYYY-MM-DD" or "ongoing",
    "search_english": true or false,
    "time_range_days": number (1-365),
    "themes": ["theme1", "theme2"],
    "people_mentioned": ["name1", "name2"] or []
}}"""


def get_search_strategy_prompt(article_text: str, analysis_type: str) -> str:
    """
    Generate a prompt to determine the best search strategy for a specific analysis type.
    """
    analysis_descriptions = {
        "jargon": "technical term explanations",
        "viewpoints": "alternative news coverage",
        "fact_check": "claim verification",
        "bias": "political bias analysis",
        "timeline": "chronological event reconstruction",
        "expert": "expert opinions and commentary"
    }
    
    description = analysis_descriptions.get(analysis_type, analysis_type)
    
    return f"""Given this Greek news article, determine the optimal search strategy for {description}.

Article excerpt:
{article_text[:1500]}

Analysis type: {analysis_type}

Determine:
1. Which sources are most valuable? (web, news, x, rss)
2. How many search results do we need? (5-50)
3. Should we enable safe_search? (true/false)
4. Are there specific domains we should exclude as unreliable?
5. For timeline analysis: what date range is relevant?
6. Should we search for X posts? (If yes, Grok will find relevant handles automatically)

Answer as JSON:
{{
    "sources": ["web", "news", "x"],  // List sources in priority order
    "max_results": 20,
    "safe_search": true,
    "excluded_domains": ["example.com"],
    "date_range": {{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}} or null,
    "include_x_search": true or false
}}"""


def get_quality_check_prompt(response_json: str, expected_schema: dict, analysis_type: str) -> str:
    """
    Generate a prompt for quality-checking a response using reasoning.
    """
    return f"""Carefully examine this {analysis_type} analysis response for quality and completeness.

Expected schema:
{json.dumps(expected_schema, ensure_ascii=False, indent=2)}

Actual response:
{response_json}

Check for:
1. Schema compliance - does it match the expected structure?
2. Language consistency - are ALL text values in Greek?
3. Source quality - does each claim have valid URL sources?
4. Completeness - are all required fields present and meaningful?
5. Accuracy concerns - any obvious errors or contradictions?

Provide your assessment as:
{{
    "is_valid": true/false,
    "issues": ["issue1", "issue2"] or [],
    "severity": "ok" or "minor" or "major",
    "suggestions": ["suggestion1"] or []
}}"""


def get_complexity_assessment_prompt(article_text: str) -> str:
    """
    Assess article complexity to determine appropriate reasoning effort.
    """
    return f"""Quickly assess the complexity of this Greek news article:

{article_text[:1000]}

Consider:
- Number of entities/organizations involved
- Technical complexity
- Political sensitivity
- Time span of events
- Conflicting information

Rate complexity as:
{{
    "complexity": "low" or "medium" or "high",
    "reasoning": "brief explanation in Greek"
}}"""


class ThinkingAnalyzer:
    """
    Wrapper for using Grok's thinking models to make intelligent decisions.
    """
    
    def __init__(self, grok_client):
        self.grok_client = grok_client
        self.thinking_model = "grok-3-mini-fast"  # Fast thinking model
        
    async def analyze_article_context(self, article_text: str) -> Dict[str, Any]:
        """
        Analyze article to determine optimal search parameters.
        
        Returns:
            Dict with story_scope, main_topic, search_english, time_range_days, x_handles
        """
        prompt = get_article_analysis_prompt(article_text)
        
        response = await self.grok_client.async_client.chat.completions.create(
            model=self.thinking_model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": "low"},  # Quick analysis
            temperature=0.3,  # Lower temperature for consistent analysis
            response_format={"type": "json_object"}
        )
        
        # Extract reasoning content for logging
        reasoning = response.choices[0].message.reasoning_content
        result = json.loads(response.choices[0].message.content)
        
        # Log reasoning for debugging
        print(f"Article analysis reasoning: {reasoning}")
        
        return result
    
    async def determine_search_strategy(self, article_text: str, analysis_type: str) -> Dict[str, Any]:
        """
        Determine optimal search strategy for a specific analysis type.
        
        Returns:
            Dict with sources, max_results, safe_search, excluded_domains, date_range
        """
        prompt = get_search_strategy_prompt(article_text, analysis_type)
        
        response = await self.grok_client.async_client.chat.completions.create(
            model=self.thinking_model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": "low"},
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def validate_response_quality(
        self, 
        response_json: str, 
        expected_schema: dict, 
        analysis_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate response quality using reasoning model.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        prompt = get_quality_check_prompt(response_json, expected_schema, analysis_type)
        
        response = await self.grok_client.async_client.chat.completions.create(
            model=self.thinking_model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": "high"},  # Thorough validation
            temperature=0.1,  # Very low temperature for consistency
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["is_valid"], result.get("issues", [])
    
    async def assess_complexity(self, article_text: str) -> str:
        """
        Assess article complexity to determine reasoning effort needed.
        
        Returns:
            "low", "medium", or "high"
        """
        prompt = get_complexity_assessment_prompt(article_text)
        
        response = await self.grok_client.async_client.chat.completions.create(
            model=self.thinking_model,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": "low"},
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["complexity"]


def build_adaptive_search_params(
    article_analysis: Dict[str, Any],
    search_strategy: Dict[str, Any],
    base_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build search parameters based on thinking model analysis.
    
    Args:
        article_analysis: Results from analyze_article_context
        search_strategy: Results from determine_search_strategy  
        base_params: Optional base parameters to override
        
    Returns:
        Complete search parameters dict
    """
    from .search_params_builder import build_search_params
    
    # Determine language settings
    language = "el"  # Always search in Greek
    include_english = article_analysis.get("search_english", False)
    
    # Build source list
    sources = []
    for source_type in search_strategy.get("sources", ["web", "news"]):
        sources.append({"type": source_type})
    
    # Calculate date range
    date_range = search_strategy.get("date_range")
    from_date = None
    to_date = None
    
    if date_range:
        from_date = date_range.get("from")
        to_date = date_range.get("to")
    elif article_analysis.get("time_range_days"):
        # Calculate based on days
        days = article_analysis["time_range_days"]
        to_date = datetime.now().date().isoformat()
        from_date = (datetime.now().date() - timedelta(days=days)).isoformat()
    
    # Build excluded websites map
    excluded_domains = search_strategy.get("excluded_domains", [])
    excluded_map = {}
    if excluded_domains:
        excluded_map["web"] = excluded_domains
        excluded_map["news"] = excluded_domains
    
    # X handles are no longer predetermined - Grok will find them dynamically
    
    # Merge with base params if provided
    params = base_params or {}
    
    return build_search_params(
        mode=params.get("mode", "on"),  # Default to "on" for thinking-guided searches
        sources=sources,
        country="GR",
        language=language,
        include_english=include_english,
        from_date=from_date,
        to_date=to_date,
        max_results=search_strategy.get("max_results", 20),
        safe_search=search_strategy.get("safe_search", True),
        excluded_websites_map=excluded_map,
        x_handles_for_x_source=None  # Let Grok discover relevant handles
    )