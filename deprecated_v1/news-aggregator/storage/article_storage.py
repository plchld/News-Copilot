"""
Article storage system for saving articles and enrichments
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from processors.article_processor import ProcessedArticle
from processors.simple_ai_enrichment import SimpleEnrichedArticle
from config.config import PROCESSED_DIR, ENRICHED_DIR


@dataclass
class StoredArticle:
    """Article with storage metadata"""
    id: str
    original_url: str
    title: str
    content: str
    source_domain: str
    word_count: int
    extracted_date: str
    storage_date: str
    file_path: str
    enriched: bool = False
    enriched_file_path: Optional[str] = None


class ArticleStorage:
    """Storage system for articles and enrichments"""
    
    def __init__(self):
        self.processed_dir = PROCESSED_DIR
        self.enriched_dir = ENRICHED_DIR
        self.index_file = os.path.join(self.processed_dir, "article_index.json")
        
        # Ensure directories exist
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.enriched_dir, exist_ok=True)
        
        # Load or create index
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict]:
        """Load article index from file"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Storage] Error loading index: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """Save article index to file"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Storage] Error saving index: {e}")
    
    def _generate_article_id(self, url: str) -> str:
        """Generate unique article ID from URL"""
        # Use SHA-256 hash of URL for consistent ID
        return hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
    
    def store_article(self, article: ProcessedArticle) -> str:
        """
        Store processed article
        
        Returns:
            Article ID
        """
        article_id = self._generate_article_id(article.url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        safe_title = "".join(c for c in article.title 
                           if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        filename = f"{timestamp}_{article_id}_{safe_title}.json"
        filepath = os.path.join(self.processed_dir, filename)
        
        # Save article data
        article_data = asdict(article)
        article_data['storage_metadata'] = {
            'id': article_id,
            'storage_date': datetime.now().isoformat(),
            'filepath': filepath
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        
        # Update index
        stored_article = StoredArticle(
            id=article_id,
            original_url=article.url,
            title=article.title,
            content=article.content[:200] + "..." if len(article.content) > 200 else article.content,
            source_domain=article.source_domain,
            word_count=article.word_count,
            extracted_date=article.extracted_date,
            storage_date=datetime.now().isoformat(),
            file_path=filepath,
            enriched=False
        )
        
        self.index[article_id] = asdict(stored_article)
        self._save_index()
        
        print(f"[Storage] Stored article {article_id}: {article.title[:50]}...")
        return article_id
    
    def store_enriched_article(self, enriched: SimpleEnrichedArticle, article_id: str = None) -> str:
        """
        Store enriched article
        
        Returns:
            Enriched article ID
        """
        if article_id is None:
            article_id = self._generate_article_id(enriched.original_article.url)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        safe_title = "".join(c for c in enriched.original_article.title 
                           if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        filename = f"{timestamp}_{article_id}_{safe_title}_enriched.json"
        filepath = os.path.join(self.enriched_dir, filename)
        
        # Save enriched data
        enriched_data = {
            'id': article_id,
            'article': asdict(enriched.original_article),
            'enrichments': enriched.enrichments,
            'metadata': enriched.metadata,
            'storage_metadata': {
                'enriched_id': f"{article_id}_enriched",
                'storage_date': datetime.now().isoformat(),
                'filepath': filepath
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
        # Update index to mark as enriched
        if article_id in self.index:
            self.index[article_id]['enriched'] = True
            self.index[article_id]['enriched_file_path'] = filepath
        else:
            # Create new entry if article wasn't stored separately
            stored_article = StoredArticle(
                id=article_id,
                original_url=enriched.original_article.url,
                title=enriched.original_article.title,
                content=enriched.original_article.content[:200] + "..." if len(enriched.original_article.content) > 200 else enriched.original_article.content,
                source_domain=enriched.original_article.source_domain,
                word_count=enriched.original_article.word_count,
                extracted_date=enriched.original_article.extracted_date,
                storage_date=datetime.now().isoformat(),
                file_path="",  # Not stored separately
                enriched=True,
                enriched_file_path=filepath
            )
            self.index[article_id] = asdict(stored_article)
        
        self._save_index()
        
        print(f"[Storage] Stored enriched article {article_id}: {enriched.original_article.title[:50]}...")
        return article_id
    
    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get article by ID"""
        if article_id not in self.index:
            return None
        
        article_info = self.index[article_id]
        
        # Load original article if exists
        result = {'index_info': article_info}
        
        if article_info.get('file_path') and os.path.exists(article_info['file_path']):
            with open(article_info['file_path'], 'r', encoding='utf-8') as f:
                result['original'] = json.load(f)
        
        # Load enriched article if exists
        if article_info.get('enriched_file_path') and os.path.exists(article_info['enriched_file_path']):
            with open(article_info['enriched_file_path'], 'r', encoding='utf-8') as f:
                result['enriched'] = json.load(f)
        
        return result
    
    def list_articles(self, limit: int = 50, enriched_only: bool = False) -> List[Dict]:
        """List articles from index"""
        articles = list(self.index.values())
        
        if enriched_only:
            articles = [a for a in articles if a.get('enriched', False)]
        
        # Sort by storage date (newest first)
        articles.sort(key=lambda x: x.get('storage_date', ''), reverse=True)
        
        return articles[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_articles = len(self.index)
        enriched_articles = len([a for a in self.index.values() if a.get('enriched', False)])
        
        # Get source distribution
        sources = {}
        for article in self.index.values():
            domain = article.get('source_domain', 'unknown')
            sources[domain] = sources.get(domain, 0) + 1
        
        return {
            'total_articles': total_articles,
            'enriched_articles': enriched_articles,
            'unenriched_articles': total_articles - enriched_articles,
            'sources': sources,
            'storage_dirs': {
                'processed': self.processed_dir,
                'enriched': self.enriched_dir
            }
        }
    
    def cleanup_orphaned_files(self):
        """Remove files not in index"""
        # This could be implemented to clean up files that aren't in the index
        pass