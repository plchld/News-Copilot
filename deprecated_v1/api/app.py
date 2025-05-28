"""Flask application factory for News Copilot API"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder='../static')
    
    # Configure CORS for web app
    allowed_origins = [
        'http://localhost:3000',  # Next.js dev
        'http://localhost:8080',  # Flask dev
        'https://news-copilot.vercel.app',  # Production
    ]
    
    # Add custom domain if configured
    custom_domain = os.getenv('CUSTOM_DOMAIN')
    if custom_domain:
        allowed_origins.append(f'https://{custom_domain}')
    
    CORS(app, origins=allowed_origins, supports_credentials=True)
    
    # Register blueprints
    from api.routes import analysis, auth, admin, unified_analysis
    
    app.register_blueprint(analysis.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(unified_analysis.bp)
    
    # Serve static files
    @app.route('/')
    def index():
        """Redirect to web app"""
        return app.send_static_file('web-app.html')
    
    @app.route('/auth/callback')
    def auth_callback():
        """Serve auth callback page"""
        return app.send_static_file('auth-callback.html')
    
    @app.route('/verification-success')
    def verification_success():
        """Serve verification success page"""
        return app.send_static_file('verification-success.html')
    
    @app.route('/verification-failed')
    def verification_failed():
        """Serve verification failed page"""
        return app.send_static_file('verification-failed.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        logging.error(f"[FLASK_APP_ERROR_HANDLER] 404 Not Found: {e}")
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"[FLASK_APP_ERROR_HANDLER] Explicit 500 error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"[FLASK_APP_ERROR_HANDLER] Unhandled Exception: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred'}), 500
    
    # Log startup
    logging.info("News Copilot API initialized")
    
    return app