"""
Local file export functionality for processed articles
"""
import os
import json
from datetime import datetime
from typing import Dict, Any
from processors.article_processor import ProcessedArticle


class LocalExporter:
    """Handles local file exports for processed articles"""
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"[LocalExporter] Created output directory: {self.output_dir}")
    
    def export_article(self, article: ProcessedArticle, format: str = "json") -> str:
        """
        Export article to local file
        
        Args:
            article: ProcessedArticle to export
            format: Export format ('json', 'txt', 'md')
            
        Returns:
            Path to exported file
        """
        # Generate safe filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50]  # Limit length
        
        if format == "json":
            filename = f"{timestamp}_{safe_title}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            article_dict = {
                'url': article.url,
                'title': article.title,
                'content': article.content,
                'source_domain': article.source_domain,
                'published_date': article.published_date,
                'extracted_date': article.extracted_date,
                'word_count': article.word_count,
                'metadata': article.metadata
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(article_dict, f, ensure_ascii=False, indent=2)
                
        elif format == "txt":
            filename = f"{timestamp}_{safe_title}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {article.title}\n")
                f.write(f"URL: {article.url}\n")
                f.write(f"Source: {article.source_domain}\n")
                f.write(f"Published: {article.published_date}\n")
                f.write(f"Extracted: {article.extracted_date}\n")
                f.write(f"Word Count: {article.word_count}\n")
                f.write("-" * 80 + "\n\n")
                f.write(article.content)
                
        elif format == "md":
            filename = f"{timestamp}_{safe_title}.md"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {article.title}\n\n")
                f.write(f"**URL:** {article.url}\n")
                f.write(f"**Source:** {article.source_domain}\n")
                f.write(f"**Published:** {article.published_date}\n")
                f.write(f"**Extracted:** {article.extracted_date}\n")
                f.write(f"**Word Count:** {article.word_count}\n\n")
                f.write("---\n\n")
                f.write(article.content)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        print(f"[LocalExporter] Exported article to: {filepath}")
        return filepath