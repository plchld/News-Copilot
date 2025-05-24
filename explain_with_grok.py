#!/usr/bin/env python
"""
explain_with_grok.py
— fetch article, ask Grok for jargon explanations + offsets & alternative viewpoints
  • Uses Live Search (built-in)
  • Forces JSON schema for jargon, plain text for viewpoints
  • Aims for Greek output and citations
  • Now with a Flask server for browser extension MVP
"""

import os, sys, re, json, trafilatura, time
from typing import List, Any, Dict, Generator
from pydantic import BaseModel
from openai import OpenAI, APIStatusError
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import urllib.error

# Import Grok-specific prompts
from prompts import (
    GROK_CONTEXT_JARGON_PROMPT_SCHEMA, 
    GROK_ALTERNATIVE_VIEWPOINTS_PROMPT,
    GROK_FACT_CHECK_PROMPT,
    GROK_BIAS_ANALYSIS_PROMPT,
    GROK_TIMELINE_PROMPT,
    GROK_EXPERT_OPINIONS_PROMPT
)

load_dotenv()

# ── config ───────────────────────────────────────────────────────────────
MODEL      = "grok-3" 
API_URL    = "https://api.x.ai/v1"
API_KEY    = os.getenv("XAI_API_KEY")
FLASK_PORT = 8080

# Standard User-Agent
COMMON_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# ── pydantic schema for structured output ───────────────────────────────
class TermExplanation(BaseModel):
    term: str
    explanation: str

class JargonResponse(BaseModel):
    terms: List[TermExplanation]

JSON_SCHEMA: Dict[str, Any] = JargonResponse.model_json_schema()

# ── helpers ──────────────────────────────────────────────────────────────
def fetch_text(url: str) -> str:
    print(f"[fetch_text] Attempting to fetch URL: {url}", flush=True)
    try:
        downloaded = trafilatura.fetch_url(url)
    except urllib.error.HTTPError as e:
        error_message = f"HTTPError when fetching URL {url}: {e.code} {e.reason}"
        print(f"[fetch_text] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)
    except Exception as e:
        error_message = f"Generic error when fetching URL {url} with trafilatura: {type(e).__name__} - {e}"
        print(f"[fetch_text] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)

    if not downloaded:
        error_message = f"Could not download content from {url} (trafilatura.fetch_url returned None even without User-Agent)"
        print(f"[fetch_text] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)
    
    print(f"[fetch_text] Successfully downloaded content from {url}", flush=True)
    text = trafilatura.extract(downloaded) or ""
    if not text:
        print(f"[fetch_text] Trafilatura failed to extract main text from {url}", flush=True)
        raise RuntimeError(f"Trafilatura failed to extract main text from {url}")
    
    print(f"[fetch_text] Successfully extracted text from {url}", flush=True)
    return re.sub(r"\s+\n", "\n", text).strip()

# Adapted to be a generator yielding status updates and final data
def get_augmentations_stream(article_url: str) -> Generator[str, None, None]:
    def stream_event(event_type: str, data: Any):
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    print(f"[get_augmentations_stream] Starting for URL: {article_url}", flush=True)
    yield stream_event("progress", {"status": "Initializing augmentation..."})

    if not API_KEY:
        print("[get_augmentations_stream] ERROR: XAI_API_KEY not set", flush=True)
        yield stream_event("error", {"message": "Server configuration error: XAI_API_KEY not set."})
        return

    article_text = None
    try:
        print("[get_augmentations_stream] Calling fetch_text...", flush=True)
        yield stream_event("progress", {"status": "Fetching article content..."})
        article_text = fetch_text(article_url)
        print(f"[get_augmentations_stream] fetch_text returned article_text (length: {len(article_text)})", flush=True)
        yield stream_event("progress", {"status": f"Article content fetched ({len(article_text)} chars)."})
    except RuntimeError as e:
        print(f"[get_augmentations_stream] ERROR from fetch_text: {e}", flush=True)
        yield stream_event("error", {"message": str(e)})
        return
    except Exception as e: # Catch any other unexpected error during fetch
        print(f"[get_augmentations_stream] UNEXPECTED ERROR during fetch_text: {type(e).__name__} - {e}", flush=True)
        yield stream_event("error", {"message": f"Unexpected error fetching article: {type(e).__name__}"})
        return

    client = OpenAI(api_key=API_KEY, base_url=API_URL)
    search_params_dict = {
        "mode": "on", "return_citations": True, "sources": [{"type": "web"}, {"type": "news"}]
    }
    final_results = {"jargon": None, "jargon_citations": [], "viewpoints": None, "viewpoints_citations": []}

    # Jargon Call
    try:
        print("[get_augmentations_stream] Preparing for Grok jargon call...", flush=True)
        yield stream_event("progress", {"status": "Explaining key terms..."})
        # time.sleep(2) # Simulate delay for testing UI
        jargon_prompt_content = GROK_CONTEXT_JARGON_PROMPT_SCHEMA + "\n\nΆρθρο:\n" + article_text
        jargon_completion = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": jargon_prompt_content}],
            extra_body={"search_parameters": search_params_dict},
            response_format={"type": "json_object", "schema": JSON_SCHEMA}, stream=False
        )
        print("[get_augmentations_stream] Grok jargon call successful.", flush=True)
        jargon_data_str = jargon_completion.choices[0].message.content
        if jargon_data_str: final_results["jargon"] = json.loads(jargon_data_str)
        if hasattr(jargon_completion, 'citations') and jargon_completion.citations:
            final_results["jargon_citations"] = [str(c) for c in jargon_completion.citations]
        elif hasattr(jargon_completion.choices[0], 'citations') and jargon_completion.choices[0].citations:
            final_results["jargon_citations"] = [str(c) for c in jargon_completion.choices[0].citations]
        yield stream_event("progress", {"status": "Key terms explained."})
    except APIStatusError as e:
        error_message = f"Grok API error (jargon): Status {e.status_code}, Response: {e.response.text if e.response else 'N/A'}"
        print(f"[get_augmentations_stream] API ERROR (jargon): {error_message}", flush=True)
        yield stream_event("error", {"message": "API error while explaining terms."})
        # Optionally send final_results even if one part fails, or just return
        # For now, we'll send what we have and then the error, then stop.
        # yield stream_event("final_result", final_results)
        return
    except Exception as e:
        error_message = f"Generic error during Grok jargon call: {type(e).__name__} - {e}"
        print(f"[get_augmentations_stream] ERROR (jargon): {error_message}", flush=True)
        yield stream_event("error", {"message": "Error explaining terms."})
        return

    # Viewpoints Call
    try:
        print("[get_augmentations_stream] Preparing for Grok viewpoints call...", flush=True)
        yield stream_event("progress", {"status": "Finding alternative viewpoints..."})
        # time.sleep(2) # Simulate delay
        viewpoints_prompt_content = GROK_ALTERNATIVE_VIEWPOINTS_PROMPT + "\n\nΠρωτότυπο Άρθρο για контекст:\n" + article_text
        viewpoints_completion = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": viewpoints_prompt_content}],
            extra_body={"search_parameters": search_params_dict}, stream=False
        )
        print("[get_augmentations_stream] Grok viewpoints call successful.", flush=True)
        final_results["viewpoints"] = viewpoints_completion.choices[0].message.content
        if hasattr(viewpoints_completion, 'citations') and viewpoints_completion.citations:
            final_results["viewpoints_citations"] = [str(c) for c in viewpoints_completion.citations]
        elif hasattr(viewpoints_completion.choices[0], 'citations') and viewpoints_completion.choices[0].citations:
            final_results["viewpoints_citations"] = [str(c) for c in viewpoints_completion.choices[0].citations]
        yield stream_event("progress", {"status": "Alternative viewpoints found."})
    except APIStatusError as e:
        error_message = f"Grok API error (viewpoints): Status {e.status_code}, Response: {e.response.text if e.response else 'N/A'}"
        print(f"[get_augmentations_stream] API ERROR (viewpoints): {error_message}", flush=True)
        yield stream_event("error", {"message": "API error finding viewpoints."})
        # Send what we have so far if jargon succeeded, then error, then stop.
        # yield stream_event("final_result", final_results) 
        return 
    except Exception as e:
        error_message = f"Generic error during Grok viewpoints call: {type(e).__name__} - {e}"
        print(f"[get_augmentations_stream] ERROR (viewpoints): {error_message}", flush=True)
        yield stream_event("error", {"message": "Error finding viewpoints."})
        return
    
    print(f"[get_augmentations_stream] All tasks complete. Sending final results.", flush=True)
    yield stream_event("final_result", final_results)
    yield stream_event("progress", {"status": "Done!"}) # Final status update

app = Flask(__name__, static_folder='static') # Ensure Flask app is initialized with static folder
CORS(app)             # Enable CORS

# Import and register auth blueprints
try:
    from api.http_supabase import http_supabase_bp, require_http_supabase_auth as require_auth
    app.register_blueprint(http_supabase_bp)
    AUTH_ENABLED = True
    print("✅ HTTP Supabase authentication enabled")
except ImportError as e:
    print(f"⚠️ Supabase auth not available: {e}")
    print("Running without authentication")
    AUTH_ENABLED = False
    # Mock decorator for local development
    def require_auth(analysis_type='basic_analysis'):
        def decorator(f):
            return f
        return decorator

@app.route('/', methods=['GET'])
def home():
    """Health check and API info endpoint, or serve auth callback page"""
    # Check if this is an API request or browser request
    accept_header = request.headers.get('Accept', '')
    
    # If it's a browser request (accepts HTML) and has auth tokens in hash, serve the static page
    if 'text/html' in accept_header:
        # Serve the static index.html for browser requests
        return app.send_static_file('index.html')
    
    # Otherwise, return API info
    return jsonify({
        "service": "News Copilot API",
        "status": "running",
        "version": "1.0.0",
        "auth_enabled": AUTH_ENABLED,
        "endpoints": {
            "/": "This health check",
            "/augment-stream": "GET - Stream article analysis with jargon and viewpoints",
            "/deep-analysis": "POST - Deep analysis (fact-check, bias, timeline, expert opinions)",
            "/api/auth/*": "Authentication endpoints",
            "/api/admin/*": "Admin endpoints"
        },
        "usage": {
            "augment-stream": "GET /?url=<article_url>",
            "deep-analysis": "POST with JSON body: {url, analysisType, searchParams}"
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check for monitoring"""
    return jsonify({"status": "ok"})

# Serve static verification pages
@app.route('/verification-success.html')
def verification_success():
    """Serve email verification success page"""
    return app.send_static_file('verification-success.html')

@app.route('/verification-failed.html')
def verification_failed():
    """Serve email verification failed page"""
    return app.send_static_file('verification-failed.html')

@app.route('/verification-expired.html')
def verification_expired():
    """Serve email verification expired page"""
    return app.send_static_file('verification-failed.html')  # Use same page for now

@app.route('/augment-stream', methods=['GET'])
@require_auth('basic_analysis')
def augment_article_stream_route():
    print("\n[Flask /augment-stream] Received stream request!", flush=True)
    article_url = request.args.get('url')
    print(f"[Flask /augment-stream] URL from request: {article_url}", flush=True)

    if not article_url:
        print("[Flask /augment-stream] ERROR: Missing 'url' parameter", flush=True)
        def error_stream():
            yield f"event: error\ndata: {json.dumps({'message': 'Missing URL parameter'})}\n\n"
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')

    return Response(stream_with_context(get_augmentations_stream(article_url)), mimetype='text/event-stream')

@app.route('/deep-analysis', methods=['POST'])
@require_auth('deep_analysis')
def deep_analysis_route():
    """Handle deep analysis requests for fact-checking, bias analysis, timeline, and expert opinions."""
    print("\n[Flask /deep-analysis] Received deep analysis request!", flush=True)
    
    try:
        data = request.get_json()
        article_url = data.get('url')
        analysis_type = data.get('analysis_type')
        search_params = data.get('search_params', {})
        
        print(f"[Flask /deep-analysis] URL: {article_url}, Type: {analysis_type}", flush=True)
        
        if not article_url or not analysis_type:
            return jsonify({'success': False, 'error': 'Missing URL or analysis_type parameter'}), 400
        
        # Get analysis result
        result = get_deep_analysis(article_url, analysis_type, search_params)
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"[Flask /deep-analysis] ERROR: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# ── Deep Analysis Function ──────────────────────────────────────────────

def get_deep_analysis(article_url: str, analysis_type: str, search_params: Dict[str, Any]) -> Dict[str, Any]:
    """Perform deep analysis using Grok API with specific prompts for each analysis type."""
    print(f"[get_deep_analysis] Starting {analysis_type} analysis for URL: {article_url}", flush=True)
    
    if not API_KEY:
        raise ValueError("XAI_API_KEY not set.")
    
    # Fetch article content
    article_text = fetch_text(article_url)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=API_KEY, base_url=API_URL)
    
    # Configure search parameters with sources based on analysis type
    default_search_params = {
        "mode": "on", 
        "return_citations": True, 
        "sources": [{"type": "web"}, {"type": "news"}]
    }
    
    # Override with provided search params
    search_params_dict = {**default_search_params, **search_params}
    
    # Select appropriate prompt based on analysis type
    prompt_map = {
        'fact-check': GROK_FACT_CHECK_PROMPT,
        'bias': GROK_BIAS_ANALYSIS_PROMPT,
        'timeline': GROK_TIMELINE_PROMPT,
        'expert': GROK_EXPERT_OPINIONS_PROMPT
    }
    
    if analysis_type not in prompt_map:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    prompt = prompt_map[analysis_type]
    prompt_content = prompt + "\n\nΆρθρο προς ανάλυση:\n" + article_text
    
    # Define JSON schemas for structured responses
    fact_check_schema = {
        "type": "object",
        "properties": {
            "overall_credibility": {"type": "string"},
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "statement": {"type": "string"},
                        "verified": {"type": "boolean"},
                        "explanation": {"type": "string"},
                        "sources": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "red_flags": {"type": "array", "items": {"type": "string"}},
            "missing_context": {"type": "string"}
        }
    }
    
    bias_schema = {
        "type": "object",
        "properties": {
            "political_lean": {"type": "string"},
            "confidence": {"type": "string"},
            "emotional_tone": {"type": "string"},
            "language_analysis": {
                "type": "object",
                "properties": {
                    "loaded_words": {"type": "array", "items": {"type": "string"}},
                    "framing": {"type": "string"},
                    "missing_perspectives": {"type": "string"}
                }
            },
            "comparison": {"type": "string"},
            "recommendations": {"type": "string"}
        }
    }
    
    timeline_schema = {
        "type": "object",
        "properties": {
            "story_title": {"type": "string"},
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "importance": {"type": "string"},
                        "source": {"type": "string"}
                    }
                }
            },
            "context": {"type": "string"},
            "future_implications": {"type": "string"}
        }
    }
    
    expert_schema = {
        "type": "object",
        "properties": {
            "topic_summary": {"type": "string"},
            "experts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "credentials": {"type": "string"},
                        "opinion": {"type": "string"},
                        "quote": {"type": "string"},
                        "source": {"type": "string"},
                        "source_url": {"type": "string"},
                        "stance": {"type": "string"}
                    }
                }
            },
            "consensus": {"type": "string"},
            "key_debates": {"type": "string"}
        }
    }
    
    schema_map = {
        'fact-check': fact_check_schema,
        'bias': bias_schema,
        'timeline': timeline_schema,
        'expert': expert_schema
    }
    
    try:
        print(f"[get_deep_analysis] Making Grok API call for {analysis_type}...", flush=True)
        
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt_content}],
            extra_body={"search_parameters": search_params_dict},
            response_format={"type": "json_object", "schema": schema_map[analysis_type]},
            stream=False
        )
        
        print(f"[get_deep_analysis] Grok {analysis_type} call successful.", flush=True)
        
        # Parse response
        response_data = json.loads(completion.choices[0].message.content)
        
        # Extract citations
        citations = []
        if hasattr(completion, 'citations') and completion.citations:
            citations = [str(c) for c in completion.citations]
        elif hasattr(completion.choices[0], 'citations') and completion.choices[0].citations:
            citations = [str(c) for c in completion.choices[0].citations]
        
        return {
            'analysis': response_data,
            'citations': citations,
            'analysis_type': analysis_type
        }
        
    except APIStatusError as e:
        error_message = f"Grok API error ({analysis_type}): Status {e.status_code}, Response: {e.response.text if e.response else 'N/A'}"
        print(f"[get_deep_analysis] API ERROR: {error_message}", flush=True)
        raise RuntimeError(f"API error during {analysis_type} analysis: {e.status_code}")
    except Exception as e:
        error_message = f"Error during {analysis_type} analysis: {type(e).__name__} - {e}"
        print(f"[get_deep_analysis] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)

# ── main (for CLI, kept for compatibility) ───────────────────────────────
# CLI mode will NOT use streaming. It will call a synchronous version or a wrapper.
# For now, let's make main_cli call the original logic if we need to keep it simple,
# or adapt it to consume the generator internally if needed for consistency.
# To keep this change focused on SSE for the extension, I'll simplify main_cli to use a direct (non-streaming) approach.

def get_augmentations_sync(article_url: str) -> Dict[str, Any]: # Synchronous version for CLI
    print(f"[get_augmentations_sync] Starting for URL: {article_url}", flush=True)
    if not API_KEY: raise ValueError("XAI_API_KEY not set.")
    article_text = fetch_text(article_url)
    
    client = OpenAI(api_key=API_KEY, base_url=API_URL)
    search_params_dict = {"mode": "on", "return_citations": True, "sources": [{"type": "web"}, {"type": "news"}]}
    results = {"jargon": None, "jargon_citations": [], "viewpoints": None, "viewpoints_citations": []}

    try: # Jargon
        jargon_prompt_content = GROK_CONTEXT_JARGON_PROMPT_SCHEMA + "\n\nΆρθρο:\n" + article_text
        jargon_completion = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": jargon_prompt_content}], extra_body={"search_parameters": search_params_dict}, response_format={"type": "json_object", "schema": JSON_SCHEMA}, stream=False)
        if jargon_completion.choices[0].message.content: results["jargon"] = json.loads(jargon_completion.choices[0].message.content)
        if hasattr(jargon_completion, 'citations') and jargon_completion.citations: results["jargon_citations"] = [str(c) for c in jargon_completion.citations]
        elif hasattr(jargon_completion.choices[0], 'citations') and jargon_completion.choices[0].citations: results["jargon_citations"] = [str(c) for c in jargon_completion.choices[0].citations]
    except Exception as e: results["jargon_error"] = str(e); print(f"Jargon Error (sync): {e}", flush=True)

    try: # Viewpoints
        viewpoints_prompt_content = GROK_ALTERNATIVE_VIEWPOINTS_PROMPT + "\n\nΠρωτότυπο Άρθρο για контекст:\n" + article_text
        viewpoints_completion = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": viewpoints_prompt_content}], extra_body={"search_parameters": search_params_dict}, stream=False)
        results["viewpoints"] = viewpoints_completion.choices[0].message.content
        if hasattr(viewpoints_completion, 'citations') and viewpoints_completion.citations: results["viewpoints_citations"] = [str(c) for c in viewpoints_completion.citations]
        elif hasattr(viewpoints_completion.choices[0], 'citations') and viewpoints_completion.choices[0].citations: results["viewpoints_citations"] = [str(c) for c in viewpoints_completion.choices[0].citations]
    except Exception as e: results["viewpoints_error"] = str(e); print(f"Viewpoints Error (sync): {e}", flush=True)
    return results

def main_cli(url: str):
    print("--- CLI Mode (Synchronous) ---")
    try:
        results = get_augmentations_sync(url) # Call the synchronous version
        if results.get("jargon_error"):
            print(f"Jargon Error: {results['jargon_error']}")
        if results.get("jargon"):
             print("\n--- ΕΠΕΞΗΓΗΣΕΙΣ ΟΡΩΝ (JSON) ---")
             print(json.dumps(results["jargon"], ensure_ascii=False, indent=2))
             if results["jargon_citations"]:
                 print("\nΠηγές (Επεξηγήσεις Όρων):")
                 for c in results["jargon_citations"]: print(f"- {c}")
        
        if results.get("viewpoints_error"):
            print(f"Viewpoints Error: {results['viewpoints_error']}")
        if results.get("viewpoints"):
            print("\n--- ΕΝΑΛΛΑΚΤΙΚΕΣ ΟΠΤΙΚΕΣ ΓΩΝΙΕΣ ---")
            print(results["viewpoints"])
            if results["viewpoints_citations"]:
                print("\nΠηγές (Εναλλακτικές Οπτικές Γωνίες):")
                for c in results["viewpoints_citations"]: print(f"- {c}")

    except Exception as e:
        print(f"Σφάλμα στο CLI mode: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        if not API_KEY:
            print("Σφάλμα: Η μεταβλητή περιβάλλοντος XAI_API_KEY δεν έχει οριστεί για τον server.", flush=True)
            sys.exit("Σφάλμα: Η μεταβλητή περιβάλλοντος XAI_API_KEY δεν έχει οριστεί για τον server.")
        print(f"Starting Flask server on http://127.0.0.1:{FLASK_PORT}...", flush=True)
        # Note: Flask's development server with stream_with_context might have issues with auto-reloader sometimes.
        # For production, a proper WSGI server (Gunicorn, uWSGI) would be used.
        app.run(host='127.0.0.1', port=FLASK_PORT, debug=True) # use_reloader=False can sometimes help with streaming issues in dev
    elif len(sys.argv) == 2:
        main_cli(sys.argv[1])
    else:
        print("Usage:")
        print("  For CLI: python explain_with_grok.py <URL_ΑΡΘΡΟΥ>")
        print("  For Server: python explain_with_grok.py --server")
        sys.exit(1) 