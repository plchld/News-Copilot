"""Example integration of the agentic architecture with existing Flask routes"""

from flask import jsonify, Response
import json
import asyncio
from typing import Dict, Any

from .coordinator import AgentCoordinator, AnalysisType, CoordinatorConfig
from ..grok_client import GrokClient
from ..article_extractor import fetch_text


# Integration with existing routes.py
def integrate_agentic_routes(app, grok_client: GrokClient):
    """Add new agentic routes to Flask app"""
    
    # Initialize coordinator with configuration
    coordinator_config = CoordinatorConfig(
        max_parallel_agents=4,
        enable_streaming=True,
        retry_failed_agents=True,
        cost_limit_per_request=0.50  # $0.50 per request limit
    )
    coordinator = AgentCoordinator(grok_client, coordinator_config)
    
    @app.route('/api/v2/analyze', methods=['POST'])
    async def analyze_v2():
        """New endpoint using agentic architecture"""
        data = request.get_json()
        article_url = data.get('url')
        requested_analyses = data.get('analyses', ['jargon', 'viewpoints'])
        
        # Extract article text
        article_text = fetch_text(article_url)
        if not article_text:
            return jsonify({'error': 'Failed to extract article'}), 400
        
        # Convert string types to enums
        analysis_types = []
        for analysis in requested_analyses:
            try:
                analysis_types.append(AnalysisType(analysis))
            except ValueError:
                pass
        
        # Get user context (if authenticated)
        user_context = {
            'tier': 'free',  # Would come from auth
            'user_id': None  # Would come from auth
        }
        
        # Execute analyses in parallel
        results = await coordinator.analyze_article(
            article_url=article_url,
            article_text=article_text,
            analysis_types=analysis_types,
            user_context=user_context
        )
        
        # Format response
        response_data = {}
        for analysis_type, result in results.items():
            if result.success:
                response_data[analysis_type.value] = {
                    'success': True,
                    'data': result.data,
                    'model_used': result.model_used.value if result.model_used else None,
                    'execution_time_ms': result.execution_time_ms
                }
            else:
                response_data[analysis_type.value] = {
                    'success': False,
                    'error': result.error
                }
        
        return jsonify(response_data)
    
    @app.route('/api/v2/analyze-stream', methods=['POST'])
    async def analyze_stream_v2():
        """Streaming endpoint using agentic architecture"""
        data = request.get_json()
        article_url = data.get('url')
        requested_analyses = data.get('analyses', ['jargon', 'viewpoints'])
        
        # Extract article text
        article_text = fetch_text(article_url)
        if not article_text:
            return jsonify({'error': 'Failed to extract article'}), 400
        
        # Convert string types to enums
        analysis_types = []
        for analysis in requested_analyses:
            try:
                analysis_types.append(AnalysisType(analysis))
            except ValueError:
                pass
        
        def generate():
            """Generator for SSE streaming"""
            # Create event loop for async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Stream callback
            async def stream_result(analysis_type: AnalysisType, result):
                data = {
                    'type': analysis_type.value,
                    'success': result.success,
                    'data': result.data if result.success else None,
                    'error': result.error if not result.success else None,
                    'model_used': result.model_used.value if result.model_used else None
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Execute with streaming
            results = loop.run_until_complete(
                coordinator.analyze_article(
                    article_url=article_url,
                    article_text=article_text,
                    analysis_types=analysis_types,
                    stream_callback=stream_result
                )
            )
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')


# Migration helper for existing AnalysisHandler
class AgenticAnalysisHandler:
    """Drop-in replacement for existing AnalysisHandler using agents"""
    
    def __init__(self, grok_client: GrokClient):
        self.coordinator = AgentCoordinator(grok_client)
    
    async def get_deep_analysis(self, article_url: str, article_text: str, 
                               analysis_type: str, user_id: str = None) -> Dict[str, Any]:
        """Backward compatible method using agents"""
        # Map old analysis types to new enum
        type_mapping = {
            'jargon': AnalysisType.JARGON,
            'viewpoints': AnalysisType.VIEWPOINTS,
            'fact-check': AnalysisType.FACT_CHECK,
            'bias': AnalysisType.BIAS,
            'timeline': AnalysisType.TIMELINE,
            'expert': AnalysisType.EXPERT,
            'x-pulse': AnalysisType.X_PULSE
        }
        
        analysis_enum = type_mapping.get(analysis_type)
        if not analysis_enum:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        # Execute single analysis
        result = await self.coordinator.analyze_single(
            article_url=article_url,
            article_text=article_text,
            analysis_type=analysis_enum,
            user_context={'user_id': user_id}
        )
        
        if result.success:
            return result.data
        else:
            raise Exception(f"Analysis failed: {result.error}")


# Performance comparison example
async def compare_performance():
    """Compare old sequential vs new parallel execution"""
    import time
    
    # Sample article
    article_url = "https://example.com/article"
    article_text = "Sample article text..."
    
    # Initialize
    grok_client = GrokClient()
    coordinator = AgentCoordinator(grok_client)
    
    # Test parallel execution
    start = time.time()
    results = await coordinator.analyze_article(
        article_url=article_url,
        article_text=article_text,
        analysis_types=[
            AnalysisType.JARGON,
            AnalysisType.VIEWPOINTS,
            AnalysisType.FACT_CHECK,
            AnalysisType.BIAS,
            AnalysisType.TIMELINE
        ]
    )
    parallel_time = time.time() - start
    
    print(f"Parallel execution: {parallel_time:.2f}s")
    print(f"Results: {len([r for r in results.values() if r.success])} successful")
    
    # With old sequential approach, this would take ~5x longer
    estimated_sequential = parallel_time * 5
    print(f"Estimated sequential: {estimated_sequential:.2f}s")
    print(f"Speed improvement: {estimated_sequential/parallel_time:.1f}x faster")


if __name__ == "__main__":
    # Run performance comparison
    asyncio.run(compare_performance())