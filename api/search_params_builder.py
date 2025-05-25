# api/search_params_builder.py
"""
Search parameters builder for Grok Live Search API.
Centralizes the construction of search_parameters objects with sensible defaults.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


def build_search_params(
    mode: str = "auto",
    *,
    sources: Optional[List[Dict[str, Any]]] = None,
    country: str = "GR",  # Default to Greece for web/news
    language: str = "el",  # Default to Greek language (ISO 639-1)
    include_english: bool = False,  # Whether to also search in English for international topics
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    max_results: int = 20,
    safe_search: bool = True,  # Default for web/news
    excluded_websites_map: Optional[Dict[str, List[str]]] = None,
    x_handles_for_x_source: Optional[List[str]] = None,
    rss_links_for_rss_source: Optional[List[str]] = None,
) -> dict:
    """
    Return a fully-formed search_parameters object for Grok API.
    
    Args:
        mode: Search mode - "auto", "on", or "off"
        sources: List of source dicts e.g. [{"type":"web"}, {"type":"x"}]
        country: Country code for web/news sources (default: "GR")
        language: Language code in ISO 639-1 format (default: "el" for Greek)
        include_english: If True, searches in English instead of the specified language
                        (useful for international topics to avoid duplicate sources)
        from_date: Start date in ISO format "YYYY-MM-DD"
        to_date: End date in ISO format "YYYY-MM-DD"
        max_results: Maximum search results to return
        safe_search: Enable safe search for web/news sources
        excluded_websites_map: Dict mapping source types to excluded sites
            e.g. {"web": ["site1.com"], "news": ["site2.com"]}
        x_handles_for_x_source: List of X/Twitter handles for type:"x" sources
        rss_links_for_rss_source: List with single RSS feed URL for type:"rss"
    
    Returns:
        Dict with properly formatted search_parameters for Grok API
    """
    # Default sources if none provided
    default_sources = [{"type": "web"}, {"type": "news"}]
    
    # Handle multilingual search without duplicating sources
    if include_english and language == "el":
        # For international topics, we'll use English as the primary language
        # This gives us broader coverage without duplicating sources
        processed_sources = sources if sources is not None else default_sources
        # Mark that we should use English for web/news sources
        effective_language = "en"
    else:
        processed_sources = sources if sources is not None else default_sources
        effective_language = language

    def enrich_source(source_item: dict) -> dict:
        """Enrich a source dict with additional parameters based on its type."""
        enriched = dict(source_item)  # Work on a copy
        source_type = enriched.get("type")

        # Enrich web/news sources
        if source_type in ("web", "news"):
            # Use the effective language determined above
            enriched["language"] = effective_language
                
            if country:
                enriched["country"] = country
            enriched["safe_search"] = safe_search
            if excluded_websites_map and excluded_websites_map.get(source_type):
                # Max 5 excluded websites per source type
                enriched["excluded_websites"] = excluded_websites_map[source_type][:5]
        
        # Enrich X source
        elif source_type == "x":
            # X searches in the language of the content, but we can hint preference
            if x_handles_for_x_source:
                enriched["x_handles"] = x_handles_for_x_source
        
        # Enrich RSS source
        elif source_type == "rss":
            if rss_links_for_rss_source:
                # Grok API currently expects a list with one link
                enriched["links"] = rss_links_for_rss_source[:1]
        
        return enriched

    # Build final parameters
    final_params = {
        "mode": mode,
        "return_citations": True,  # Always true for our use case
        "max_search_results": max_results,
        "sources": [enrich_source(s) for s in processed_sources],
    }

    # Add date range if specified
    if from_date:
        final_params["from_date"] = from_date  # ISO8601 format "YYYY-MM-DD"
    if to_date:
        final_params["to_date"] = to_date      # ISO8601 format "YYYY-MM-DD"

    return final_params


def get_date_range_for_timeline(days_back: int = 30) -> tuple[str, str]:
    """
    Get date range for timeline analysis.
    
    Args:
        days_back: Number of days to look back (default: 30)
    
    Returns:
        Tuple of (from_date, to_date) in ISO format
    """
    today = datetime.now().date()
    from_date = today - timedelta(days=days_back)
    return from_date.isoformat(), today.isoformat()


def get_date_range_for_breaking_news() -> tuple[str, str]:
    """
    Get date range for breaking news (last 24 hours).
    
    Returns:
        Tuple of (from_date, to_date) in ISO format
    """
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    return yesterday.isoformat(), today.isoformat()




def get_excluded_websites() -> Dict[str, List[str]]:
    """
    Get list of sites to exclude from search results.
    
    TRANSPARENCY NOTICE: 
    - Excluding sites introduces bias into the analysis
    - Users can disable exclusions or use their own list
    - The exclusion list is publicly visible in config/low_quality_sites.yml
    
    Returns:
        Dict mapping source types to lists of domains to exclude
    """
    try:
        import yaml
        import os
        from .config import EXCLUDED_SITES_CONFIG_PATH
        
        # Try to load from config file
        config_path = EXCLUDED_SITES_CONFIG_PATH
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                excluded_sites = yaml.safe_load(f)
                
            # Ensure proper structure
            if isinstance(excluded_sites, dict):
                web_exclusions = excluded_sites.get("web", []) or []
                news_exclusions = excluded_sites.get("news", []) or []
                
                # Log if exclusions are active (for transparency)
                if web_exclusions or news_exclusions:
                    print(f"[TRANSPARENCY] Site exclusions active: {len(web_exclusions)} web, {len(news_exclusions)} news sites")
                
                return {
                    "web": web_exclusions,
                    "news": news_exclusions
                }
    except Exception as e:
        print(f"[TRANSPARENCY] Could not load excluded sites config: {e}")
    
    # Default: no exclusions (transparent by default)
    return {
        "web": [],
        "news": []
    }


# Helper function to create exclusion map with article domain
def create_exclusion_map_with_article_domain(article_domain: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Create exclusion map including the current article domain if provided.
    
    Args:
        article_domain: Domain to exclude (e.g., "kathimerini.gr")
        
    Returns:
        Dict mapping source types to lists of domains to exclude
    """
    base_exclusions = get_excluded_websites()
    
    if not article_domain:
        return base_exclusions
    
    # Make a copy to avoid modifying the base exclusions
    exclusion_map = {
        "web": list(base_exclusions.get("web", [])),
        "news": list(base_exclusions.get("news", []))
    }
    
    # Add article domain if not already present
    if article_domain not in exclusion_map["web"]:
        exclusion_map["web"].append(article_domain)
    if article_domain not in exclusion_map["news"]:
        exclusion_map["news"].append(article_domain)
    
    return exclusion_map


