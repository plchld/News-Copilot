#!/usr/bin/env python3
"""
Test simple AI enrichment
"""
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.article_processor import ArticleProcessor
from processors.simple_ai_enrichment import SimpleAIEnrichment
from config.config import XAI_API_KEY

def main():
    """Test simple AI enrichment"""
    
    if not XAI_API_KEY:
        print("❌ Error: XAI_API_KEY not set")
        print("Please create a .env file with your XAI_API_KEY")
        return
    
    # The AMNA article URL
    amna_url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"
    
    print("=" * 80)
    print("SIMPLE AI ENRICHMENT TEST")
    print("=" * 80)
    
    # Step 1: Extract article
    print("\n1. Extracting article...")
    processor = ArticleProcessor()
    
    try:
        article = processor.extract_article(amna_url)
        print(f"✓ Extracted: {article.title}")
        print(f"  Words: {article.word_count}")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return
    finally:
        processor.close()
    
    # Step 2: Enrich with AI
    print("\n2. Enriching with AI...")
    enricher = SimpleAIEnrichment()
    
    try:
        enriched = enricher.enrich_article(article)
        
        # Step 3: Save results
        filepath = enricher.save_enriched_article(enriched)
        
        # Step 4: Display results
        print("\n3. Enrichment Results:")
        print("-" * 50)
        
        if "jargon" in enriched.enrichments and not enriched.enrichments["jargon"].get("error"):
            print("\n📚 Jargon Terms:")
            print(json.dumps(enriched.enrichments["jargon"], ensure_ascii=False, indent=2)[:300] + "...")
        
        if "bias" in enriched.enrichments and not enriched.enrichments["bias"].get("error"):
            print("\n⚖️ Bias Analysis:")
            print(enriched.enrichments["bias"]["analysis"][:300] + "...")
        
        if "summary" in enriched.enrichments and not enriched.enrichments["summary"].get("error"):
            print("\n📝 Summary:")
            print(enriched.enrichments["summary"]["summary"])
        
        print("\n" + "=" * 80)
        print(f"✅ Enrichment completed successfully!")
        print(f"📁 Results saved to: {filepath}")
        
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()