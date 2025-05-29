"""
AI Enrichment for articles using News Copilot agents
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import (
    JargonAgent, ViewpointsAgent, FactCheckAgent,
    BiasAnalysisAgent, TimelineAgent, ExpertOpinionsAgent
)
from processors.article_processor import ProcessedArticle
from config.config import AGENT_CONFIG, XAI_API_KEY, ENRICHED_DIR


@dataclass
class EnrichedArticle:
    """Article with AI-powered enrichments"""
    original_article: ProcessedArticle
    jargon_terms: Optional[Dict[str, Any]] = None
    viewpoints: Optional[Dict[str, Any]] = None
    fact_checks: Optional[Dict[str, Any]] = None
    bias_analysis: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    expert_opinions: Optional[Dict[str, Any]] = None
    enrichment_metadata: Optional[Dict[str, Any]] = None
    

class AIEnrichmentProcessor:
    """Process articles with AI-powered analysis"""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all analysis agents"""
        return {
            "jargon": JargonAgent(api_key=XAI_API_KEY),
            "viewpoints": ViewpointsAgent(api_key=XAI_API_KEY),
            "fact_check": FactCheckAgent(api_key=XAI_API_KEY),
            "bias": BiasAnalysisAgent(api_key=XAI_API_KEY),
            "timeline": TimelineAgent(api_key=XAI_API_KEY),
            "expert": ExpertOpinionsAgent(api_key=XAI_API_KEY)
        }
    
    async def enrich_article_async(self, article: ProcessedArticle, 
                                  analyses: List[str] = None) -> EnrichedArticle:
        """
        Enrich article with AI analyses asynchronously
        
        Args:
            article: ProcessedArticle to enrich
            analyses: List of analyses to perform (default: all)
            
        Returns:
            EnrichedArticle with AI enrichments
        """
        if analyses is None:
            analyses = ["jargon", "viewpoints", "fact_check", "bias", "timeline", "expert"]
        
        start_time = datetime.now()
        print(f"[AIEnrichment] Starting enrichment for: {article.title[:50]}...")
        
        # Create tasks for parallel execution
        tasks = {}
        for analysis_type in analyses:
            if analysis_type in self.agents:
                agent = self.agents[analysis_type]
                task = asyncio.create_task(self._run_agent_async(
                    agent, article, analysis_type
                ))
                tasks[analysis_type] = task
        
        # Wait for all tasks to complete
        results = {}
        for analysis_type, task in tasks.items():
            try:
                result = await task
                results[analysis_type] = result
                print(f"[AIEnrichment] ✓ Completed {analysis_type} analysis")
            except Exception as e:
                print(f"[AIEnrichment] ✗ Failed {analysis_type} analysis: {e}")
                results[analysis_type] = {"error": str(e)}
        
        # Create enriched article
        enriched = EnrichedArticle(
            original_article=article,
            jargon_terms=results.get("jargon"),
            viewpoints=results.get("viewpoints"),
            fact_checks=results.get("fact_check"),
            bias_analysis=results.get("bias"),
            timeline=results.get("timeline"),
            expert_opinions=results.get("expert"),
            enrichment_metadata={
                "analyses_requested": analyses,
                "analyses_completed": [k for k, v in results.items() if "error" not in v],
                "enrichment_date": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
        )
        
        print(f"[AIEnrichment] Enrichment completed in {enriched.enrichment_metadata['duration_seconds']:.1f}s")
        return enriched
    
    async def _run_agent_async(self, agent: Any, article: ProcessedArticle, 
                              analysis_type: str) -> Dict[str, Any]:
        """Run an agent asynchronously"""
        # Most agents have async analyze methods
        if hasattr(agent, 'analyze'):
            result = await agent.analyze(article.content, article.url)
            return result.dict() if hasattr(result, 'dict') else result
        else:
            # Fallback for agents without analyze method
            return {"error": f"Agent {analysis_type} does not have analyze method"}
    
    def enrich_article(self, article: ProcessedArticle, 
                      analyses: List[str] = None) -> EnrichedArticle:
        """
        Synchronous wrapper for article enrichment
        """
        return asyncio.run(self.enrich_article_async(article, analyses))
    
    def save_enriched_article(self, enriched: EnrichedArticle, format: str = "json") -> str:
        """
        Save enriched article to file
        
        Args:
            enriched: EnrichedArticle to save
            format: Export format (json, md)
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in enriched.original_article.title 
                           if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        
        if format == "json":
            filename = f"{timestamp}_{safe_title}_enriched.json"
            filepath = os.path.join(ENRICHED_DIR, filename)
            
            # Convert to dict
            data = {
                "article": asdict(enriched.original_article),
                "enrichments": {
                    "jargon": enriched.jargon_terms,
                    "viewpoints": enriched.viewpoints,
                    "fact_checks": enriched.fact_checks,
                    "bias_analysis": enriched.bias_analysis,
                    "timeline": enriched.timeline,
                    "expert_opinions": enriched.expert_opinions
                },
                "metadata": enriched.enrichment_metadata
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif format == "md":
            filename = f"{timestamp}_{safe_title}_enriched.md"
            filepath = os.path.join(ENRICHED_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"# {enriched.original_article.title}\n\n")
                f.write(f"**URL:** {enriched.original_article.url}\n")
                f.write(f"**Source:** {enriched.original_article.source_domain}\n")
                f.write(f"**Extracted:** {enriched.original_article.extracted_date}\n\n")
                
                # Write original content
                f.write("## Original Content\n\n")
                f.write(enriched.original_article.content + "\n\n")
                
                # Write enrichments
                if enriched.jargon_terms:
                    f.write("## Jargon Terms\n\n")
                    f.write(json.dumps(enriched.jargon_terms, ensure_ascii=False, indent=2))
                    f.write("\n\n")
                
                if enriched.viewpoints:
                    f.write("## Alternative Viewpoints\n\n")
                    f.write(json.dumps(enriched.viewpoints, ensure_ascii=False, indent=2))
                    f.write("\n\n")
                
                if enriched.fact_checks:
                    f.write("## Fact Checks\n\n")
                    f.write(json.dumps(enriched.fact_checks, ensure_ascii=False, indent=2))
                    f.write("\n\n")
                
                if enriched.bias_analysis:
                    f.write("## Bias Analysis\n\n")
                    f.write(json.dumps(enriched.bias_analysis, ensure_ascii=False, indent=2))
                    f.write("\n\n")
                
                if enriched.timeline:
                    f.write("## Timeline\n\n")
                    f.write(json.dumps(enriched.timeline, ensure_ascii=False, indent=2))
                    f.write("\n\n")
                
                if enriched.expert_opinions:
                    f.write("## Expert Opinions\n\n")
                    f.write(json.dumps(enriched.expert_opinions, ensure_ascii=False, indent=2))
                    f.write("\n\n")
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"[AIEnrichment] Saved enriched article to: {filepath}")
        return filepath