# Preset configurations for different analysis types

def get_search_params_for_jargon(mode: str = "auto", article_domain: Optional[str] = None) -> dict:
    """Get optimized search params for jargon/term explanations."""
    return build_search_params(
        mode=mode,
        max_results=10,  # Fewer results needed for term definitions
        sources=[{"type": "web"}, {"type": "news"}],
        excluded_websites_map=create_exclusion_map_with_article_domain(article_domain)
    )


def get_search_params_for_timeline(mode: str = "on", article_domain: Optional[str] = None) -> dict:
    """Get search params for timeline analysis with date range."""
    from_date, to_date = get_date_range_for_timeline()
    return build_search_params(
        mode=mode,
        from_date=from_date,
        to_date=to_date,
        max_results=15,
        sources=[{"type": "news"}, {"type": "web"}],
        excluded_websites_map=create_exclusion_map_with_article_domain(article_domain)
    )


def get_search_params_for_expert_opinions(mode: str = "on", article_domain: Optional[str] = None) -> dict:
    """Get search params for expert opinions including X/Twitter."""
    return build_search_params(
        mode=mode,
        sources=[
            {"type": "x"},
            {"type": "news"},
            {"type": "web"}
        ],
        # X handles will be discovered dynamically by Grok based on context
        x_handles_for_x_source=None,
        max_results=20,
        excluded_websites_map=create_exclusion_map_with_article_domain(article_domain)
    )


