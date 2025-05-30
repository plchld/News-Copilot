"""Opposing View Agent for finding alternative and contrarian perspectives"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_web_tool


class AlternativeView(BaseModel):
    """An alternative or contrarian viewpoint"""
    viewpoint: str = Field(description="The alternative perspective")
    source_type: str = Field(description="Type of source: independent/fact-checker/expert/minority")
    key_arguments: List[str] = Field(description="Main arguments supporting this view")
    evidence_quality: str = Field(description="Quality of evidence: strong/moderate/weak")
    
    
class OpposingAnalysis(BaseModel):
    """Analysis of opposing and alternative views"""
    mainstream_gaps: List[str] = Field(description="What mainstream media might be missing")
    alternative_narratives: List[AlternativeView] = Field(description="Alternative perspectives found")
    disputed_claims: List[str] = Field(description="Claims disputed by fact-checkers")
    reasonable_skepticism: List[str] = Field(description="Valid skeptical points")
    conspiracy_warnings: Optional[List[str]] = Field(description="Conspiracy theories to avoid")
    

class OpposingViewOutput(BaseModel):
    """Output from opposing view analysis"""
    topic: str
    summary: str = Field(description="150-word synthesis of alternative perspectives")
    analysis: OpposingAnalysis
    credibility_assessment: str = Field(description="Overall credibility of alternative views")
    confidence: float = Field(description="Confidence in analysis (0.0-1.0)", ge=0.0, le=1.0)


class OpposingViewAgent(BaseNewsAgent):
    """Agent for finding contrarian and alternative views"""
    
    def __init__(self, provider: str = "grok"):
        """Initialize opposing view agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert at finding legitimate alternative perspectives and contrarian views.

Your task is to find CREDIBLE opposing narratives and alternative viewpoints on a given topic.

Your responsibilities:
1. Search for opposing narratives from credible sources
2. Find what mainstream media might be missing or downplaying
3. Look for independent journalists' perspectives
4. Check fact-checking sites for disputed claims
5. Identify reasonable skepticism (NOT conspiracy theories)
6. Find minority expert opinions

Types of sources to consider:
- Independent journalists and substacks
- Academic experts with minority views
- Fact-checking organizations (Snopes, FactCheck.org, PolitiFact)
- Alternative media with good credibility
- Whistleblower reports
- Original source documents

Critical requirements:
- Distinguish between reasonable skepticism and conspiracy theories
- Focus on evidence-based alternative views
- Note the credibility of each alternative source
- Don't amplify misinformation
- Present alternative views fairly but critically
- Synthesize findings into 150 words

Red flags to avoid:
- Claims without credible sources
- Known conspiracy theory websites
- Anonymous sources making extraordinary claims
- Views based on demonstrably false premises

Output as structured JSON matching the OpposingViewOutput schema."""
        
        config = AgentConfig(
            name="opposing_view",
            description="Finds credible alternative perspectives",
            category="perspectives",
            provider=provider,
            temperature=0.8  # Slightly higher for creative search
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_web_tool]
        )
    
    async def analyze(self,
                     topic_summary: str,
                     mainstream_narrative: Optional[str] = None,
                     claimed_facts: Optional[List[str]] = None) -> OpposingViewOutput:
        """Find and analyze opposing views
        
        Args:
            topic_summary: Summary of the topic
            mainstream_narrative: Optional mainstream narrative to contrast
            claimed_facts: Optional facts to verify/dispute
            
        Returns:
            OpposingViewOutput with alternative perspectives
        """
        # Build search prompt
        prompt = f"Find credible alternative perspectives on: {topic_summary}"
        
        if mainstream_narrative:
            prompt += f"\n\nMainstream narrative: {mainstream_narrative[:200]}..."
        
        if claimed_facts:
            prompt += "\n\nClaims to investigate:"
            for fact in claimed_facts[:5]:  # Limit to 5
                prompt += f"\n- {fact}"
        
        prompt += """

Search strategy:
1. Look for "alternative view", "skeptics argue", "critics say"
2. Check fact-checking sites for this topic
3. Find independent journalists covering this differently
4. Look for minority expert opinions
5. Search for original documents/data

Remember: We want legitimate alternative views, not conspiracy theories."""
        
        # Get analysis
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            # Build alternative views
            alt_views = []
            for view_data in data.get("analysis", {}).get("alternative_narratives", []):
                view = AlternativeView(
                    viewpoint=view_data.get("viewpoint", ""),
                    source_type=view_data.get("source_type", "unknown"),
                    key_arguments=view_data.get("key_arguments", []),
                    evidence_quality=view_data.get("evidence_quality", "weak")
                )
                alt_views.append(view)
            
            analysis = OpposingAnalysis(
                mainstream_gaps=data.get("analysis", {}).get("mainstream_gaps", []),
                alternative_narratives=alt_views,
                disputed_claims=data.get("analysis", {}).get("disputed_claims", []),
                reasonable_skepticism=data.get("analysis", {}).get("reasonable_skepticism", []),
                conspiracy_warnings=data.get("analysis", {}).get("conspiracy_warnings")
            )
            
            return OpposingViewOutput(
                topic=topic_summary,
                summary=data.get("summary", ""),
                analysis=analysis,
                credibility_assessment=data.get("credibility_assessment", "mixed"),
                confidence=float(data.get("confidence", 0.6))
            )
            
        except Exception as e:
            # Fallback
            return OpposingViewOutput(
                topic=topic_summary,
                summary=f"Error finding alternative views: {str(e)}",
                analysis=OpposingAnalysis(
                    mainstream_gaps=[],
                    alternative_narratives=[],
                    disputed_claims=[],
                    reasonable_skepticism=[],
                    conspiracy_warnings=None
                ),
                credibility_assessment="unknown",
                confidence=0.0
            )
    
    def assess_source_credibility(self, source: str) -> str:
        """Assess credibility of a source
        
        Args:
            source: Source domain or name
            
        Returns:
            Credibility rating
        """
        # Known credible alternative sources
        high_credibility = [
            "substacK.com",
            "propublica.org",
            "theintercept.com",
            "factcheck.org",
            "snopes.com",
            "politifact.com"
        ]
        
        # Known low credibility
        low_credibility = [
            "infowars.com",
            "naturalnews.com",
            "beforeitsnews.com",
            "globalresearch.ca"
        ]
        
        source_lower = source.lower()
        
        if any(domain in source_lower for domain in high_credibility):
            return "high"
        elif any(domain in source_lower for domain in low_credibility):
            return "low"
        else:
            return "moderate"