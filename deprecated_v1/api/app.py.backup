"""
Main Flask application for News Copilot API
"""
from flask import Flask
from flask_cors import CORS
from .routes import main_bp
from .config import AUTH_ENABLED


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder='../static')
    
    # Enable CORS
    CORS(app)
    
    # Register main routes blueprint
    app.register_blueprint(main_bp)
    
    # Register web routes (no auth required)
    from .web_routes import web_bp
    app.register_blueprint(web_bp)
    print("✅ Web routes enabled (no auth required)")
    
    # Import and register auth blueprints if available
    try:
        from .http_supabase import http_supabase_bp
        app.register_blueprint(http_supabase_bp)
        print("✅ HTTP Supabase authentication enabled")
        
        # Also register the augment-stream and deep-analysis routes with auth
        from .http_supabase import require_http_supabase_auth as require_auth
        from .routes import augment_article_stream_route, deep_analysis_route
        
        # Add authenticated routes
        app.add_url_rule(
            '/augment-stream',
            endpoint='augment_stream',
            view_func=require_auth('basic_analysis')(augment_article_stream_route),
            methods=['GET']
        )
        
        app.add_url_rule(
            '/deep-analysis',
            endpoint='deep_analysis',
            view_func=require_auth('deep_analysis')(deep_analysis_route),
            methods=['POST']
        )
        
    except ImportError as e:
        print(f"⚠️ Supabase auth not available: {e}")
        print("Running without authentication")
        
        # Add routes without auth
        from .routes import augment_article_stream_route, deep_analysis_route
        
        app.add_url_rule(
            '/augment-stream',
            endpoint='augment_stream',
            view_func=augment_article_stream_route,
            methods=['GET']
        )
        
        app.add_url_rule(
            '/deep-analysis',
            endpoint='deep_analysis',
            view_func=deep_analysis_route,
            methods=['POST']
        )
    
    return app


# Create the app instance
app = create_app()