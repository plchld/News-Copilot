"""Tool definitions for agents"""

from .search import search_web, search_greek_news, search_international_news
from .base import create_tool_definition

__all__ = [
    "search_web",
    "search_greek_news", 
    "search_international_news",
    "create_tool_definition"
]