"""
Flask routes module for News Copilot API
Contains all route definitions and request handlers
"""
import json
from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
from .analysis_handlers import AnalysisHandler
from .config import AUTH_ENABLED

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize analysis handler
analysis_handler = AnalysisHandler()


@main_bp.route('/', methods=['GET'])
def home():
    """Health check and API info endpoint, or serve auth callback page"""
    # Check if this is an API request or browser request
    accept_header = request.headers.get('Accept', '')
    
    # If it's a browser request (accepts HTML) and has auth tokens in hash, serve the static page
    if 'text/html' in accept_header:
        # Serve the static index.html for browser requests
        return current_app.send_static_file('index.html')
    
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


@main_bp.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check for monitoring"""
    return jsonify({"status": "ok"})


# Serve static verification pages
@main_bp.route('/verification-success.html')
def verification_success():
    """Serve email verification success page"""
    return current_app.send_static_file('verification-success.html')


@main_bp.route('/verification-failed.html')
def verification_failed():
    """Serve email verification failed page"""
    return current_app.send_static_file('verification-failed.html')


@main_bp.route('/verification-expired.html')
def verification_expired():
    """Serve email verification expired page"""
    return current_app.send_static_file('verification-failed.html')  # Use same page for now


def augment_article_stream_route():
    """Handle augment-stream requests"""
    print("\n[Flask /augment-stream] Received stream request!", flush=True)
    article_url = request.args.get('url')
    print(f"[Flask /augment-stream] URL from request: {article_url}", flush=True)

    if not article_url:
        print("[Flask /augment-stream] ERROR: Missing 'url' parameter", flush=True)
        def error_stream():
            yield f"event: error\ndata: {json.dumps({'message': 'Missing URL parameter'})}\n\n"
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')

    # Create a wrapper generator that logs usage after completion
    def stream_with_usage_logging():
        # Track if we've logged usage yet (only log once)
        usage_logged = False
        
        try:
            # Get user info from request context (set by auth decorator)
            user_id = getattr(request, 'user_id', None)
            
            # Stream the analysis (async generator)
            import asyncio
            
            # Handle async generator in sync context
            async def get_chunks():
                chunks = []
                async for chunk in analysis_handler.get_augmentations_stream(article_url):
                    chunks.append(chunk)
                return chunks
            
            # Run async generator and yield chunks
            chunks = asyncio.run(get_chunks())
            for chunk in chunks:
                yield chunk
            
            # Log usage only after successful completion
            if user_id and not usage_logged:
                try:
                    # Import the correct log_usage function based on auth system
                    if hasattr(request, '_http_supabase_auth'):
                        from .http_supabase import log_usage
                    else:
                        from .supabase_auth import log_usage
                    
                    # Log basic analysis (jargon + viewpoints)
                    log_usage(
                        user_id=user_id,
                        analysis_type='basic_analysis',
                        article_url=article_url
                    )
                    usage_logged = True
                    print(f"[Flask /augment-stream] Logged usage for user {user_id}", flush=True)
                except Exception as e:
                    print(f"[Flask /augment-stream] Error logging usage: {e}", flush=True)
                    
        except Exception as e:
            print(f"[Flask /augment-stream] Error in stream: {e}", flush=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return Response(
        stream_with_context(stream_with_usage_logging()), 
        mimetype='text/event-stream'
    )


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
        result = analysis_handler.get_deep_analysis(article_url, analysis_type, search_params)
        
        # Log usage after successful analysis
        user_id = getattr(request, 'user_id', None)
        if user_id:
            try:
                # Import the correct log_usage function based on auth system
                if hasattr(request, '_http_supabase_auth'):
                    from .http_supabase import log_usage
                else:
                    from .supabase_auth import log_usage
                
                # Log deep analysis usage
                log_usage(
                    user_id=user_id,
                    analysis_type=analysis_type,  # This will be fact-check, bias, timeline, expert, or x-pulse
                    article_url=article_url
                )
                print(f"[Flask /deep-analysis] Logged {analysis_type} usage for user {user_id}", flush=True)
            except Exception as e:
                print(f"[Flask /deep-analysis] Error logging usage: {e}", flush=True)
        
        # Return in the format expected by frontend
        return jsonify({
            'success': True, 
            'result': result['analysis'],
            'citations': result['citations']
        })
        
    except Exception as e:
        print(f"[Flask /deep-analysis] ERROR: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# Register routes with decorators after blueprint creation
# This will be done in the main app when registering the blueprint