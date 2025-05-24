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
        include_english: Also search in English for international topics
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
    
    # If include_english is True and we're searching Greek, duplicate sources for English
    if include_english and language == "el":
        # Create both Greek and English versions of web/news sources
        processed_sources = []
        base_sources = sources if sources is not None else default_sources
        
        for source in base_sources:
            if source.get("type") in ("web", "news"):
                # Greek version
                processed_sources.append(source)
                # English version
                english_source = dict(source)
                english_source["_english_variant"] = True  # Internal marker
                processed_sources.append(english_source)
            else:
                # X and RSS sources don't need duplication
                processed_sources.append(source)
    else:
        processed_sources = sources if sources is not None else default_sources

    def enrich_source(source_item: dict) -> dict:
        """Enrich a source dict with additional parameters based on its type."""
        enriched = dict(source_item)  # Work on a copy
        source_type = enriched.get("type")
        is_english_variant = enriched.pop("_english_variant", False)

        # Enrich web/news sources
        if source_type in ("web", "news"):
            # Set language - English variant or specified language
            if is_english_variant:
                enriched["language"] = "en"
            else:
                enriched["language"] = language
                
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
    Get list of low-credibility sites to exclude.
    
    Returns:
        Dict mapping source types to lists of domains to exclude
    """
    # TODO: This should be loaded from a configuration file
    # For now, return empty dict (no exclusions)
    return {
        "web": [],
        "news": []
    }


# Preset configurations for different analysis types

def get_search_params_for_jargon(mode: str = "auto") -> dict:
    """Get optimized search params for jargon/term explanations."""
    return build_search_params(
        mode=mode,
        max_results=10,  # Fewer results needed for term definitions
        sources=[{"type": "web"}, {"type": "news"}]
    )


def get_search_params_for_timeline(mode: str = "on") -> dict:
    """Get search params for timeline analysis with date range."""
    from_date, to_date = get_date_range_for_timeline()
    return build_search_params(
        mode=mode,
        from_date=from_date,
        to_date=to_date,
        max_results=15,
        sources=[{"type": "news"}, {"type": "web"}]
    )


def get_search_params_for_expert_opinions(mode: str = "on") -> dict:
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
        max_results=20
    )


def get_search_params_for_fact_check(mode: str = "on") -> dict:
    """Get search params for fact-checking with quality filters."""
    return build_search_params(
        mode=mode,
        safe_search=True,
        excluded_websites_map=get_excluded_websites(),
        max_results=25,  # More sources for verification
        sources=[{"type": "web"}, {"type": "news"}]
    )


def get_search_params_for_bias_analysis(mode: str = "on") -> dict:
    """Get search params for bias analysis (less restrictive)."""
    return build_search_params(
        mode=mode,
        safe_search=False,  # Allow all viewpoints
        max_results=20,
        sources=[{"type": "news"}, {"type": "web"}, {"type": "x"}]
    )