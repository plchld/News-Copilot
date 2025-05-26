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
            
            # Handle async generator properly
            async def collect_all_chunks():
                chunks = []
                async for chunk in analysis_handler.get_augmentations_stream(article_url):
                    chunks.append(chunk)
                return chunks
            
            # Run async generator and collect chunks
            chunks = asyncio.run(collect_all_chunks())
            
            # Yield chunks synchronously for Flask SSE
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


@main_bp.route('/api/debug/agent', methods=['POST'])
def debug_agent():
    """Debug endpoint for testing individual agents
    
    Request body:
    {
        "url": "article_url",
        "agent": "viewpoints|jargon|fact_check|bias|timeline|expert|x_pulse",
        "debug_level": "minimal|normal|verbose|extreme"  (optional, default: verbose)
    }
    
    Returns detailed execution trace and debug information
    """
    try:
        data = request.get_json()
        article_url = data.get('url')
        agent_type = data.get('agent')
        debug_level = data.get('debug_level', 'verbose')
        
        if not article_url or not agent_type:
            return jsonify({
                'success': False,
                'error': 'Missing url or agent parameter'
            }), 400
        
        # Import debug utilities
        from .agents.debug_framework import DebugLevel, debug_single_agent
        from .agents.optimized_coordinator import AnalysisType
        
        # Map agent type to actual agent
        agent_map = {
            'viewpoints': ('VIEWPOINTS', lambda gc: ViewpointsAgent.create(gc)),
            'jargon': ('JARGON', lambda gc: JargonAgent.create(gc)),
            'fact_check': ('FACT_CHECK', lambda gc: FactCheckAgent.create(gc)),
            'bias': ('BIAS', lambda gc: BiasAgent.create(gc)),
            'timeline': ('TIMELINE', lambda gc: TimelineAgent.create(gc)),
            'expert': ('EXPERT', lambda gc: ExpertAgent.create(gc)),
            'x_pulse': ('X_PULSE', lambda gc: XPulseAgent.create(gc))
        }
        
        if agent_type not in agent_map:
            return jsonify({
                'success': False,
                'error': f'Unknown agent type: {agent_type}',
                'available_agents': list(agent_map.keys())
            }), 400
        
        # Get debug level
        try:
            debug_level_enum = DebugLevel(debug_level)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid debug level: {debug_level}',
                'available_levels': [level.value for level in DebugLevel]
            }), 400
        
        # Import required agents
        from .agents.viewpoints_agent import ViewpointsAgent
        from .agents.jargon_agent import JargonAgent
        from .agents.fact_check_agent import FactCheckAgent
        from .agents.bias_agent import BiasAgent
        from .agents.timeline_agent import TimelineAgent
        from .agents.expert_agent import ExpertAgent
        from .agents.x_pulse_agent import XPulseAgent
        
        # Create agent
        analysis_type_name, agent_factory = agent_map[agent_type]
        agent = agent_factory(analysis_handler.grok_client)
        
        # Run debug analysis
        import asyncio
        result, report = asyncio.run(debug_single_agent(
            agent,
            article_url,
            debug_level_enum
        ))
        
        # Format response
        response = {
            'success': result.success,
            'agent': agent_type,
            'execution_time_ms': result.execution_time_ms,
            'model_used': result.model_used.value if result.model_used else None,
            'tokens_used': result.tokens_used,
            'debug_report': report
        }
        
        if result.success and result.data:
            response['result'] = result.data
        elif result.error:
            response['error'] = result.error
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@main_bp.route('/api/debug/batch', methods=['POST'])
def debug_batch():
    """Debug endpoint for testing multiple agents
    
    Request body:
    {
        "url": "article_url",
        "agents": ["viewpoints", "jargon", ...] or "all",
        "debug_level": "minimal|normal|verbose|extreme"  (optional, default: normal)
    }
    
    Returns batch execution report with timing and success metrics
    """
    try:
        data = request.get_json()
        article_url = data.get('url')
        agents = data.get('agents', 'all')
        debug_level = data.get('debug_level', 'normal')
        
        if not article_url:
            return jsonify({
                'success': False,
                'error': 'Missing url parameter'
            }), 400
        
        # Import debug utilities
        from .agents.debug_framework import DebugLevel, debug_agent_batch
        from .agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, AnalysisType
        
        # Get debug level
        try:
            debug_level_enum = DebugLevel(debug_level)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid debug level: {debug_level}',
                'available_levels': [level.value for level in DebugLevel]
            }), 400
        
        # Determine which agents to run
        if agents == 'all':
            analysis_types = [
                AnalysisType.JARGON,
                AnalysisType.VIEWPOINTS,
                AnalysisType.FACT_CHECK,
                AnalysisType.BIAS,
                AnalysisType.TIMELINE,
                AnalysisType.EXPERT
            ]
        else:
            # Map agent names to AnalysisType
            type_map = {
                'viewpoints': AnalysisType.VIEWPOINTS,
                'jargon': AnalysisType.JARGON,
                'fact_check': AnalysisType.FACT_CHECK,
                'bias': AnalysisType.BIAS,
                'timeline': AnalysisType.TIMELINE,
                'expert': AnalysisType.EXPERT,
                'x_pulse': AnalysisType.X_PULSE
            }
            
            analysis_types = []
            for agent_name in agents:
                if agent_name in type_map:
                    analysis_types.append(type_map[agent_name])
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Unknown agent: {agent_name}',
                        'available_agents': list(type_map.keys())
                    }), 400
        
        # Create coordinator
        coordinator = AgentCoordinator(analysis_handler.grok_client)
        
        # Run batch debug
        import asyncio
        results, report = asyncio.run(debug_agent_batch(
            coordinator,
            analysis_types,
            article_url,
            debug_level_enum
        ))
        
        # Format response
        response = {
            'success': True,
            'debug_report': report,
            'results': {}
        }
        
        # Add individual results
        for analysis_type, result in results.items():
            agent_data = {
                'success': result.success,
                'execution_time_ms': result.execution_time_ms,
                'model_used': result.model_used.value if result.model_used else None,
                'tokens_used': result.tokens_used
            }
            
            if result.success and result.data:
                agent_data['data'] = result.data
            elif result.error:
                agent_data['error'] = result.error
            
            response['results'][analysis_type.value] = agent_data
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# Register routes with decorators after blueprint creation
# This will be done in the main app when registering the blueprint