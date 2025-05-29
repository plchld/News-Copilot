"""
Web interface for News Aggregator with integrated API
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any

from api.main_api import create_api_app
from processors.enhanced_article_processor import EnhancedArticleProcessor
from config.config import WEB_HOST, WEB_PORT, WEB_DEBUG

# Create app with integrated API
app = create_api_app()

# Global processor (for direct web interface use)
enhanced_processor = EnhancedArticleProcessor()


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/articles')
def list_articles():
    """List all stored articles"""
    try:
        enriched_only = request.args.get('enriched_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        
        result = enhanced_processor.list_articles(limit=limit, enriched_only=enriched_only)
        
        # Format articles for frontend
        formatted_articles = []
        for article in result['articles']:
            formatted_article = {
                'id': article['id'],
                'title': article['title'],
                'url': article['original_url'],
                'source': article['source_domain'],
                'word_count': article['word_count'],
                'storage_date': article['storage_date'],
                'enriched': article.get('enriched', False),
                'analyses': []  # Will be populated from enriched data if available
            }
            formatted_articles.append(formatted_article)
        
        return jsonify({
            'status': 'success',
            'articles': formatted_articles,
            'stats': result['stats'],
            'total': result['total_found']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/article/<article_id>')
def get_article(article_id):
    """Get specific stored article"""
    try:
        article_data = enhanced_processor.get_article(article_id)
        
        if not article_data:
            return jsonify({
                'status': 'error',
                'error': 'Article not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': article_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/process', methods=['POST'])
def process_article():
    """Process a new article"""
    try:
        data = request.get_json()
        url = data.get('url')
        enrich = data.get('enrich', True)
        
        if not url:
            return jsonify({
                'status': 'error',
                'error': 'URL is required'
            }), 400
        
        # Process article with enhanced processor
        result = enhanced_processor.process_article_url(url, enrich=enrich)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.teardown_appcontext
def cleanup(error):
    """Cleanup on app context teardown"""
    pass


if __name__ == '__main__':
    print(f"Starting News Aggregator Web Interface...")
    print(f"Access at: http://localhost:{WEB_PORT}")
    
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG)