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
        result = analysis_handler.get_deep_analysis(article_url, analysis_type, search_params)
        
        print(f"[Web /deep-analysis] Analysis completed successfully for {analysis_type}", flush=True)
        
        # Return in the format expected by frontend
        response = jsonify({
            'success': True, 
            'result': result['analysis'],
            'citations': result.get('citations', [])
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