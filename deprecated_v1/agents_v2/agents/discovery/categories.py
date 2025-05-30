"""Discovery categories configuration"""

from typing import Dict, Any


DISCOVERY_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "greek_politics": {
        "name": "Greek Politics",
        "description": "Greek political news and government affairs",
        "keywords": ["ελληνική πολιτική", "κυβέρνηση", "βουλή", "Greek politics", "government"],
        "focus_areas": [
            "Government decisions and policies",
            "Parliamentary activities",
            "Political party news",
            "Elections and polls",
            "EU-Greece relations"
        ],
        "priority_weight": 0.9  # High priority for Greek audience
    },
    
    "global_politics": {
        "name": "Global Politics",
        "description": "International political developments with Greek relevance",
        "keywords": ["world politics", "international relations", "geopolitics"],
        "focus_areas": [
            "Major world events",
            "EU politics affecting Greece",
            "Mediterranean region politics",
            "US/China/Russia developments",
            "International conflicts"
        ],
        "priority_weight": 0.7
    },
    
    "economy_business": {
        "name": "Economy & Business",
        "description": "Economic news, markets, and business developments",
        "keywords": ["economy", "οικονομία", "business", "markets", "finance"],
        "focus_areas": [
            "Greek economy updates",
            "EU economic policies",
            "Global market trends",
            "Energy and inflation",
            "Tech and startups"
        ],
        "priority_weight": 0.8
    },
    
    "science_tech": {
        "name": "Science & Technology",
        "description": "Scientific breakthroughs and technology news",
        "keywords": ["science", "technology", "AI", "research", "innovation"],
        "focus_areas": [
            "AI and machine learning",
            "Climate science",
            "Medical breakthroughs",
            "Space exploration",
            "Tech industry news"
        ],
        "priority_weight": 0.6
    },
    
    "society_culture": {
        "name": "Society & Culture",
        "description": "Social issues, cultural events, and human interest",
        "keywords": ["society", "κοινωνία", "culture", "πολιτισμός"],
        "focus_areas": [
            "Social movements",
            "Cultural events",
            "Education news",
            "Health and wellness",
            "Human interest stories"
        ],
        "priority_weight": 0.5
    }
}