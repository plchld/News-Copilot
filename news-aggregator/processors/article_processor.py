"""
Article processing module for news aggregation service
Handles extraction, analysis, and processing of news articles
"""
import re
import json
import trafilatura
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
from processors.enhanced_extractor import EnhancedExtractor


@dataclass
class ProcessedArticle:
    """Structured representation of a processed news article"""
    url: str
    title: str
    content: str
    source_domain: str
    published_date: Optional[str]
    extracted_date: str
    word_count: int
    metadata: Dict[str, Any]


class ArticleProcessor:
    """Enhanced article processor for news aggregation"""
    
    def __init__(self):
        self.user_agent = "News-Copilot-Aggregator/1.0"
        self.enhanced_extractor = EnhancedExtractor()
    
    def extract_article(self, url: str) -> ProcessedArticle:
        """
        Extract and process article from URL
        
        Args:
            url: The URL of the article to process
            
        Returns:
            ProcessedArticle object with structured data
            
        Raises:
            RuntimeError: If extraction fails
        """
        print(f"[ArticleProcessor] Processing URL: {url}")
        
        try:
            # Use enhanced extractor with fallback capabilities
            title, content, extraction_metadata = self.enhanced_extractor.extract_fallback(url)
            
            # Clean up content
            cleaned_content = re.sub(r"\s+", " ", content).strip()
            
            # Extract domain
            parsed_url = urlparse(url)
            source_domain = parsed_url.netloc
            
            # Calculate word count
            word_count = len(cleaned_content.split())
            
            # Merge metadata
            metadata = {
                'extraction_method': extraction_metadata.get('method', 'unknown'),
                'author': extraction_metadata.get('metadata', {}).get('author'),
                'description': extraction_metadata.get('metadata', {}).get('description'),
                'sitename': extraction_metadata.get('metadata', {}).get('sitename'),
                'categories': extraction_metadata.get('metadata', {}).get('categories', []),
                'tags': extraction_metadata.get('metadata', {}).get('tags', [])
            }
            
            # Try to extract published date
            published_date = None
            if 'metadata' in extraction_metadata:
                published_date = extraction_metadata['metadata'].get('date')
            
            # Create processed article
            article = ProcessedArticle(
                url=url,
                title=title,
                content=cleaned_content,
                source_domain=source_domain,
                published_date=published_date,
                extracted_date=datetime.now().isoformat(),
                word_count=word_count,
                metadata=metadata
            )
            
            print(f"[ArticleProcessor] Successfully processed article: {article.title}")
            print(f"[ArticleProcessor] Word count: {word_count}, Source: {source_domain}")
            print(f"[ArticleProcessor] Extraction method: {metadata['extraction_method']}")
            
            return article
            
        except Exception as e:
            error_message = f"Error processing article from {url}: {str(e)}"
            print(f"[ArticleProcessor] ERROR: {error_message}")
            raise RuntimeError(error_message)
    
    def to_dict(self, article: ProcessedArticle) -> Dict[str, Any]:
        """Convert ProcessedArticle to dictionary"""
        return asdict(article)
    
    def to_json(self, article: ProcessedArticle, indent: int = 2) -> str:
        """Convert ProcessedArticle to JSON string"""
        return json.dumps(self.to_dict(article), ensure_ascii=False, indent=indent)
    
    def close(self):
        """Close the enhanced extractor"""
        if hasattr(self, 'enhanced_extractor'):
            self.enhanced_extractor.close()
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close()