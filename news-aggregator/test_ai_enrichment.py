#!/usr/bin/env python3
"""
Test AI enrichment of AMNA article
"""
import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.article_processor import ArticleProcessor
from processors.ai_enrichment import AIEnrichmentProcessor
from config.config import XAI_API_KEY

async def test_enrichment():
    """Test AI enrichment on AMNA article"""
    
    if not XAI_API_KEY:
        print("❌ Error: XAI_API_KEY not set in environment")
        return
    
    # The AMNA article URL
    amna_url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"
    
    print("=" * 80)
    print("AI ENRICHMENT TEST - AMNA ARTICLE")
    print("=" * 80)
    
    # Step 1: Extract article
    print("\n1. Extracting article...")
    article_processor = ArticleProcessor()
    
    try:
        article = article_processor.extract_article(amna_url)
        print(f"✓ Extracted: {article.title}")
        print(f"  Word count: {article.word_count}")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return
    finally:
        article_processor.close()
    
    # Step 2: Enrich with AI
    print("\n2. Enriching with AI analyses...")
    enrichment_processor = AIEnrichmentProcessor()
    
    # For testing, let's just run a subset of analyses
    test_analyses = ["jargon", "viewpoints", "bias"]
    
    try:
        enriched = await enrichment_processor.enrich_article_async(
            article, 
            analyses=test_analyses
        )
        
        print(f"\n✓ Enrichment completed!")
        print(f"  Duration: {enriched.enrichment_metadata['duration_seconds']:.1f}s")
        print(f"  Analyses completed: {enriched.enrichment_metadata['analyses_completed']}")
        
        # Step 3: Save enriched article
        print("\n3. Saving enriched article...")
        json_path = enrichment_processor.save_enriched_article(enriched, format="json")
        md_path = enrichment_processor.save_enriched_article(enriched, format="md")
        
        print(f"✓ Saved JSON: {json_path}")
        print(f"✓ Saved Markdown: {md_path}")
        
        # Step 4: Display sample results
        print("\n4. Sample enrichment results:")
        print("-" * 50)
        
        if enriched.jargon_terms and not enriched.jargon_terms.get("error"):
            print("\n📚 Jargon Terms:")
            print(json.dumps(enriched.jargon_terms, ensure_ascii=False, indent=2)[:500] + "...")
        
        if enriched.viewpoints and not enriched.viewpoints.get("error"):
            print("\n🔍 Alternative Viewpoints:")
            print(json.dumps(enriched.viewpoints, ensure_ascii=False, indent=2)[:500] + "...")
        
        if enriched.bias_analysis and not enriched.bias_analysis.get("error"):
            print("\n⚖️ Bias Analysis:")
            print(json.dumps(enriched.bias_analysis, ensure_ascii=False, indent=2)[:500] + "...")
        
        print("\n" + "=" * 80)
        print("✅ AI enrichment test completed successfully!")
        
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    # Create event loop and run async function
    asyncio.run(test_enrichment())

if __name__ == "__main__":
    main()