"""
Web app routes without authentication requirements
These routes use the server's API key instead of user authentication
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
from .analysis_handlers import AnalysisHandler
from .config import API_KEY, AUTH_ENABLED
import json

web_bp = Blueprint('web', __name__)

# Create analysis handler with server's API key
analysis_handler = AnalysisHandler()


@web_bp.route('/web/augment-stream', methods=['GET'])
def web_augment_stream():
    """Web version of augment-stream that uses server's API key"""
    article_url = request.args.get('url')
    
    if not article_url:
        def error_stream():
            yield f"event: error\ndata: {json.dumps({'message': 'Missing URL parameter'})}\n\n"
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')
    
    # Stream the analysis using server's API key
    def generate():
        try:
            import asyncio
            
            # Handle async generator properly
            async def collect_chunks():
                chunks = []
                async for chunk in analysis_handler.get_augmentations_stream(article_url):
                    chunks.append(chunk)
                return chunks
            
            # Run async generator and yield chunks
            chunks = asyncio.run(collect_chunks())
            for chunk in chunks:
                yield chunk
                
        except GeneratorExit:
            # Client disconnected
            pass
        except Exception as e:
            print(f"[Web augment-stream] Error during streaming: {e}", flush=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
            'Connection': 'keep-alive'
        }
    )