def detect_international_keywords(keywords: List[str]) -> bool:
    """
    Detect if the article topic has international relevance.
    
    Args:
        keywords: List of keywords extracted from the article
    
    Returns:
        True if international sources should be included
    """
    # International organization keywords
    international_orgs = {
        'EU', 'ΕΕ', 'NATO', 'ΝΑΤΟ', 'UN', 'ΟΗΕ', 'IMF', 'ΔΝΤ', 'ECB', 'ΕΚΤ',
        'European', 'Ευρωπαϊκ', 'Brussels', 'Βρυξέλλες', 'Washington', 'Ουάσινγκτον',
        'G7', 'G20', 'OECD', 'ΟΟΣΑ', 'World Bank', 'Παγκόσμια Τράπεζα',
        'European Commission', 'Ευρωπαϊκή Επιτροπή', 'European Parliament', 'Ευρωκοινοβούλιο'
    }
    
    # International topic keywords
    international_topics = {
        'pandemic', 'πανδημία', 'climate', 'κλίμα', 'refugee', 'πρόσφυγ',
        'migration', 'μετανάστευ', 'sanctions', 'κυρώσεις', 'war', 'πόλεμος',
        'global', 'παγκόσμι', 'international', 'διεθν', 'energy', 'ενέργεια',
        'inflation', 'πληθωρισμ', 'recession', 'ύφεση', 'Ukraine', 'Ουκραν',
        'Russia', 'Ρωσ', 'Turkey', 'Τουρκ', 'Cyprus', 'Κύπρ', 'Israel', 'Ισραήλ',
        'Middle East', 'Μέση Ανατολή', 'Biden', 'Trump', 'Putin', 'Erdogan',
        'COVID', 'κορονοϊός', 'vaccine', 'εμβόλι', 'trade', 'εμπόρ'
    }
    
    # Check if any keyword matches international patterns
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Check exact matches for organizations
        if keyword in international_orgs:
            return True
            
        # Check partial matches for topics
        for intl_term in international_topics:
            if intl_term.lower() in keyword_lower:
                return True
    
    return False


def get_search_params_for_x_pulse(mode: str = "on", keywords: List[str] = None, 
                                  article_domain: Optional[str] = None,
                                  topic_context: Optional[Dict[str, Any]] = None) -> dict:
    """
    Get search params optimized for X Pulse analysis.
    
    TRANSPARENCY: No curated account lists - Grok finds relevant discussions organically
    based on article content and keywords to avoid bias.
    
    For international topics (Ukraine, Russia, EU, etc.), we automatically search
    in English to get broader coverage without duplicating sources.
    
    Args:
        mode: Search mode (on/auto)
        keywords: Keywords extracted from article
        article_domain: Domain to exclude from search
        topic_context: Additional context about the article topic
    
    Returns:
        Configured search parameters
    """
    # Check if we should include international sources
    include_international = False
    if keywords:
        include_international = detect_international_keywords(keywords)
        if include_international:
            print("[X-Pulse] Detected international topic - including English sources")
    
    # X search will focus on finding relevant discussions organically
    sources = [{"type": "x"}]
    
    # If keywords are provided, also search web/news for broader context
    if keywords:
        sources.extend([{"type": "news"}, {"type": "web"}])
    
    # Build parameters without curated handles - let Grok find relevant voices
    return build_search_params(
        mode=mode,
        sources=sources,
        x_handles_for_x_source=None,  # No curated list - organic discovery
        max_results=30,  # More results for discourse analysis
        include_english=include_international,  # Include English based on topic detection
        excluded_websites_map=create_exclusion_map_with_article_domain(article_domain)
    )


def get_search_params_for_fact_check(mode: str = "on", article_domain: Optional[str] = None, 
                                    keywords: Optional[List[str]] = None) -> dict:
    """Get search params for fact-checking with quality filters."""
    # Check if international sources would be helpful
    include_international = False
    if keywords:
        include_international = detect_international_keywords(keywords)
        
    return build_search_params(
        mode=mode,
        safe_search=True,
        excluded_websites_map=create_exclusion_map_with_article_domain(article_domain),
        max_results=25,  # More sources for verification
        sources=[{"type": "web"}, {"type": "news"}],
        include_english=include_international
    )


def get_search_params_for_bias_analysis(mode: str = "on", article_domain: Optional[str] = None) -> dict:
    """Get search params for bias analysis (less restrictive)."""
    return build_search_params(
        mode=mode,
        safe_search=False,  # Allow all viewpoints
        max_results=20,
        sources=[{"type": "news"}, {"type": "web"}, {"type": "x"}],
        excluded_websites_map=create_exclusion_map_with_article_domain(article_domain)
    )