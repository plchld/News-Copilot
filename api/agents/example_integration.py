"""
Example of integrating the agentic architecture with existing routes.
This shows how to gradually migrate to the new architecture.
"""
from flask import request, jsonify, Response, stream_with_context
from .coordinator import AnalysisCoordinator


# Initialize coordinator (could be singleton)
coordinator = AnalysisCoordinator()


def augment_article_stream_route_v2():
    """
    Enhanced version using agent coordinator for parallel execution.
    """
    article_url = request.args.get('url')
    
    if not article_url:
        def error_stream():
            yield coordinator.stream_event('error', {'message': 'Missing URL parameter'})
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')
    
    # Stream results using coordinator
    return Response(
        stream_with_context(coordinator.get_augmentations_stream(article_url)),
        mimetype='text/event-stream'
    )


def deep_analysis_route_v2():
    """
    Enhanced deep analysis using specific agents.
    """
    try:
        data = request.get_json()
        article_url = data.get('url')
        analysis_type = data.get('analysis_type')
        search_params = data.get('search_params', {})
        
        if not article_url or not analysis_type:
            return jsonify({'success': False, 'error': 'Missing URL or analysis_type parameter'}), 400
        
        # Use coordinator for single analysis
        result = coordinator.analyze_parallel(
            article_url=article_url,
            analysis_types=[analysis_type],
            search_params=search_params
        )
        
        # Extract the specific analysis result
        if analysis_type in result['analyses']:
            analysis_result = result['analyses'][analysis_type]
            
            if 'error' in analysis_result:
                return jsonify({'success': False, 'error': analysis_result['error']}), 500
            
            return jsonify({
                'success': True,
                'result': analysis_result['analysis'],
                'citations': analysis_result.get('citations', [])
            })
        else:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def multi_analysis_route():
    """
    New route for requesting multiple analyses at once.
    """
    try:
        data = request.get_json()
        article_url = data.get('url')
        analysis_types = data.get('analysis_types', ['jargon', 'viewpoints'])
        search_params = data.get('search_params', {})
        
        if not article_url:
            return jsonify({'success': False, 'error': 'Missing URL parameter'}), 400
        
        # Perform parallel analyses
        result = coordinator.analyze_parallel(
            article_url=article_url,
            analysis_types=analysis_types,
            search_params=search_params,
            max_workers=6  # Allow more parallelism
        )
        
        return jsonify({
            'success': True,
            'article_url': result['article_url'],
            'analyses': result['analyses'],
            'timestamp': result['timestamp']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def analysis_stream_route():
    """
    Stream multiple analyses as they complete.
    """
    article_url = request.args.get('url')
    analysis_types = request.args.getlist('types') or ['jargon', 'viewpoints', 'fact-check']
    
    if not article_url:
        def error_stream():
            yield coordinator.stream_event('error', {'message': 'Missing URL parameter'})
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')
    
    # Stream all requested analyses
    return Response(
        stream_with_context(
            coordinator.stream_analyses(
                article_url=article_url,
                analysis_types=analysis_types
            )
        ),
        mimetype='text/event-stream'
    )


# Example of gradual migration in app.py:
"""
from api.agents.example_integration import (
    augment_article_stream_route_v2,
    deep_analysis_route_v2,
    multi_analysis_route,
    analysis_stream_route
)

# Add new routes alongside existing ones
app.route('/augment-stream-v2', methods=['GET'])(augment_article_stream_route_v2)
app.route('/deep-analysis-v2', methods=['POST'])(deep_analysis_route_v2)
app.route('/multi-analysis', methods=['POST'])(multi_analysis_route)
app.route('/analysis-stream', methods=['GET'])(analysis_stream_route)

# Gradually migrate clients to v2 endpoints
# Once stable, replace original implementations
"""