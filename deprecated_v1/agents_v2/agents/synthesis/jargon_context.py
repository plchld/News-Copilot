"""Jargon & Context Agent for explaining complex terms"""

import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_web_tool


class JargonTerm(BaseModel):
    """A jargon term with explanation"""
    term: str = Field(description="The term or acronym")
    explanation: str = Field(description="Simple explanation in plain language")
    greek_translation: Optional[str] = Field(description="Greek translation if helpful")
    context: Optional[str] = Field(description="Additional context if needed")
    category: str = Field(description="Category: technical/political/economic/scientific/cultural")


class JargonAnalysis(BaseModel):
    """Analysis of jargon and complex terms"""
    terms: List[JargonTerm] = Field(description="List of terms needing explanation")
    complexity_level: str = Field(description="Overall complexity: low/medium/high")
    reading_level: str = Field(description="Estimated reading level required")
    key_concepts: List[str] = Field(description="Key concepts for understanding")


class JargonContextOutput(BaseModel):
    """Output from jargon analysis"""
    narrative_analyzed: bool = Field(description="Whether narrative was successfully analyzed")
    analysis: JargonAnalysis
    jargon_dictionary: Dict[str, str] = Field(description="Simple term->explanation mapping")
    accessibility_score: float = Field(description="How accessible the text is (0.0-1.0)", ge=0.0, le=1.0)
    recommendations: List[str] = Field(description="Recommendations for clarity")


class JargonContextAgent(BaseNewsAgent):
    """Agent for identifying and explaining jargon/complex terms"""
    
    def __init__(self, provider: str = "grok"):
        """Initialize jargon context agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert at making complex information accessible.

Your task is to identify and explain technical terms, acronyms, and complex concepts in news narratives.

Your responsibilities:
1. Identify ALL technical terms, acronyms, and jargon
2. Research simple, accurate explanations
3. Add Greek translations where helpful
4. Provide essential context for understanding
5. Categorize terms by type
6. Assess overall complexity

Term identification criteria:
- Technical terms specific to a field
- Acronyms and abbreviations
- Political/economic jargon
- Cultural references needing context
- Complex concepts
- Foreign terms

Explanation guidelines:
- Use simple, everyday language
- Keep explanations concise (1-2 sentences)
- Add Greek translation for key terms
- Include pronunciation for difficult words
- Provide context when needed

Categories to use:
- technical: Technology, engineering terms
- political: Government, policy terms
- economic: Finance, market terms
- scientific: Science, medical terms
- cultural: Cultural references, idioms

Quality markers:
- All jargon identified
- Explanations clear to general audience
- Greek translations accurate
- Context helpful but concise

Output as structured JSON matching the JargonContextOutput schema."""
        
        config = AgentConfig(
            name="jargon_context",
            description="Identifies and explains complex terms",
            category="synthesis",
            provider=provider,
            temperature=0.3  # Low temperature for accuracy
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_web_tool]
        )
    
    async def process(self,
                     narrative: str,
                     topic_category: Optional[str] = None,
                     target_audience: str = "general_public") -> JargonContextOutput:
        """Analyze narrative for jargon and complex terms
        
        Args:
            narrative: The narrative text to analyze
            topic_category: Optional category to help identify domain-specific terms
            target_audience: Target audience level
            
        Returns:
            JargonContextOutput with explanations
        """
        # Build analysis prompt
        prompt = f"Analyze this narrative for jargon and complex terms:\n\n{narrative}\n\n"
        
        if topic_category:
            prompt += f"Topic category: {topic_category}\n"
        
        prompt += f"Target audience: {target_audience}\n\n"
        
        prompt += """Tasks:
1. Identify ALL terms that might confuse a general reader
2. Research accurate, simple explanations
3. Add Greek translations for important terms
4. Categorize each term
5. Assess overall complexity

Remember: If you'd need to Google it, explain it."""
        
        # Get analysis
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            # Build term list
            terms = []
            jargon_dict = {}
            
            for term_data in data.get("analysis", {}).get("terms", []):
                term = JargonTerm(
                    term=term_data.get("term", ""),
                    explanation=term_data.get("explanation", ""),
                    greek_translation=term_data.get("greek_translation"),
                    context=term_data.get("context"),
                    category=term_data.get("category", "technical")
                )
                terms.append(term)
                
                # Simple dictionary entry
                jargon_dict[term.term] = term.explanation
            
            analysis = JargonAnalysis(
                terms=terms,
                complexity_level=data.get("analysis", {}).get("complexity_level", "medium"),
                reading_level=data.get("analysis", {}).get("reading_level", "college"),
                key_concepts=data.get("analysis", {}).get("key_concepts", [])
            )
            
            # Calculate accessibility score
            accessibility = self._calculate_accessibility(len(terms), len(narrative.split()))
            
            return JargonContextOutput(
                narrative_analyzed=True,
                analysis=analysis,
                jargon_dictionary=jargon_dict,
                accessibility_score=accessibility,
                recommendations=data.get("recommendations", [])
            )
            
        except Exception as e:
            # Fallback
            return JargonContextOutput(
                narrative_analyzed=False,
                analysis=JargonAnalysis(
                    terms=[],
                    complexity_level="unknown",
                    reading_level="unknown",
                    key_concepts=[]
                ),
                jargon_dictionary={},
                accessibility_score=0.5,
                recommendations=[f"Analysis error: {str(e)}"]
            )
    
    def _calculate_accessibility(self, jargon_count: int, word_count: int) -> float:
        """Calculate accessibility score based on jargon density
        
        Args:
            jargon_count: Number of jargon terms
            word_count: Total word count
            
        Returns:
            Accessibility score (0.0-1.0)
        """
        if word_count == 0:
            return 0.5
        
        # Jargon density (terms per 100 words)
        density = (jargon_count / word_count) * 100
        
        # Score calculation (lower density = higher accessibility)
        if density < 1:
            return 0.9  # Very accessible
        elif density < 3:
            return 0.7  # Accessible
        elif density < 5:
            return 0.5  # Moderate
        elif density < 8:
            return 0.3  # Complex
        else:
            return 0.1  # Very complex
    
    def extract_terms(self, text: str) -> List[str]:
        """Extract potential jargon terms from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of potential terms
        """
        # Patterns for common jargon
        patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+(?:ization|isation)\b',  # -ization words
            r'\b\w+(?:ology|ological)\b',  # -ology words
            r'\b(?:crypto|cyber|nano|bio|geo)\w+\b',  # Tech prefixes
            r'\b\w+(?:ware|tech|chain)\b',  # Tech suffixes
        ]
        
        terms = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.update(matches)
        
        return list(terms)