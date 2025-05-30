#!/usr/bin/env python3
"""
Production script to run daily news analysis
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.orchestration.parallel_category_orchestrator import ParallelCategoryOrchestrator as CategoryOrchestrator


async def run_daily_analysis(date: str = None, output_dir: str = None):
    """Run complete daily news analysis
    
    Args:
        date: Target date (default: today)
        output_dir: Output directory (default: outputs/YYYY-MM-DD/)
    """
    
    # Set date
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Set output directory
    if output_dir is None:
        output_dir = f"outputs/{date}"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🚀 Starting Daily News Analysis for {date}")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        orchestrator = CategoryOrchestrator()
        
        # Run analysis
        results = await orchestrator.run_daily_analysis(date)
        
        # Save results
        output_file = os.path.join(output_dir, "analysis_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Analysis complete!")
        print(f"📁 Results saved to: {output_file}")
        
        # Save individual story files
        story_dir = os.path.join(output_dir, "stories")
        os.makedirs(story_dir, exist_ok=True)
        
        for story_id, story_data in results["results"].items():
            if "synthesis" in story_data:
                story_file = os.path.join(story_dir, f"{story_id}.md")
                with open(story_file, 'w', encoding='utf-8') as f:
                    f.write(story_data["synthesis"])
        
        print(f"📰 Individual stories saved to: {story_dir}")
        
        # Print summary
        print("\n📊 Summary:")
        print(f"  • Total stories analyzed: {results['total_stories']}")
        print(f"  • Categories: 6")
        print(f"  • Output language: Greek")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


def main():
    """Main entry point"""
    
    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("Export your API key: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not set")
        print("Export your API key: export GEMINI_API_KEY='your-key'")
        sys.exit(1)
    
    # Parse command line arguments
    date = sys.argv[1] if len(sys.argv) > 1 else None
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Run analysis
    asyncio.run(run_daily_analysis(date, output_dir))


if __name__ == "__main__":
    main()