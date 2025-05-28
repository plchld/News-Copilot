"""Analysis endpoints for News Copilot API"""

from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('analysis', __name__, url_prefix='/api')

@bp.route('/analysis/types')
def get_analysis_types():
    """Get available analysis types"""
    return jsonify({
        'individual': ['jargon', 'viewpoints', 'fact-check', 'bias', 'timeline', 'expert', 'x-pulse'],
        'anonymous_access': ['jargon', 'viewpoints', 'fact-check', 'bias'],
        'requires_auth': ['timeline', 'expert', 'x-pulse'],
        # Legacy support
        'basic': ['jargon', 'viewpoints'],
        'deep': ['fact-check', 'bias', 'timeline', 'expert', 'x-pulse']
    })

@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'news-copilot-api'})