"""
Main API Application - Combines all API blueprints
"""
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.agent_api import agent_api
from api.article_api import article_api
from config.config import WEB_HOST, WEB_PORT, WEB_DEBUG


def create_api_app():
    """Create and configure the main API application"""
    app = Flask(__name__)
    
    # Enable CORS for cross-origin requests
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(agent_api)
    app.register_blueprint(article_api)
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """Main API health check"""
        return jsonify({
            'status': 'healthy',
            'service': 'news-aggregator-api',
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'agents': '/api/agents/*',
                'articles': '/api/articles/*'
            }
        })
    
    @app.route('/api/info', methods=['GET'])
    def api_info():
        """API information and available endpoints"""
        return jsonify({
            'service': 'News Aggregator API v2',
            'description': 'RESTful API for Greek news analysis with AI agents',
            'version': '2.0',
            'endpoints': {
                'agent_endpoints': {
                    'health': 'GET /api/agents/health',
                    'list_agents': 'GET /api/agents/list',
                    'single_agent': 'POST /api/agents/{agent_name}/analyze',
                    'multiple_agents': 'POST /api/agents/analyze-multiple',
                    'full_analysis': 'POST /api/agents/analyze-full',
                    'batch_analysis': 'POST /api/agents/batch',
                    'agent_config': 'GET /api/agents/{agent_name}/config'
                },
                'article_endpoints': {
                    'health': 'GET /api/articles/health',
                    'process': 'POST /api/articles/process',
                    'list': 'GET /api/articles/list',
                    'get_article': 'GET /api/articles/{id}',
                    'enrichments': 'GET /api/articles/{id}/enrichments',
                    'specific_enrichment': 'GET /api/articles/{id}/enrichments/{type}',
                    'export': 'GET /api/articles/{id}/export',
                    'stats': 'GET /api/articles/stats',
                    'search': 'POST /api/articles/search'
                }
            },
            'available_agents': [
                'jargon', 'viewpoints', 'fact_check', 
                'bias', 'timeline', 'expert'
            ],
            'supported_formats': ['json', 'txt', 'md'],
            'timestamp': datetime.now().isoformat()
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'error': 'Endpoint not found',
            'available_endpoints': '/api/info'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'error': 'Internal server error'
        }), 500
    
    return app


if __name__ == '__main__':
    """Run the API server"""
    app = create_api_app()
    
    print("🚀 NEWS AGGREGATOR API v2")
    print("=" * 50)
    print(f"🌐 Server: http://localhost:{WEB_PORT}")
    print(f"📖 API Info: http://localhost:{WEB_PORT}/api/info")
    print(f"🔍 Agents: http://localhost:{WEB_PORT}/api/agents/list")
    print(f"📄 Articles: http://localhost:{WEB_PORT}/api/articles/stats")
    print("=" * 50)
    
    app.run(
        host=WEB_HOST,
        port=WEB_PORT,
        debug=WEB_DEBUG
    )