"""
Comprehensive AI Enrichment using the full agent system
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.news_agent_coordinator import NewsAgentCoordinator
from processors.article_processor import ProcessedArticle
from config.config import ENRICHED_DIR


@dataclass
class ComprehensiveEnrichedArticle:
    """Article with comprehensive AI enrichments"""
    original_article: ProcessedArticle
    enrichments: Dict[str, Any]
    metadata: Dict[str, Any]


class ComprehensiveAIEnrichment:
    """Comprehensive AI enrichment using all available agents"""
    
    def __init__(self):
        self.coordinator = NewsAgentCoordinator()
        
    async def enrich_article_async(self, article: ProcessedArticle, 
                                  analyses: Optional[List[str]] = None) -> ComprehensiveEnrichedArticle:
        """
        Enrich article with comprehensive AI analysis
        
        Args:
            article: ProcessedArticle to enrich
            analyses: List of specific analyses to run (default: all)
            
        Returns:
            ComprehensiveEnrichedArticle with all enrichments
        """
        start_time = datetime.now()
        print(f"[ComprehensiveAI] Starting enrichment for: {article.title[:50]}...")
        
        try:
            # Run analysis
            if analyses:
                # Run subset of analyses
                results = await self.coordinator.analyze_article_subset(
                    article.content, article.url, analyses
                )
            else:
                # Run full analysis
                results = await self.coordinator.analyze_article_full(
                    article.content, article.url
                )
            
            # Format results for storage
            formatted_results = self.coordinator.format_results_for_storage(results)
            
            # Create metadata
            duration = (datetime.now() - start_time).total_seconds()
            metadata = {
                'enrichment_date': datetime.now().isoformat(),
                'duration_seconds': duration,
                'requested_analyses': analyses or self.coordinator.get_available_agents(),
                'successful_analyses': [name for name, result in results.items() 
                                      if result.status == "success"],
                'failed_analyses': [name for name, result in results.items() 
                                  if result.status != "success"],
                'agent_metadata': formatted_results['metadata']
            }
            
            # Create enriched article
            enriched = ComprehensiveEnrichedArticle(
                original_article=article,
                enrichments=formatted_results['analyses'],
                metadata=metadata
            )
            
            print(f"[ComprehensiveAI] Enrichment completed in {duration:.1f}s")
            print(f"[ComprehensiveAI] Successful: {len(metadata['successful_analyses'])}")
            print(f"[ComprehensiveAI] Failed: {len(metadata['failed_analyses'])}")
            
            return enriched
            
        except Exception as e:
            print(f"[ComprehensiveAI] Error during enrichment: {e}")
            raise
    
    def enrich_article(self, article: ProcessedArticle, 
                      analyses: Optional[List[str]] = None) -> ComprehensiveEnrichedArticle:
        """
        Synchronous wrapper for article enrichment
        """
        return asyncio.run(self.enrich_article_async(article, analyses))
    
    def get_available_analyses(self) -> List[str]:
        """Get list of available analysis types"""
        return self.coordinator.get_available_agents()
    
    def get_analysis_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available analyses"""
        return self.coordinator.get_agent_info()
    
    def save_enriched_article(self, enriched: ComprehensiveEnrichedArticle, 
                            article_id: str = None) -> str:
        """
        Save enriched article to file
        
        Args:
            enriched: ComprehensiveEnrichedArticle to save
            article_id: Optional article ID for filename
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in enriched.original_article.title 
                           if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        
        if article_id:
            filename = f"{timestamp}_{article_id}_{safe_title}_comprehensive.json"
        else:
            filename = f"{timestamp}_{safe_title}_comprehensive.json"
            
        filepath = os.path.join(ENRICHED_DIR, filename)
        
        # Prepare data for saving
        data = {
            'article': asdict(enriched.original_article),
            'enrichments': enriched.enrichments,
            'metadata': enriched.metadata,
            'save_timestamp': datetime.now().isoformat(),
            'version': '2.0'  # Version for comprehensive enrichment
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[ComprehensiveAI] Saved to: {filepath}")
        return filepath
    
    def create_analysis_summary(self, enriched: ComprehensiveEnrichedArticle) -> Dict[str, Any]:
        """Create a summary of the analysis results"""
        summary = {
            'article_info': {
                'title': enriched.original_article.title,
                'source': enriched.original_article.source_domain,
                'word_count': enriched.original_article.word_count,
                'url': enriched.original_article.url
            },
            'enrichment_summary': {
                'total_analyses': len(enriched.metadata['requested_analyses']),
                'successful': len(enriched.metadata['successful_analyses']),
                'failed': len(enriched.metadata['failed_analyses']),
                'duration': enriched.metadata['duration_seconds'],
                'success_rate': len(enriched.metadata['successful_analyses']) / len(enriched.metadata['requested_analyses']) * 100
            },
            'available_enrichments': list(enriched.enrichments.keys()),
            'analysis_date': enriched.metadata['enrichment_date']
        }
        
        # Add specific analysis summaries
        analysis_summaries = {}
        
        for analysis_name, data in enriched.enrichments.items():
            if isinstance(data, dict) and 'error' not in data:
                # Successful analysis
                if analysis_name == 'jargon' and 'terms' in data:
                    analysis_summaries[analysis_name] = f"{len(data['terms'])} terms explained"
                elif analysis_name == 'viewpoints' and 'viewpoints' in data:
                    analysis_summaries[analysis_name] = f"{len(data['viewpoints'])} alternative viewpoints"
                elif analysis_name == 'fact_check' and 'claims' in data:
                    analysis_summaries[analysis_name] = f"{len(data['claims'])} claims fact-checked"
                elif analysis_name == 'bias':
                    analysis_summaries[analysis_name] = "Bias analysis completed"
                elif analysis_name == 'timeline' and 'events' in data:
                    analysis_summaries[analysis_name] = f"{len(data['events'])} timeline events"
                elif analysis_name == 'expert' and 'opinions' in data:
                    analysis_summaries[analysis_name] = f"{len(data['opinions'])} expert opinions"
                else:
                    analysis_summaries[analysis_name] = "Analysis completed"
            else:
                # Failed analysis
                analysis_summaries[analysis_name] = f"Failed: {data.get('error', 'Unknown error')}"
        
        summary['analysis_summaries'] = analysis_summaries
        return summary