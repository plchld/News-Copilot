"""
Article API - RESTful endpoints for article management
"""
from flask import Blueprint, request, jsonify, send_file
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.enhanced_article_processor import EnhancedArticleProcessor
from storage.article_storage import ArticleStorage


# Create Blueprint
article_api = Blueprint('article_api', __name__, url_prefix='/api/articles')

# Initialize processors
enhanced_processor = EnhancedArticleProcessor(use_comprehensive=True)
storage = ArticleStorage()


@article_api.route('/health', methods=['GET'])
def health_check():
    """Health check for article API"""
    stats = storage.get_stats()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'storage_stats': stats
    })


@article_api.route('/process', methods=['POST'])
def process_article():
    """
    Process a new article from URL
    
    Expected JSON payload:
    {
        "url": "https://example.com/article",
        "enrich": true,  # Optional, default true
        "analyses": ["jargon", "bias"]  # Optional, specific analyses to run
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'JSON payload required'
            }), 400
        
        url = data.get('url')
        enrich = data.get('enrich', True)
        specific_analyses = data.get('analyses')  # None means all analyses
        
        if not url:
            return jsonify({
                'status': 'error',
                'error': 'URL is required'
            }), 400
        
        print(f"[ArticleAPI] Processing article: {url}")
        print(f"[ArticleAPI] Enrich: {enrich}, Specific analyses: {specific_analyses}")
        
        # Process article
        result = enhanced_processor.process_article_url(url, enrich=enrich)
        
        # If specific analyses requested and enrichment was successful, 
        # we might need to re-run with only those analyses
        if (enrich and specific_analyses and 
            result.get('status') == 'success' and 
            result.get('enriched')):
            
            print(f"[ArticleAPI] Re-running with specific analyses: {specific_analyses}")
            # This would require extending the enhanced_processor to support specific analyses
            # For now, we'll note this in the response
            result['note'] = f'Specific analyses requested: {specific_analyses}'
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[ArticleAPI] Error processing article: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/list', methods=['GET'])
def list_articles():
    """
    List stored articles with filtering options
    
    Query parameters:
    - limit: Maximum number of articles (default: 20)
    - enriched_only: Show only enriched articles (default: false)
    - source: Filter by source domain
    - search: Search in title/content
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        enriched_only = request.args.get('enriched_only', 'false').lower() == 'true'
        source_filter = request.args.get('source')
        search_term = request.args.get('search')
        
        print(f"[ArticleAPI] Listing articles: limit={limit}, enriched_only={enriched_only}")
        
        # Get articles from storage
        articles = storage.list_articles(limit=limit, enriched_only=enriched_only)
        
        # Apply additional filters
        filtered_articles = articles
        
        if source_filter:
            filtered_articles = [a for a in filtered_articles 
                               if a.get('source_domain', '').lower() == source_filter.lower()]
        
        if search_term:
            search_lower = search_term.lower()
            filtered_articles = [a for a in filtered_articles 
                               if (search_lower in a.get('title', '').lower() or 
                                   search_lower in a.get('content', '').lower())]
        
        # Get stats
        stats = storage.get_stats()
        
        response = {
            'status': 'success',
            'articles': filtered_articles,
            'total_found': len(filtered_articles),
            'total_in_storage': len(articles),
            'storage_stats': stats,
            'filters_applied': {
                'limit': limit,
                'enriched_only': enriched_only,
                'source': source_filter,
                'search': search_term
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[ArticleAPI] Error listing articles: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/<article_id>', methods=['GET'])
def get_article(article_id: str):
    """Get specific article by ID with all enrichments"""
    try:
        article_data = enhanced_processor.get_article(article_id)
        
        if not article_data:
            return jsonify({
                'status': 'error',
                'error': 'Article not found'
            }), 404
        
        # Format response with metadata
        response = {
            'status': 'success',
            'article_id': article_id,
            'data': article_data,
            'retrieved_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[ArticleAPI] Error retrieving article {article_id}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/<article_id>/enrichments', methods=['GET'])
def get_article_enrichments(article_id: str):
    """Get only the enrichments for a specific article"""
    try:
        article_data = enhanced_processor.get_article(article_id)
        
        if not article_data:
            return jsonify({
                'status': 'error',
                'error': 'Article not found'
            }), 404
        
        # Extract only enrichments
        enrichments = {}
        if 'enriched' in article_data:
            enrichments = article_data['enriched'].get('enrichments', {})
        
        response = {
            'status': 'success',
            'article_id': article_id,
            'enrichments': enrichments,
            'available_analyses': list(enrichments.keys()),
            'retrieved_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/<article_id>/enrichments/<analysis_type>', methods=['GET'])
def get_specific_enrichment(article_id: str, analysis_type: str):
    """Get specific enrichment type for an article"""
    try:
        article_data = enhanced_processor.get_article(article_id)
        
        if not article_data:
            return jsonify({
                'status': 'error',
                'error': 'Article not found'
            }), 404
        
        # Extract specific enrichment
        enrichments = {}
        if 'enriched' in article_data:
            enrichments = article_data['enriched'].get('enrichments', {})
        
        if analysis_type not in enrichments:
            return jsonify({
                'status': 'error',
                'error': f'Analysis type "{analysis_type}" not found',
                'available_analyses': list(enrichments.keys())
            }), 404
        
        response = {
            'status': 'success',
            'article_id': article_id,
            'analysis_type': analysis_type,
            'data': enrichments[analysis_type],
            'retrieved_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/<article_id>/export', methods=['GET'])
def export_article(article_id: str):
    """
    Export article in various formats
    
    Query parameters:
    - format: json, txt, md (default: json)
    - include_enrichments: true/false (default: true)
    """
    try:
        format_type = request.args.get('format', 'json').lower()
        include_enrichments = request.args.get('include_enrichments', 'true').lower() == 'true'
        
        if format_type not in ['json', 'txt', 'md']:
            return jsonify({
                'status': 'error',
                'error': 'Format must be json, txt, or md'
            }), 400
        
        article_data = enhanced_processor.get_article(article_id)
        
        if not article_data:
            return jsonify({
                'status': 'error',
                'error': 'Article not found'
            }), 404
        
        # For now, return the data formatted as JSON
        # In a full implementation, we'd generate actual files
        export_data = article_data
        
        if not include_enrichments and 'enriched' in export_data:
            export_data = {k: v for k, v in export_data.items() if k != 'enriched'}
        
        response = {
            'status': 'success',
            'article_id': article_id,
            'format': format_type,
            'include_enrichments': include_enrichments,
            'data': export_data,
            'exported_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/stats', methods=['GET'])
def get_stats():
    """Get comprehensive statistics about stored articles"""
    try:
        stats = enhanced_processor.get_storage_stats()
        
        response = {
            'status': 'success',
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@article_api.route('/search', methods=['POST'])
def search_articles():
    """
    Advanced search in articles
    
    Expected JSON payload:
    {
        "query": "search terms",
        "filters": {
            "source_domain": "www.example.com",
            "enriched_only": true,
            "date_from": "2025-01-01",
            "date_to": "2025-12-31"
        },
        "limit": 50
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'JSON payload required'
            }), 400
        
        query = data.get('query', '')
        filters = data.get('filters', {})
        limit = data.get('limit', 50)
        
        print(f"[ArticleAPI] Search query: '{query}' with filters: {filters}")
        
        # Get all articles first
        all_articles = storage.list_articles(limit=1000)  # Get more for searching
        
        # Apply search and filters
        results = []
        
        for article in all_articles:
            # Text search
            if query:
                query_lower = query.lower()
                title_match = query_lower in article.get('title', '').lower()
                content_match = query_lower in article.get('content', '').lower()
                
                if not (title_match or content_match):
                    continue
            
            # Apply filters
            if filters.get('source_domain'):
                if article.get('source_domain') != filters['source_domain']:
                    continue
            
            if filters.get('enriched_only') and not article.get('enriched', False):
                continue
            
            # Date filtering would require date parsing
            # TODO: Implement date range filtering
            
            results.append(article)
        
        # Limit results
        results = results[:limit]
        
        response = {
            'status': 'success',
            'query': query,
            'filters': filters,
            'total_found': len(results),
            'results': results,
            'searched_at': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500