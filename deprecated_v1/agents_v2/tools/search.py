"""Search tools for agents"""

from typing import Optional, List, Dict, Any
from .base import create_tool_definition


search_web_tool = create_tool_definition(
    name="search_web",
    description="Search the web for general information on any topic",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query"
        },
        "region": {
            "type": "string",
            "description": "Region code (e.g., 'gr' for Greece, 'us' for USA)",
            "default": "us"
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return",
            "default": 5
        }
    },
    required_params=["query"]
)


search_greek_news_tool = create_tool_definition(
    name="search_greek_news",
    description="Search specifically Greek news sources for information",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query in Greek or English"
        },
        "source_type": {
            "type": "string",
            "description": "Type of sources: 'mainstream', 'alternative', 'all'",
            "default": "all"
        },
        "time_range": {
            "type": "string",
            "description": "Time range: 'today', 'week', 'month', 'year'",
            "default": "week"
        }
    },
    required_params=["query"]
)


search_international_news_tool = create_tool_definition(
    name="search_international_news",
    description="Search international news sources for global perspectives",
    parameters={
        "query": {
            "type": "string",
            "description": "The search query"
        },
        "regions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of regions to search (e.g., ['us', 'uk', 'eu'])",
            "default": ["us", "uk", "eu"]
        },
        "exclude_sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of domains to exclude"
        }
    },
    required_params=["query"]
)


# Tool implementations (these would call actual search APIs)
async def search_web(
    query: str,
    region: str = "us",
    num_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search the web for information
    
    In a real implementation, this would call a search API
    """
    # Placeholder implementation
    return [
        {
            "title": f"Result for: {query}",
            "url": f"https://example.com/{i}",
            "snippet": f"This is result {i} for query: {query}",
            "source": "example.com"
        }
        for i in range(num_results)
    ]


async def search_greek_news(
    query: str,
    source_type: str = "all",
    time_range: str = "week"
) -> List[Dict[str, Any]]:
    """
    Search Greek news sources
    
    In a real implementation, this would search Greek news sites
    """
    # Greek news domains by category
    greek_sources = {
        "mainstream": ["kathimerini.gr", "tanea.gr", "protothema.gr"],
        "alternative": ["efsyn.gr", "documento.gr", "thetoc.gr"],
        "all": ["kathimerini.gr", "tanea.gr", "protothema.gr", "efsyn.gr", "documento.gr"]
    }
    
    sources = greek_sources.get(source_type, greek_sources["all"])
    
    # Placeholder implementation
    return [
        {
            "title": f"Greek news: {query}",
            "url": f"https://{source}/article/{i}",
            "snippet": f"Greek perspective on {query}",
            "source": source,
            "language": "el"
        }
        for i, source in enumerate(sources[:3])
    ]


async def search_international_news(
    query: str,
    regions: List[str] = None,
    exclude_sources: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Search international news sources
    
    In a real implementation, this would search global news
    """
    if regions is None:
        regions = ["us", "uk", "eu"]
    
    if exclude_sources is None:
        exclude_sources = []
    
    # Region to source mapping
    region_sources = {
        "us": ["cnn.com", "nytimes.com", "wsj.com"],
        "uk": ["bbc.com", "theguardian.com", "ft.com"],
        "eu": ["dw.com", "euronews.com", "france24.com"]
    }
    
    results = []
    for region in regions:
        sources = region_sources.get(region, [])
        for source in sources:
            if source not in exclude_sources:
                results.append({
                    "title": f"{region.upper()} view: {query}",
                    "url": f"https://{source}/article",
                    "snippet": f"International perspective from {region}",
                    "source": source,
                    "region": region
                })
    
    return results[:10]  # Limit to 10 results