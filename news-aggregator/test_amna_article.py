#!/usr/bin/env python3
"""
Test script to process the AMNA article
"""
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.article_processor import ArticleProcessor
from exporters.local_exporter import LocalExporter

def main():
    """Test processing the AMNA article"""
    
    # The AMNA article URL provided
    amna_url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"
    
    print("=" * 80)
    print("NEWS AGGREGATOR - AMNA ARTICLE TEST")
    print("=" * 80)
    print(f"Processing URL: {amna_url}")
    print()
    
    # Initialize processor and exporter
    processor = ArticleProcessor()
    exporter = LocalExporter()
    
    try:
        # Process the article
        print("1. Extracting article content...")
        article = processor.extract_article(amna_url)
        
        print(f"✓ Successfully extracted article:")
        print(f"  Title: {article.title}")
        print(f"  Source: {article.source_domain}")
        print(f"  Word Count: {article.word_count}")
        print(f"  Published: {article.published_date}")
        print()
        
        # Export in multiple formats
        print("2. Exporting to local files...")
        
        json_path = exporter.export_article(article, format="json")
        print(f"✓ JSON export: {json_path}")
        
        txt_path = exporter.export_article(article, format="txt")
        print(f"✓ TXT export: {txt_path}")
        
        md_path = exporter.export_article(article, format="md")
        print(f"✓ Markdown export: {md_path}")
        
        print()
        print("3. Content preview:")
        print("-" * 50)
        preview = article.content[:500] + "..." if len(article.content) > 500 else article.content
        print(preview)
        print("-" * 50)
        
        print()
        print("✅ AMNA article processing completed successfully!")
        print(f"📁 Files exported to: {exporter.output_dir}")
        
    except Exception as e:
        print(f"❌ Error processing article: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()