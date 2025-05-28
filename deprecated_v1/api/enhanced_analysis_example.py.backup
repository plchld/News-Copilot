# api/enhanced_analysis_example.py
"""
Example of how to integrate thinking models with search params and hardened prompts.
This shows the complete flow from article analysis to validated results.
"""

import asyncio
import json
from typing import Dict, Any

from .thinking_utils import ThinkingAnalyzer, build_adaptive_search_params
from .search_params_builder import build_search_params
from .prompt_utils import (
    build_prompt,
    get_jargon_task_instruction,
    get_jargon_response_schema,
    inject_runtime_search_context
)


async def analyze_article_with_thinking(grok_client, article_text: str, analysis_type: str):
    """
    Complete analysis flow using thinking models for intelligent decision-making.
    
    Args:
        grok_client: The Grok API client
        article_text: The article to analyze
        analysis_type: Type of analysis (jargon, viewpoints, fact_check, etc.)
    
    Returns:
        Dict with analysis results and metadata
    """
    analyzer = ThinkingAnalyzer(grok_client)
    
    # Step 1: Analyze article context using thinking model
    print("🤔 Analyzing article context...")
    article_analysis = await analyzer.analyze_article_context(article_text)
    
    print(f"Article scope: {article_analysis['story_scope']}")
    print(f"Main topic: {article_analysis['main_topic']}")
    print(f"Search in English too: {article_analysis['search_english']}")
    
    # Step 2: Determine optimal search strategy for this analysis type
    print(f"\n🎯 Determining search strategy for {analysis_type}...")
    search_strategy = await analyzer.determine_search_strategy(article_text, analysis_type)
    
    print(f"Sources to use: {search_strategy['sources']}")
    print(f"Max results: {search_strategy['max_results']}")
    
    # Step 3: Build adaptive search parameters
    search_params = build_adaptive_search_params(article_analysis, search_strategy)
    
    print(f"\n🔍 Search parameters:")
    print(json.dumps(search_params, ensure_ascii=False, indent=2))
    
    # Step 4: Get the appropriate prompt and schema
    if analysis_type == "jargon":
        task_instruction = get_jargon_task_instruction(article_text)
        schema = get_jargon_response_schema()
    # Add other analysis types here...
    
    # Step 5: Build the complete prompt with hardened template
    base_prompt = build_prompt(task_instruction, schema)
    
    # Step 6: Inject search context into prompt
    final_prompt = inject_runtime_search_context(base_prompt, search_params)
    
    # Step 7: Call Grok with the main model (not thinking model)
    print(f"\n🚀 Calling Grok for {analysis_type} analysis...")
    response = await grok_client.create_completion(
        model="grok-3",  # Use full model for domain knowledge
        prompt=final_prompt,
        extra_body={"search_parameters": search_params},
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    result_json = response.choices[0].message.content
    
    # Step 8: Validate response quality using thinking model
    print("\n✅ Validating response quality...")
    is_valid, issues = await analyzer.validate_response_quality(
        result_json, 
        schema,
        analysis_type
    )
    
    if not is_valid:
        print(f"⚠️  Quality issues found: {issues}")
        # Could retry or handle errors here
    else:
        print("✅ Response validated successfully!")
    
    # Step 9: Return complete results with metadata
    return {
        "analysis": json.loads(result_json),
        "metadata": {
            "article_scope": article_analysis['story_scope'],
            "main_topic": article_analysis['main_topic'],
            "search_params": search_params,
            "sources_used": search_strategy['sources'],
            "validation_status": "valid" if is_valid else "invalid",
            "validation_issues": issues if not is_valid else []
        }
    }


async def smart_multi_analysis(grok_client, article_text: str):
    """
    Perform multiple analyses with intelligent parameter selection.
    Uses thinking model to assess complexity once and apply to all analyses.
    """
    analyzer = ThinkingAnalyzer(grok_client)
    
    # Assess complexity once for all analyses
    complexity = await analyzer.assess_complexity(article_text)
    print(f"📊 Article complexity: {complexity}")
    
    # Get article context once
    article_analysis = await analyzer.analyze_article_context(article_text)
    
    # Perform different analyses with adapted parameters
    analyses = ["jargon", "viewpoints", "fact_check"]
    results = {}
    
    for analysis_type in analyses:
        # Get search strategy specific to this analysis
        search_strategy = await analyzer.determine_search_strategy(
            article_text, 
            analysis_type
        )
        
        # Adjust based on complexity
        if complexity == "high":
            search_strategy["max_results"] = min(search_strategy["max_results"] * 2, 50)
        
        # Build parameters and perform analysis
        search_params = build_adaptive_search_params(
            article_analysis,
            search_strategy
        )
        
        # Add language consideration for international stories
        if article_analysis["story_scope"] == "international":
            # For international stories, also search in English
            search_params = build_search_params(
                **{k: v for k, v in search_params.items() if k != "sources"},
                sources=search_params["sources"],
                include_english=True
            )
        
        # Perform the analysis (simplified for example)
        results[analysis_type] = {
            "search_params": search_params,
            "complexity": complexity
        }
    
    return results


# Example usage
if __name__ == "__main__":
    # This would be run in an async context
    article = """
    Ο πρωθυπουργός Κυριάκος Μητσοτάκης συναντήθηκε σήμερα με τον πρόεδρο 
    της Ευρωπαϊκής Επιτροπής για να συζητήσουν το νέο πακέτο οικονομικής 
    στήριξης της ΕΕ προς την Ουκρανία...
    """
    
    # Example of how to use the enhanced analysis
    # results = await analyze_article_with_thinking(grok_client, article, "jargon")