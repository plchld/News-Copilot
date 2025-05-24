#!/usr/bin/env python
"""
explain_with_grok.py
Simple CLI wrapper for News Copilot article analysis
"""

import sys
import json
from api.article_extractor import fetch_text
from api.grok_client import GrokClient
from api.analysis_handlers import AnalysisHandler
from api.config import FLASK_PORT, API_KEY
from prompts import (
    GROK_CONTEXT_JARGON_PROMPT_SCHEMA,
    GROK_ALTERNATIVE_VIEWPOINTS_PROMPT
)


def get_augmentations_sync(article_url: str) -> dict:
    """Synchronous version for CLI - get article augmentations"""
    print(f"[CLI] Starting analysis for URL: {article_url}", flush=True)
    
    if not API_KEY:
        raise ValueError("XAI_API_KEY not set.")
    
    # Fetch article text
    article_text = fetch_text(article_url)
    
    # Initialize Grok client
    grok_client = GrokClient()
    search_params = grok_client.get_default_search_params()
    
    results = {
        "jargon": None,
        "jargon_citations": [],
        "viewpoints": None,
        "viewpoints_citations": []
    }
    
    # Get jargon explanations
    try:
        from api.models import JargonResponse
        jargon_prompt = GROK_CONTEXT_JARGON_PROMPT_SCHEMA + "\n\nΆρθρο:\n" + article_text
        json_schema = JargonResponse.model_json_schema()
        
        jargon_completion = grok_client.create_completion(
            prompt=jargon_prompt,
            search_params=search_params,
            response_format={"type": "json_object", "schema": json_schema},
            stream=False
        )
        
        if jargon_completion.choices[0].message.content:
            results["jargon"] = json.loads(jargon_completion.choices[0].message.content)
        
        results["jargon_citations"] = grok_client.extract_citations(jargon_completion)
        
    except Exception as e:
        results["jargon_error"] = str(e)
        print(f"Jargon Error: {e}", flush=True)
    
    # Get alternative viewpoints
    try:
        viewpoints_prompt = GROK_ALTERNATIVE_VIEWPOINTS_PROMPT + "\n\nΠρωτότυπο Άρθρο για контекст:\n" + article_text
        
        viewpoints_completion = grok_client.create_completion(
            prompt=viewpoints_prompt,
            search_params=search_params,
            stream=False
        )
        
        results["viewpoints"] = viewpoints_completion.choices[0].message.content
        results["viewpoints_citations"] = grok_client.extract_citations(viewpoints_completion)
        
    except Exception as e:
        results["viewpoints_error"] = str(e)
        print(f"Viewpoints Error: {e}", flush=True)
    
    return results


def main_cli(url: str):
    """Main CLI function for article analysis"""
    print("--- CLI Mode (Synchronous) ---")
    try:
        results = get_augmentations_sync(url)
        
        if results.get("jargon_error"):
            print(f"Jargon Error: {results['jargon_error']}")
        if results.get("jargon"):
            print("\n--- ΕΠΕΞΗΓΗΣΕΙΣ ΟΡΩΝ (JSON) ---")
            print(json.dumps(results["jargon"], ensure_ascii=False, indent=2))
            if results["jargon_citations"]:
                print("\nΠηγές (Επεξηγήσεις Όρων):")
                for c in results["jargon_citations"]:
                    print(f"- {c}")
        
        if results.get("viewpoints_error"):
            print(f"Viewpoints Error: {results['viewpoints_error']}")
        if results.get("viewpoints"):
            print("\n--- ΕΝΑΛΛΑΚΤΙΚΕΣ ΟΠΤΙΚΕΣ ΓΩΝΙΕΣ ---")
            print(results["viewpoints"])
            if results["viewpoints_citations"]:
                print("\nΠηγές (Εναλλακτικές Οπτικές Γωνίες):")
                for c in results["viewpoints_citations"]:
                    print(f"- {c}")
    
    except Exception as e:
        print(f"Σφάλμα στο CLI mode: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Import and run the Flask app
        from api.app import app
        
        if not API_KEY:
            print("Σφάλμα: Η μεταβλητή περιβάλλοντος XAI_API_KEY δεν έχει οριστεί για τον server.", flush=True)
            sys.exit("Σφάλμα: Η μεταβλητή περιβάλλοντος XAI_API_KEY δεν έχει οριστεί για τον server.")
        
        print(f"Starting Flask server on http://127.0.0.1:{FLASK_PORT}...", flush=True)
        app.run(host='127.0.0.1', port=FLASK_PORT, debug=True)
        
    elif len(sys.argv) == 2:
        main_cli(sys.argv[1])
    else:
        print("Usage:")
        print("  For CLI: python explain_with_grok.py <URL_ΑΡΘΡΟΥ>")
        print("  For Server: python explain_with_grok.py --server")
        sys.exit(1)