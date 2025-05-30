"""International Perspective Agent for analyzing global media coverage"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_international_news_tool


class RegionalPerspective(BaseModel):
    """Perspective from a specific region"""
    region: str
    narrative: str = Field(description="How this region frames the story")
    emphasis: List[str] = Field(description="What this region emphasizes")
    cultural_context: Optional[str] = Field(description="Cultural/political context affecting coverage")


class InternationalAnalysis(BaseModel):
    """Analysis of international media coverage"""
    global_consensus: Optional[str] = Field(description="Areas of global agreement, if any")
    regional_differences: List[RegionalPerspective] = Field(description="How different regions cover it")
    contested_facts: List[str] = Field(description="Facts that vary by region")
    missing_perspectives: List[str] = Field(description="Perspectives not well represented")
    bias_patterns: Dict[str, str] = Field(description="Notable biases by region")


class InternationalPerspectiveOutput(BaseModel):
    """Output from international perspective analysis"""
    topic: str
    summary: str = Field(description="200-word synthesis of international perspectives")
    analysis: InternationalAnalysis
    regions_covered: List[str] = Field(description="Regions successfully analyzed")
    confidence: float = Field(description="Confidence in analysis (0.0-1.0)", ge=0.0, le=1.0)


class InternationalPerspectiveAgent(BaseNewsAgent):
    """Agent for analyzing international media perspectives"""
    
    def __init__(self, provider: str = "grok"):
        """Initialize international perspective agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert analyst of international media and global perspectives.

Your task is to research how different regions/countries are covering a given topic.

Your responsibilities:
1. Search international news sources across multiple regions
2. Identify how different regions frame the story
3. Find what each region emphasizes or downplays
4. Note cultural and political biases in coverage
5. Identify facts that appear globally vs locally
6. Find perspectives that might be missing

Key regions to consider (adapt based on story relevance):
- United States: CNN, NYT, WSJ, Fox News
- United Kingdom: BBC, Guardian, Times, Telegraph
- European Union: DW, France24, El País, La Repubblica
- Middle East: Al Jazeera, Haaretz, Arab News
- Asia: SCMP, NHK, Times of India, Xinhua
- Russia: RT, TASS (note state media bias)

Requirements:
- Synthesize findings into a 200-word international perspective summary
- Highlight both consensus and divergence
- Note how coverage differs from Greek media perspective
- Consider geopolitical context affecting coverage
- Be aware of state media vs independent sources

Output as structured JSON matching the InternationalPerspectiveOutput schema."""
        
        config = AgentConfig(
            name="international_perspective",
            description="Analyzes international media perspectives",
            category="perspectives",
            provider=provider,
            temperature=0.7
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_international_news_tool]
        )
    
    async def analyze(self,
                     topic_summary: str,
                     story_category: Optional[str] = None,
                     greek_perspective: Optional[str] = None) -> InternationalPerspectiveOutput:
        """Analyze international media perspectives
        
        Args:
            topic_summary: Summary of the topic to analyze
            story_category: Category to help select relevant regions
            greek_perspective: Optional Greek perspective for comparison
            
        Returns:
            InternationalPerspectiveOutput with analysis
        """
        # Determine relevant regions based on story category
        regions = self._select_regions(story_category)
        
        # Build analysis prompt
        prompt = f"Analyze international media coverage of: {topic_summary}"
        
        prompt += f"\n\nFocus on these regions: {', '.join(regions)}"
        
        if greek_perspective:
            prompt += f"\n\nFor context, Greek media perspective: {greek_perspective[:200]}..."
        
        prompt += """

Tasks:
1. Search news sources from each specified region
2. Identify how each region frames this story
3. Find consensus points and major differences
4. Note cultural/political factors affecting coverage
5. Identify any missing perspectives

Provide balanced analysis considering source credibility and bias."""
        
        # Get analysis
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            # Build regional perspectives
            regional_perspectives = []
            for region_data in data.get("analysis", {}).get("regional_differences", []):
                perspective = RegionalPerspective(
                    region=region_data.get("region", ""),
                    narrative=region_data.get("narrative", ""),
                    emphasis=region_data.get("emphasis", []),
                    cultural_context=region_data.get("cultural_context")
                )
                regional_perspectives.append(perspective)
            
            analysis = InternationalAnalysis(
                global_consensus=data.get("analysis", {}).get("global_consensus"),
                regional_differences=regional_perspectives,
                contested_facts=data.get("analysis", {}).get("contested_facts", []),
                missing_perspectives=data.get("analysis", {}).get("missing_perspectives", []),
                bias_patterns=data.get("analysis", {}).get("bias_patterns", {})
            )
            
            return InternationalPerspectiveOutput(
                topic=topic_summary,
                summary=data.get("summary", ""),
                analysis=analysis,
                regions_covered=data.get("regions_covered", regions),
                confidence=float(data.get("confidence", 0.7))
            )
            
        except Exception as e:
            # Fallback
            return InternationalPerspectiveOutput(
                topic=topic_summary,
                summary=f"Error analyzing international perspectives: {str(e)}",
                analysis=InternationalAnalysis(
                    global_consensus=None,
                    regional_differences=[],
                    contested_facts=[],
                    missing_perspectives=[],
                    bias_patterns={}
                ),
                regions_covered=[],
                confidence=0.0
            )
    
    def _select_regions(self, story_category: Optional[str]) -> List[str]:
        """Select relevant regions based on story category
        
        Args:
            story_category: Category of the story
            
        Returns:
            List of regions to analyze
        """
        # Default regions
        default_regions = ["US", "UK", "EU"]
        
        if not story_category:
            return default_regions
        
        # Category-specific regions
        category_regions = {
            "global_politics": ["US", "UK", "EU", "Russia", "China"],
            "middle_east": ["US", "UK", "EU", "Middle East", "Israel"],
            "economy_business": ["US", "UK", "EU", "Asia", "China"],
            "science_tech": ["US", "UK", "EU", "Asia", "China"],
            "climate_environment": ["US", "UK", "EU", "China", "India"],
            "greek_politics": ["EU", "US", "UK", "Germany", "Turkey"]
        }
        
        return category_regions.get(story_category.lower(), default_regions)