"""Greek Perspective Agent for analyzing Greek media coverage"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_greek_news_tool


class GreekMediaAnalysis(BaseModel):
    """Analysis of Greek media coverage"""
    dominant_narrative: str = Field(description="The main narrative in Greek media")
    unique_angles: List[str] = Field(description="Angles unique to Greek coverage")
    emphasized_aspects: List[str] = Field(description="What Greek media emphasizes")
    ignored_aspects: List[str] = Field(description="What Greek media ignores or downplays")
    political_spin: Optional[str] = Field(description="Any detected political bias or spin")
    source_diversity: str = Field(description="Diversity of sources (high/medium/low)")
    public_sentiment: Optional[str] = Field(description="General public sentiment if detectable")


class GreekPerspectiveOutput(BaseModel):
    """Output from Greek perspective analysis"""
    topic: str
    summary: str = Field(description="200-word synthesis of Greek perspective")
    analysis: GreekMediaAnalysis
    key_sources: List[str] = Field(description="Main Greek sources analyzed")
    confidence: float = Field(description="Confidence in analysis (0.0-1.0)", ge=0.0, le=1.0)


class GreekPerspectiveAgent(BaseNewsAgent):
    """Agent for analyzing Greek media perspective on a topic"""
    
    def __init__(self, provider: str = "grok"):
        """Initialize Greek perspective agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert analyst of Greek media and public discourse.

Your task is to research and analyze how GREEK media is covering a given topic.

Your responsibilities:
1. Search Greek news sources comprehensively (mainstream and alternative)
2. Identify the dominant Greek narrative and consensus
3. Find uniquely Greek concerns, angles, or perspectives
4. Note what Greek media emphasizes versus what it ignores
5. Detect any political spin or bias in coverage
6. Assess source diversity (left/right/center perspectives)
7. Gauge public sentiment if possible

Greek media landscape context:
- Mainstream: Kathimerini (center-right), Ta Nea (center), Proto Thema (center-right)
- Left-leaning: Efsyn, Avgi, Documento
- Alternative: The TOC, Liberal.gr
- TV/Digital: SKAI, ANT1, MEGA, ERT

Key requirements:
- Synthesize findings into a clear 200-word summary
- Maintain objectivity while noting biases
- Consider both Greek and English-language Greek sources
- Focus on substantive coverage, not just headlines
- Note if coverage differs significantly from international media

Output as structured JSON matching the GreekPerspectiveOutput schema."""
        
        config = AgentConfig(
            name="greek_perspective",
            description="Analyzes Greek media perspective on topics",
            category="perspectives",
            provider=provider,
            temperature=0.7
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_greek_news_tool]
        )
    
    async def analyze(self, 
                     topic_summary: str,
                     story_headline: Optional[str] = None,
                     key_facts: Optional[List[str]] = None) -> GreekPerspectiveOutput:
        """Analyze Greek media perspective on a topic
        
        Args:
            topic_summary: Summary of the topic to analyze
            story_headline: Optional specific headline
            key_facts: Optional key facts about the story
            
        Returns:
            GreekPerspectiveOutput with analysis
        """
        # Build analysis prompt
        prompt = f"Analyze Greek media coverage of: {topic_summary}"
        
        if story_headline:
            prompt += f"\n\nHeadline: {story_headline}"
        
        if key_facts:
            prompt += "\n\nKey facts to verify in Greek coverage:"
            for fact in key_facts:
                prompt += f"\n- {fact}"
        
        prompt += """

Tasks:
1. Search both mainstream and alternative Greek news sources
2. Identify how Greek media frames this story
3. Find perspectives unique to Greek coverage
4. Note any political angles or biases
5. Assess what aspects get emphasized or ignored

Focus on substantive analysis, not just listing sources."""
        
        # Get analysis with structured output
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            analysis = GreekMediaAnalysis(
                dominant_narrative=data.get("analysis", {}).get("dominant_narrative", ""),
                unique_angles=data.get("analysis", {}).get("unique_angles", []),
                emphasized_aspects=data.get("analysis", {}).get("emphasized_aspects", []),
                ignored_aspects=data.get("analysis", {}).get("ignored_aspects", []),
                political_spin=data.get("analysis", {}).get("political_spin"),
                source_diversity=data.get("analysis", {}).get("source_diversity", "medium"),
                public_sentiment=data.get("analysis", {}).get("public_sentiment")
            )
            
            return GreekPerspectiveOutput(
                topic=topic_summary,
                summary=data.get("summary", ""),
                analysis=analysis,
                key_sources=data.get("key_sources", []),
                confidence=float(data.get("confidence", 0.7))
            )
            
        except Exception as e:
            # Fallback
            return GreekPerspectiveOutput(
                topic=topic_summary,
                summary=f"Error analyzing Greek perspective: {str(e)}",
                analysis=GreekMediaAnalysis(
                    dominant_narrative="Analysis failed",
                    unique_angles=[],
                    emphasized_aspects=[],
                    ignored_aspects=[],
                    political_spin=None,
                    source_diversity="unknown",
                    public_sentiment=None
                ),
                key_sources=[],
                confidence=0.0
            )
    
    def assess_political_spectrum(self, sources: List[str]) -> Dict[str, int]:
        """Assess political spectrum coverage
        
        Args:
            sources: List of source domains
            
        Returns:
            Dict with counts by political leaning
        """
        spectrum_map = {
            "left": ["efsyn.gr", "avgi.gr", "documento.gr"],
            "center-left": ["tanea.gr", "tovima.gr"],
            "center": ["in.gr", "news247.gr"],
            "center-right": ["kathimerini.gr", "skai.gr"],
            "right": ["protothema.gr", "liberal.gr"]
        }
        
        counts = {"left": 0, "center": 0, "right": 0, "unknown": 0}
        
        for source in sources:
            found = False
            for leaning, domains in spectrum_map.items():
                if any(domain in source for domain in domains):
                    if "left" in leaning:
                        counts["left"] += 1
                    elif "right" in leaning:
                        counts["right"] += 1
                    else:
                        counts["center"] += 1
                    found = True
                    break
            
            if not found:
                counts["unknown"] += 1
        
        return counts