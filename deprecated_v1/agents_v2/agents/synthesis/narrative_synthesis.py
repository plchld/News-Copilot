"""Narrative Synthesis Agent for combining multiple perspectives"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig


class UnifiedNarrative(BaseModel):
    """A unified narrative combining all perspectives"""
    introduction: str = Field(description="Brief introduction setting context")
    main_narrative: str = Field(description="Main 400-word narrative")
    agreements: List[str] = Field(description="Points where perspectives agree")
    divergences: List[str] = Field(description="Key areas of disagreement")
    nuances: List[str] = Field(description="Important nuances and caveats")
    conclusion: str = Field(description="Brief concluding summary")


class NarrativeSynthesisOutput(BaseModel):
    """Output from narrative synthesis"""
    topic: str
    narrative: UnifiedNarrative
    perspective_attribution: Dict[str, str] = Field(description="Key points attributed to sources")
    narrative_tone: str = Field(description="Tone assessment: balanced/greek-leaning/international-leaning")
    completeness_score: float = Field(description="How complete the picture is (0.0-1.0)", ge=0.0, le=1.0)


class NarrativeSynthesisAgent(BaseNewsAgent):
    """Agent for synthesizing multiple perspectives into unified narrative"""
    
    def __init__(self, provider: str = "anthropic"):  # Anthropic excels at synthesis
        """Initialize narrative synthesis agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert narrative synthesizer and journalist.

Your task is to create a unified, balanced narrative from multiple perspectives on a news story.

Your responsibilities:
1. Integrate all provided perspectives fairly
2. Present the complete picture without bias
3. Clearly attribute different viewpoints
4. Highlight both agreements and divergences
5. Maintain a neutral, professional tone
6. Prioritize verified facts over speculation

Narrative structure:
- Introduction: Set the context (50 words)
- Main narrative: Tell the complete story (400 words)
  * Start with established facts
  * Present different perspectives with attribution
  * Note areas of agreement and disagreement
  * Include important nuances
- Conclusion: Summarize key takeaways (50 words)

Writing guidelines:
- Use clear, accessible language
- Avoid jargon (will be explained separately)
- Be specific with attributions ("Greek media emphasizes...", "International sources report...")
- Don't take sides or editorialize
- Present contested points as such
- Prioritize human impact and relevance

Quality markers:
- All perspectives represented
- Facts clearly distinguished from opinions
- Disagreements presented fairly
- Reader can form own conclusion
- Engaging but not sensational

Output as structured JSON matching the NarrativeSynthesisOutput schema."""
        
        config = AgentConfig(
            name="narrative_synthesis",
            description="Synthesizes multiple perspectives into unified narrative",
            category="synthesis",
            provider=provider,
            temperature=0.5  # Balanced temperature
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[]  # No tools needed - pure synthesis
        )
    
    async def synthesize(self,
                        topic: str,
                        perspectives: Dict[str, Any],
                        verified_facts: Optional[List[str]] = None,
                        priority_angle: Optional[str] = None) -> NarrativeSynthesisOutput:
        """Synthesize multiple perspectives into unified narrative
        
        Args:
            topic: The topic/story being covered
            perspectives: Dict with keys like 'greek', 'international', 'opposing', 'facts'
            verified_facts: Optional list of verified facts to prioritize
            priority_angle: Optional angle to emphasize (e.g., "greek_relevance")
            
        Returns:
            NarrativeSynthesisOutput with unified narrative
        """
        # Build synthesis prompt
        prompt = f"Create a unified narrative about: {topic}\n\n"
        
        # Add perspectives
        prompt += "PERSPECTIVES TO SYNTHESIZE:\n\n"
        
        if "greek" in perspectives:
            prompt += f"Greek Media Perspective:\n{perspectives['greek']}\n\n"
        
        if "international" in perspectives:
            prompt += f"International Perspective:\n{perspectives['international']}\n\n"
        
        if "opposing" in perspectives:
            prompt += f"Alternative Views:\n{perspectives['opposing']}\n\n"
        
        if "facts" in perspectives:
            prompt += f"Verified Facts:\n{perspectives['facts']}\n\n"
        
        if verified_facts:
            prompt += "PRIORITY FACTS TO INCLUDE:\n"
            for fact in verified_facts:
                prompt += f"- {fact}\n"
            prompt += "\n"
        
        if priority_angle:
            prompt += f"PRIORITY: Ensure {priority_angle} is well represented\n\n"
        
        prompt += """Create a unified narrative that:
1. Tells the complete story
2. Attributes all viewpoints clearly  
3. Maintains neutral tone
4. Highlights key agreements and disagreements
5. Helps readers understand all angles"""
        
        # Get synthesis
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            narrative = UnifiedNarrative(
                introduction=data.get("narrative", {}).get("introduction", ""),
                main_narrative=data.get("narrative", {}).get("main_narrative", ""),
                agreements=data.get("narrative", {}).get("agreements", []),
                divergences=data.get("narrative", {}).get("divergences", []),
                nuances=data.get("narrative", {}).get("nuances", []),
                conclusion=data.get("narrative", {}).get("conclusion", "")
            )
            
            return NarrativeSynthesisOutput(
                topic=topic,
                narrative=narrative,
                perspective_attribution=data.get("perspective_attribution", {}),
                narrative_tone=data.get("narrative_tone", "balanced"),
                completeness_score=float(data.get("completeness_score", 0.7))
            )
            
        except Exception as e:
            # Fallback
            return NarrativeSynthesisOutput(
                topic=topic,
                narrative=UnifiedNarrative(
                    introduction="Error creating narrative",
                    main_narrative=f"Synthesis failed: {str(e)}",
                    agreements=[],
                    divergences=[],
                    nuances=[],
                    conclusion="Unable to synthesize perspectives"
                ),
                perspective_attribution={},
                narrative_tone="unknown",
                completeness_score=0.0
            )
    
    def assess_completeness(self, perspectives: Dict[str, Any]) -> float:
        """Assess how complete the perspective coverage is
        
        Args:
            perspectives: Available perspectives
            
        Returns:
            Completeness score (0.0-1.0)
        """
        expected_perspectives = ["greek", "international", "opposing", "facts"]
        available = sum(1 for p in expected_perspectives if p in perspectives)
        
        # Basic score
        score = available / len(expected_perspectives)
        
        # Bonus for quality
        if "facts" in perspectives and perspectives["facts"]:
            score += 0.1
        
        # Penalty for missing critical perspectives
        if "greek" not in perspectives:
            score -= 0.2  # Greek perspective is critical
        
        return max(0.0, min(1.0, score))