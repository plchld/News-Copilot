#!/usr/bin/env python3
"""
Test the comprehensive news aggregator system
"""
import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.enhanced_article_processor import EnhancedArticleProcessor
from config.config import XAI_API_KEY

async def test_comprehensive_system():
    """Test the comprehensive system"""
    
    if not XAI_API_KEY:
        print("❌ Error: XAI_API_KEY not set")
        return
    
    # The AMNA article URL
    amna_url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"
    
    print("=" * 80)
    print("COMPREHENSIVE NEWS AGGREGATOR SYSTEM TEST")
    print("=" * 80)
    
    # Initialize enhanced processor with comprehensive enrichment
    processor = EnhancedArticleProcessor(use_comprehensive=True)
    
    try:
        # Test 1: Process article with comprehensive enrichment
        print("\n1. Processing article with comprehensive enrichment...")
        result = processor.process_article_url(amna_url, enrich=True)
        
        if result['status'] == 'success':
            print(f"✓ Article processed successfully!")
            print(f"  Article ID: {result['article_id']}")
            print(f"  Title: {result['title']}")
            print(f"  Enrichment Type: {result.get('enrichment_type', 'N/A')}")
            print(f"  Duration: {result.get('enrichment_duration', 0):.1f}s")
            
            if result.get('analyses_completed'):
                print(f"  Successful analyses: {result['analyses_completed']}")
            if result.get('analyses_failed'):
                print(f"  Failed analyses: {result['analyses_failed']}")
                
            article_id = result['article_id']
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return
        
        # Test 2: Retrieve stored article
        print(f"\n2. Retrieving stored article...")
        stored_article = processor.get_article(article_id)
        
        if stored_article:
            print(f"✓ Article retrieved successfully!")
            print(f"  Index info: {stored_article.get('index_info', {}).get('title', 'N/A')[:50]}...")
            
            if 'enriched' in stored_article:
                enriched_data = stored_article['enriched']
                print(f"  Enrichment version: {enriched_data.get('version', 'N/A')}")
                print(f"  Available enrichments: {list(enriched_data.get('enrichments', {}).keys())}")
        else:
            print(f"❌ Failed to retrieve article")
        
        # Test 3: List articles
        print(f"\n3. Listing stored articles...")
        articles_list = processor.list_articles(limit=5)
        
        print(f"✓ Found {articles_list['total_found']} articles")
        print(f"  Storage stats: {articles_list['stats']}")
        
        for i, article in enumerate(articles_list['articles'][:3], 1):
            print(f"  {i}. {article['title'][:60]}... (Enriched: {article['enriched']})")
        
        # Test 4: Get available analyses
        if hasattr(processor, 'comprehensive_enricher') and processor.comprehensive_enricher:
            print(f"\n4. Available analyses:")
            available = processor.comprehensive_enricher.get_available_analyses()
            print(f"✓ Available: {available}")
            
            analysis_info = processor.comprehensive_enricher.get_analysis_info()
            for name, info in analysis_info.items():
                print(f"  - {name}: {info.get('description', 'No description')[:60]}...")
        
        print("\n" + "=" * 80)
        print("✅ COMPREHENSIVE SYSTEM TEST COMPLETED SUCCESSFULLY!")
        print("📁 Check data/processed/ and data/enriched/ for saved articles")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close()

def main():
    """Main function"""
    asyncio.run(test_comprehensive_system())

if __name__ == "__main__":
    main()