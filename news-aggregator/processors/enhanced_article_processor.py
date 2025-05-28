"""
Enhanced article processor with storage and enrichment
"""
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.article_processor import ArticleProcessor
from processors.simple_ai_enrichment import SimpleAIEnrichment
from processors.comprehensive_ai_enrichment import ComprehensiveAIEnrichment
from storage.article_storage import ArticleStorage


class EnhancedArticleProcessor:
    """
    Enhanced processor that extracts, enriches, and stores articles
    """
    
    def __init__(self, use_comprehensive: bool = True):
        self.article_processor = ArticleProcessor()
        self.ai_enricher = SimpleAIEnrichment()
        self.comprehensive_enricher = ComprehensiveAIEnrichment() if use_comprehensive else None
        self.storage = ArticleStorage()
        self.use_comprehensive = use_comprehensive
    
    def process_article_url(self, url: str, enrich: bool = True) -> Dict[str, Any]:
        """
        Process article from URL with storage
        
        Args:
            url: Article URL to process
            enrich: Whether to enrich with AI analysis
            
        Returns:
            Dictionary with processing results
        """
        try:
            print(f"[Enhanced] Processing: {url}")
            
            # Step 1: Extract article
            article = self.article_processor.extract_article(url)
            print(f"[Enhanced] ✓ Extracted: {article.title[:50]}...")
            
            # Step 2: Store original article
            article_id = self.storage.store_article(article)
            print(f"[Enhanced] ✓ Stored article with ID: {article_id}")
            
            result = {
                'status': 'success',
                'article_id': article_id,
                'title': article.title,
                'word_count': article.word_count,
                'source': article.source_domain,
                'enriched': False
            }
            
            # Step 3: Enrich if requested
            if enrich:
                try:
                    print(f"[Enhanced] Starting AI enrichment...")
                    
                    if self.use_comprehensive and self.comprehensive_enricher:
                        # Use comprehensive enrichment with all agents
                        enriched = self.comprehensive_enricher.enrich_article(article)
                        
                        # Store enriched version (comprehensive format)
                        filepath = self.comprehensive_enricher.save_enriched_article(enriched, article_id)
                        
                        result.update({
                            'enriched': True,
                            'enrichment_type': 'comprehensive',
                            'analyses_completed': enriched.metadata.get('successful_analyses', []),
                            'analyses_failed': enriched.metadata.get('failed_analyses', []),
                            'enrichment_duration': enriched.metadata.get('duration_seconds', 0),
                            'enrichment_file': filepath
                        })
                    else:
                        # Use simple enrichment
                        enriched = self.ai_enricher.enrich_article(article)
                        
                        # Store enriched version
                        self.storage.store_enriched_article(enriched, article_id)
                        
                        result.update({
                            'enriched': True,
                            'enrichment_type': 'simple',
                            'analyses_completed': enriched.metadata.get('analyses_completed', []),
                            'enrichment_duration': enriched.metadata.get('duration_seconds', 0)
                        })
                    
                    print(f"[Enhanced] ✓ Enrichment completed")
                    
                except Exception as e:
                    print(f"[Enhanced] ✗ Enrichment failed: {e}")
                    result['enrichment_error'] = str(e)
            
            return result
            
        except Exception as e:
            print(f"[Enhanced] ✗ Processing failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get stored article by ID"""
        return self.storage.get_article(article_id)
    
    def list_articles(self, limit: int = 50, enriched_only: bool = False) -> Dict[str, Any]:
        """List stored articles"""
        articles = self.storage.list_articles(limit=limit, enriched_only=enriched_only)
        stats = self.storage.get_stats()
        
        return {
            'articles': articles,
            'stats': stats,
            'total_found': len(articles)
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return self.storage.get_stats()
    
    def close(self):
        """Close processors"""
        self.article_processor.close()