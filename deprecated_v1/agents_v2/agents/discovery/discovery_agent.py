"""Discovery Agent for finding important news topics"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_web_tool


class DiscoveredStory(BaseModel):
    """A discovered news story"""
    headline: str = Field(description="The main headline of the story")
    why_important: str = Field(description="Why this story matters (impact, urgency, relevance)")
    key_facts: List[str] = Field(description="3-5 key facts about the story")
    greek_relevance: float = Field(description="Relevance to Greece (0.0 to 1.0)", ge=0.0, le=1.0)
    initial_sources_found: int = Field(description="Number of sources covering this story")
    category_match: float = Field(description="How well it matches the category focus", ge=0.0, le=1.0)


class DiscoveryOutput(BaseModel):
    """Output from a discovery agent"""
    category: str
    stories: List[DiscoveredStory]
    search_summary: str = Field(description="Brief summary of the search process")


class DiscoveryAgent(BaseNewsAgent):
    """Agent for discovering important news stories in a specific category"""
    
    def __init__(self, category_config: Dict[str, Any], provider: str = "grok"):
        """Initialize a discovery agent for a specific category
        
        Args:
            category_config: Configuration for the news category
            provider: AI provider to use
        """
        self.category_config = category_config
        category_name = category_config["name"]
        
        instructions = f"""You are a news discovery agent specializing in {category_name}.

Your task is to find the TOP 5 most important {category_name} stories for today.

Focus areas for this category:
{chr(10).join('- ' + area for area in category_config['focus_areas'])}

For each story you discover:
1. Search current news about {category_name} using relevant keywords
2. Identify why this matters (consider impact, urgency, relevance)
3. Extract 3-5 key facts (WHO, WHAT, WHEN, WHERE, WHY)
4. Assess relevance to Greece (0.0 to 1.0 scale)
5. Note how many sources are covering it

Key requirements:
- Focus on stories from the last 24-48 hours
- Prioritize stories with broad impact
- Consider both Greek and international sources
- Return structured data, not full articles
- Be concise but informative

Output your findings as a JSON object matching the DiscoveryOutput schema."""
        
        config = AgentConfig(
            name=f"discovery_{category_config['name'].lower().replace(' & ', '_').replace(' ', '_')}",
            description=f"Discovers important {category_name} news",
            category=category_name,
            provider=provider,
            temperature=0.7
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_web_tool]
        )
    
    async def discover(self, 
                      additional_context: Optional[str] = None,
                      time_range: str = "today") -> DiscoveryOutput:
        """Discover top stories in this category
        
        Args:
            additional_context: Optional additional context or focus
            time_range: Time range to search ("today", "week", etc.)
            
        Returns:
            DiscoveryOutput with discovered stories
        """
        # Build the discovery prompt
        prompt = f"Find the top 5 most important {self.category_config['name']} stories"
        
        if time_range != "today":
            prompt += f" from the past {time_range}"
        else:
            prompt += " from today"
        
        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"
        
        # Add category-specific keywords
        keywords = self.category_config.get("keywords", [])
        if keywords:
            prompt += f"\n\nUse these keywords to guide your search: {', '.join(keywords)}"
        
        # Request structured output
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        try:
            data = json.loads(response.content)
            
            # Ensure proper structure
            stories = []
            for story_data in data.get("stories", []):
                story = DiscoveredStory(
                    headline=story_data.get("headline", ""),
                    why_important=story_data.get("why_important", ""),
                    key_facts=story_data.get("key_facts", []),
                    greek_relevance=float(story_data.get("greek_relevance", 0.0)),
                    initial_sources_found=int(story_data.get("initial_sources_found", 1)),
                    category_match=float(story_data.get("category_match", 0.8))
                )
                stories.append(story)
            
            return DiscoveryOutput(
                category=self.category_config["name"],
                stories=stories,
                search_summary=data.get("search_summary", "Discovery completed")
            )
            
        except Exception as e:
            # Fallback for parsing errors
            return DiscoveryOutput(
                category=self.category_config["name"],
                stories=[],
                search_summary=f"Error parsing discovery results: {str(e)}"
            )
    
    def rank_stories(self, stories: List[DiscoveredStory]) -> List[DiscoveredStory]:
        """Rank stories by importance
        
        Args:
            stories: List of discovered stories
            
        Returns:
            Sorted list with most important first
        """
        # Calculate importance score for each story
        def importance_score(story: DiscoveredStory) -> float:
            # Factors: greek relevance, category match, source count
            base_score = story.category_match
            greek_bonus = story.greek_relevance * 0.3
            source_bonus = min(story.initial_sources_found / 20, 0.2)  # Cap at 0.2
            
            # Apply category priority weight
            category_weight = self.category_config.get("priority_weight", 0.5)
            
            return (base_score + greek_bonus + source_bonus) * category_weight
        
        return sorted(stories, key=importance_score, reverse=True)