@web_bp.route('/web/deep-analysis', methods=['POST', 'OPTIONS'])
def web_deep_analysis():
    """Web version of deep-analysis that uses server's API key"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON in request body'}), 400
            
        article_url = data.get('url')
        analysis_type = data.get('analysis_type')
        search_params = data.get('search_params', {})
        
        print(f"[Web /deep-analysis] Request: url={article_url}, type={analysis_type}", flush=True)
        
        if not article_url or not analysis_type:
            return jsonify({'success': False, 'error': 'Missing URL or analysis_type parameter'}), 400
        
        # Get analysis result using server's API key
        # analysis_handler.get_deep_analysis is now async
        result = await analysis_handler.get_deep_analysis(article_url, analysis_type, search_params)
        
        print(f"[Web /deep-analysis] Analysis completed successfully for {analysis_type}", flush=True)
        
        raw_analysis_data = result.get('analysis', {})
        adapted_analysis_data = raw_analysis_data # Default to raw if no specific adapter

        if analysis_type == 'fact-check':
            adapted_analysis_data = _adapt_fact_check_for_web_ui(raw_analysis_data)
        elif analysis_type == 'bias':
            adapted_analysis_data = _adapt_bias_for_web_ui(raw_analysis_data)
        elif analysis_type == 'timeline':
            adapted_analysis_data = _adapt_timeline_for_web_ui(raw_analysis_data)
        elif analysis_type == 'expert':
            adapted_analysis_data = _adapt_expert_for_web_ui(raw_analysis_data)
        elif analysis_type == 'x-pulse':
            adapted_analysis_data = _adapt_x_pulse_for_web_ui(raw_analysis_data)
            
        # Return in the format expected by frontend
        response = jsonify({
            'success': True, 
            'result': adapted_analysis_data, # Use adapted data
            'citations': result.get('citations', []) # Citations are currently empty from handler
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except Exception as e:
        print(f"[Web /deep-analysis] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        response = jsonify({
            'success': False, 
            'error': str(e)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@web_bp.route('/web/status', methods=['GET'])
def web_status():
    """Check if web API is working"""
    return jsonify({
        'status': 'ok',
        'api_key_configured': bool(API_KEY),
        'auth_enabled': AUTH_ENABLED
    }), 200, {'Access-Control-Allow-Origin': '*'}


@web_bp.route('/web')
@web_bp.route('/web/')
def serve_web_app():
    """Serve the web app HTML"""
    from flask import send_from_directory
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_dir, 'web-app.html')

# --- UI Data Adaptation Functions ---

def _adapt_fact_check_for_web_ui(raw_data: dict) -> dict:
    adapted = {}
    
    # Overall credibility mapping
    oc_map = {"υψηλή": "8/10", "μέτρια": "5/10", "χαμηλή": "2/10"}
    adapted['overall_credibility'] = oc_map.get(raw_data.get('overall_credibility', '').lower(), "N/A")
    
    adapted_claims = []
    # The `transform_fact_check_for_ui` in analysis_handlers already transformed original verdicts to boolean 'verified'
    # and original sources to list of URLs.
    for claim_in in raw_data.get('claims', []):
        # `claim_in` here is the output of `transform_fact_check_for_ui` for a single claim
        credibility_score = "9/10" if claim_in.get('verified') else "3/10" # Map boolean 'verified'
        
        adapted_claims.append({
            "claim": claim_in.get('statement'),
            "verification": claim_in.get('explanation'), # UI uses 'verification' for explanation
            "credibility": credibility_score,
            "sources": claim_in.get('sources', []) # Should be list of URLs
        })
    adapted['claims'] = adapted_claims
    
    adapted['red_flags'] = raw_data.get('red_flags', [])
    adapted['missing_context'] = raw_data.get('missing_context', "N/A")
    adapted['source_quality'] = "N/A" # Not available from Pydantic model

    return adapted

def _adapt_bias_for_web_ui(raw_data: dict) -> dict:
    adapted = {}
    # raw_data is the output of `transform_bias_for_ui` from analysis_handlers
    adapted['position'] = str(raw_data.get('objectivity_score_raw', "N/A")) + "/10"
    adapted['leaning'] = raw_data.get('political_lean', "N/A")
    adapted['analysis'] = raw_data.get('reasoning_raw', "No detailed reasoning provided.")
    
    indicators = raw_data.get('language_analysis', {}).get('loaded_words', [])
    if not indicators:
        framing_str = raw_data.get('language_analysis', {}).get('framing', "")
        if framing_str:
            indicators = [f.strip() for f in framing_str.split(',') if f.strip()]
            
    adapted['indicators'] = indicators if indicators else ["No specific indicators identified."]
    
    return adapted

def _adapt_timeline_for_web_ui(raw_data: dict) -> dict:
    adapted = {}
    adapted['story_title'] = raw_data.get('story_title', "N/A")
    
    adapted_events = []
    for event_in in raw_data.get('events', []):
        adapted_events.append({
            "date": event_in.get('date'),
            "description": event_in.get('description'),
            "significance": event_in.get('importance'), # UI uses 'significance'
            "title": event_in.get('title') 
        })
    adapted['events'] = adapted_events
    
    # Combine duration and key_turning_points for UI 'context' field
    context_parts = []
    if raw_data.get('duration'):
        context_parts.append(f"Duration: {raw_data.get('duration')}")
    if raw_data.get('key_turning_points'):
        turning_points_str = "; ".join(raw_data.get('key_turning_points',[]))
        context_parts.append(f"Key Turning Points: {turning_points_str}")
    adapted['context'] = ". ".join(context_parts) if context_parts else "N/A"
    
    adapted['future_implications'] = raw_data.get('future_implications', "N/A")
    return adapted

def _adapt_expert_for_web_ui(raw_data: dict) -> dict:
    adapted = {}
    adapted['topic_summary'] = raw_data.get('topic_summary', "N/A")
    
    adapted_opinions = []
    for expert_in in raw_data.get('experts', []):
        expert_details = expert_in.get('expert', {})
        expert_name = expert_details.get('name', 'Unknown Expert')
        expert_title = expert_details.get('title', '')
        
        adapted_opinions.append({
            "quote": expert_in.get('key_quote', "N/A"),
            "expert": f"{expert_name}{', ' + expert_title if expert_title else ''}",
            "credentials": expert_details.get('affiliation', "N/A"),
            "context": expert_in.get('main_argument', "N/A") # UI uses 'context' for main_argument
        })
    adapted['opinions'] = adapted_opinions
    
    adapted['consensus_level'] = raw_data.get('consensus_level', "N/A")
    adapted['key_debates'] = raw_data.get('key_debates', [])
    return adapted

def _adapt_x_pulse_for_web_ui(raw_data: dict) -> dict:
    adapted = {}
    adapted['overall_discourse_summary'] = raw_data.get('overall_discourse_summary', "N/A")
    adapted['themes'] = [theme.get('theme_title', "Untitled Theme") for theme in raw_data.get('discussion_themes', [])]
    
    # Sentiment mapping (simplified)
    sentiment_map = {
        "Θετικό": {"positive": 100, "neutral": 0, "negative": 0},
        "Αρνητικό": {"positive": 0, "neutral": 0, "negative": 100},
        "Μικτό": {"positive": 33, "neutral": 34, "negative": 33},
        "Ουδέτερο": {"positive": 0, "neutral": 100, "negative": 0},
    }
    overall_sentiment_str = raw_data.get('overall_sentiment') # This is an enum value, e.g., "Θετικό"
    adapted['sentiment'] = sentiment_map.get(overall_sentiment_str, {"positive": 0, "neutral": 100, "negative": 0}) # Default to neutral
    adapted['overall_sentiment_string'] = overall_sentiment_str if overall_sentiment_str else "Ουδέτερο"


    adapted_influencers = []
    for name_str in raw_data.get('key_influencers', []):
        adapted_influencers.append({"username": name_str, "stance": "neutral"}) # Stance not available
    adapted['influencers'] = adapted_influencers
    
    adapted['misinformation'] = [] # Not available from Pydantic schema
    adapted['public_concerns'] = [] # Not available from Pydantic schema
    
    adapted['total_posts_analyzed'] = raw_data.get('total_posts_analyzed', 0)
    adapted['trending_hashtags'] = raw_data.get('trending_hashtags', [])
    adapted['data_caveats'] = raw_data.get('data_caveats', "Standard data limitations apply.")
    return adapted



@web_bp.route('/debug')
@web_bp.route('/debug/')
def serve_debug_page():
    """Serve the debug interface HTML"""
    from flask import send_from_directory
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_dir, 'debug.html')


@web_bp.route('/')
def home():
    """Redirect root to web app"""
    from flask import redirect
    return redirect('/web', code=302)