"""Fact Verification Agent for verifying claims and finding primary sources"""

import json
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from ..base import BaseNewsAgent, AgentConfig
from ...tools.search import search_web_tool


class FactCheck(BaseModel):
    """Result of checking a specific fact"""
    claim: str = Field(description="The claim being verified")
    verdict: str = Field(description="Verdict: confirmed/disputed/unverifiable/partially-true")
    confidence: float = Field(description="Confidence level (0.0-1.0)", ge=0.0, le=1.0)
    sources: List[str] = Field(description="Sources supporting the verdict")
    notes: Optional[str] = Field(description="Additional context or caveats")


class VerificationAnalysis(BaseModel):
    """Complete fact verification analysis"""
    verified_facts: List[FactCheck] = Field(description="List of fact checks performed")
    primary_sources: List[str] = Field(description="Primary sources found")
    conflicting_reports: List[str] = Field(description="Areas with conflicting information")
    data_quality: str = Field(description="Overall data quality: high/medium/low")
    key_uncertainties: List[str] = Field(description="What remains uncertain")


class FactVerificationOutput(BaseModel):
    """Output from fact verification"""
    topic: str
    summary: str = Field(description="Summary of fact verification findings")
    analysis: VerificationAnalysis
    overall_reliability: float = Field(description="Overall reliability score (0.0-1.0)", ge=0.0, le=1.0)
    recommendations: List[str] = Field(description="Recommendations for readers")


class FactVerificationAgent(BaseNewsAgent):
    """Agent for verifying facts and finding primary sources"""
    
    def __init__(self, provider: str = "grok"):
        """Initialize fact verification agent
        
        Args:
            provider: AI provider to use
        """
        instructions = """You are an expert fact-checker and verification specialist.

Your task is to VERIFY key claims about a given topic using primary sources and reliable data.

Your responsibilities:
1. Find primary sources (official statements, data, documents)
2. Check multiple reliable sources for each key fact
3. Identify which facts are contested or uncertain
4. Note confidence level for each claim
5. Find what we definitively know vs speculation
6. Identify conflicting reports and explain discrepancies

Verification methodology:
- Primary sources: Official websites, government data, academic papers
- Secondary sources: Reputable news organizations, fact-checking sites
- Verification levels:
  * Confirmed: Multiple reliable sources agree
  * Disputed: Credible sources disagree
  * Partially-true: True with important caveats
  * Unverifiable: Cannot be confirmed with available data

Source hierarchy:
1. Official statements/documents
2. Peer-reviewed research
3. Government statistics
4. Major news organizations
5. Expert analysis
6. Fact-checking organizations

Key requirements:
- Be rigorous and skeptical
- Note source reliability
- Distinguish facts from interpretation
- Identify speculation presented as fact
- Provide confidence levels
- Flag areas needing more investigation

Output as structured JSON matching the FactVerificationOutput schema."""
        
        config = AgentConfig(
            name="fact_verification",
            description="Verifies claims and finds primary sources",
            category="perspectives",
            provider=provider,
            temperature=0.3  # Lower temperature for accuracy
        )
        
        super().__init__(
            config=config,
            instructions=instructions,
            tools=[search_web_tool]
        )
    
    async def verify(self,
                    topic_summary: str,
                    claims_to_verify: Optional[List[str]] = None,
                    priority_facts: Optional[List[str]] = None) -> FactVerificationOutput:
        """Verify facts about a topic
        
        Args:
            topic_summary: Summary of the topic
            claims_to_verify: Specific claims to verify
            priority_facts: High-priority facts to focus on
            
        Returns:
            FactVerificationOutput with verification results
        """
        # Build verification prompt
        prompt = f"Verify key facts about: {topic_summary}"
        
        if priority_facts:
            prompt += "\n\nPriority facts to verify:"
            for fact in priority_facts[:5]:
                prompt += f"\n- {fact}"
        
        if claims_to_verify:
            prompt += "\n\nSpecific claims to check:"
            for claim in claims_to_verify[:5]:
                prompt += f"\n- {claim}"
        
        prompt += """

Verification tasks:
1. Search for primary sources and official statements
2. Cross-check facts across multiple reliable sources
3. Note any conflicting information
4. Assess confidence level for each fact
5. Identify what's confirmed vs speculation

Focus on factual accuracy, not opinions."""
        
        # Get verification results
        response = await self.run(
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            data = json.loads(response.content)
            
            # Build fact checks
            fact_checks = []
            for check_data in data.get("analysis", {}).get("verified_facts", []):
                check = FactCheck(
                    claim=check_data.get("claim", ""),
                    verdict=check_data.get("verdict", "unverifiable"),
                    confidence=float(check_data.get("confidence", 0.5)),
                    sources=check_data.get("sources", []),
                    notes=check_data.get("notes")
                )
                fact_checks.append(check)
            
            analysis = VerificationAnalysis(
                verified_facts=fact_checks,
                primary_sources=data.get("analysis", {}).get("primary_sources", []),
                conflicting_reports=data.get("analysis", {}).get("conflicting_reports", []),
                data_quality=data.get("analysis", {}).get("data_quality", "medium"),
                key_uncertainties=data.get("analysis", {}).get("key_uncertainties", [])
            )
            
            # Calculate overall reliability
            if fact_checks:
                avg_confidence = sum(fc.confidence for fc in fact_checks) / len(fact_checks)
                confirmed_ratio = len([fc for fc in fact_checks if fc.verdict == "confirmed"]) / len(fact_checks)
                overall_reliability = (avg_confidence + confirmed_ratio) / 2
            else:
                overall_reliability = 0.5
            
            return FactVerificationOutput(
                topic=topic_summary,
                summary=data.get("summary", ""),
                analysis=analysis,
                overall_reliability=overall_reliability,
                recommendations=data.get("recommendations", [])
            )
            
        except Exception as e:
            # Fallback
            return FactVerificationOutput(
                topic=topic_summary,
                summary=f"Error during fact verification: {str(e)}",
                analysis=VerificationAnalysis(
                    verified_facts=[],
                    primary_sources=[],
                    conflicting_reports=[],
                    data_quality="low",
                    key_uncertainties=["Verification failed"]
                ),
                overall_reliability=0.0,
                recommendations=["Treat all claims with caution"]
            )
    
    def calculate_verdict(self, supporting: int, disputing: int, total: int) -> Tuple[str, float]:
        """Calculate verdict based on source counts
        
        Args:
            supporting: Number of supporting sources
            disputing: Number of disputing sources  
            total: Total sources checked
            
        Returns:
            Tuple of (verdict, confidence)
        """
        if total == 0:
            return "unverifiable", 0.0
        
        support_ratio = supporting / total
        dispute_ratio = disputing / total
        
        if support_ratio > 0.8 and dispute_ratio < 0.1:
            return "confirmed", support_ratio
        elif dispute_ratio > 0.5:
            return "disputed", 1.0 - dispute_ratio
        elif support_ratio > 0.5:
            return "partially-true", support_ratio
        else:
            return "unverifiable", 0.3