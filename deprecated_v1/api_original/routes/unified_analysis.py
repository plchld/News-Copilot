"""Unified analysis endpoint - Simple, clean API for all analysis types"""

from flask import Blueprint, request, jsonify, Response
from api.auth.decorators import optional_auth
from api.core.analysis_handlers import AnalysisHandler
from api.models import User
import logging
from typing import List, Dict, Any
import time
import json
from functools import wraps

logger = logging.getLogger(__name__)

bp = Blueprint('unified', __name__, url_prefix='/api')

# Analysis types that require authentication
PREMIUM_ANALYSES = {'timeline', 'expert', 'x-pulse'}

# Valid analysis types
VALID_ANALYSIS_TYPES = {'jargon', 'viewpoints', 'fact-check', 'bias', 'timeline', 'expert', 'x-pulse'}

# Rate limiting configuration (can be moved to config later)
RATE_LIMITS = {
    'free': {'requests_per_hour': 10, 'max_concurrent': 2},
    'premium': {'requests_per_hour': 100, 'max_concurrent': 5},
    'admin': {'requests_per_hour': 1000, 'max_concurrent': 10}
}

def validate_request_data(f):
    """Decorator to validate request data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON in request body'}), 400
        
        url = data.get('url')
        types = data.get('types', [])
        
        # Validate URL
        if not url or not isinstance(url, str) or len(url.strip()) == 0:
            return jsonify({'error': 'URL is required and must be a non-empty string'}), 400
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({'error': 'URL must start with http:// or https://'}), 400
        
        # Validate types
        if not types or not isinstance(types, list) or len(types) == 0:
            return jsonify({'error': 'types must be a non-empty array'}), 400
        
        # Check for duplicate types
        if len(types) != len(set(types)):
            return jsonify({'error': 'Duplicate analysis types are not allowed'}), 400
        
        # Validate analysis types
        invalid_types = [t for t in types if t not in VALID_ANALYSIS_TYPES]
        if invalid_types:
            return jsonify({
                'error': f'Invalid analysis types: {invalid_types}',
                'valid_types': list(VALID_ANALYSIS_TYPES)
            }), 400
        
        # Limit number of concurrent analysis types
        if len(types) > 7:  # All available types
            return jsonify({'error': 'Maximum 7 analysis types allowed per request'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

# SSE validation function removed - not needed anymore

def log_request_metrics(f):
    """Decorator to log request metrics"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        # Get request info
        data = request.get_json()
        url = data.get('url', 'unknown') if data else request.args.get('url', 'unknown')
        types = data.get('types', []) if data else request.args.get('types', '').split(',')
        user_agent = request.headers.get('User-Agent', 'unknown')
        ip_address = request.remote_addr
        
        try:
            result = f(*args, **kwargs)
            
            # Log successful request
            execution_time = time.time() - start_time
            logger.info(
                f"[UNIFIED_API] SUCCESS | "
                f"Types: {types} | "
                f"URL: {url[:100]}... | "
                f"Time: {execution_time:.2f}s | "
                f"IP: {ip_address} | "
                f"UA: {user_agent[:50]}..."
            )
            
            return result
            
        except Exception as e:
            # Log failed request
            execution_time = time.time() - start_time
            logger.error(
                f"[UNIFIED_API] ERROR | "
                f"Types: {types} | "
                f"URL: {url[:100]}... | "
                f"Time: {execution_time:.2f}s | "
                f"Error: {str(e)} | "
                f"IP: {ip_address}"
            )
            raise
            
    return decorated_function

# SSE endpoint removed due to complexity - using regular API without timeouts instead

def get_analysis_display_name(analysis_type: str) -> str:
    """Get display name for analysis type"""
    display_names = {
        'jargon': 'Επεξήγηση Όρων',
        'viewpoints': 'Εναλλακτικές Οπτικές',
        'fact-check': 'Έλεγχος Γεγονότων',
        'bias': 'Ανάλυση Μεροληψίας',
        'timeline': 'Χρονολόγιο',
        'expert': 'Απόψεις Ειδικών',
        'x-pulse': 'Κοινωνικός Παλμός'
    }
    return display_names.get(analysis_type, analysis_type)

@bp.route('/analyze', methods=['POST'])
@optional_auth
@validate_request_data
@log_request_metrics
def analyze(current_user: User = None):
    """
    Single unified endpoint for all analysis types.
    
    Request body:
    {
        "url": "https://example.com/article",
        "types": ["jargon", "viewpoints", "fact-check", ...]
    }
    
    Response:
    {
        "results": { "jargon": {...}, "viewpoints": {...}, ... },
        "errors": { "timeline": "error message" },
        "metadata": { "total_time_seconds": 4.2, ... }
    }
    """
    logger.info("[UNIFIED_ANALYZE_ROUTE] Request received. Attempting to parse JSON.")
    start_time = time.time()
    data_for_error_logging = {} # Initialize with an empty dict
    
    try:
        # Parse request (already validated by decorator)
        data = request.get_json()
        data_for_error_logging = data # Store for logging in case of error
        logger.info(f"[UNIFIED_ANALYZE_ROUTE] JSON parsed successfully: {data}")
        url = data.get('url')
        types = data.get('types', [])
        
        # Check authentication for premium analyses
        if not current_user:
            requested_premium = [t for t in types if t in PREMIUM_ANALYSES]
            if requested_premium:
                return jsonify({
                    'error': f'Authentication required for: {requested_premium}',
                    'premium_types': list(PREMIUM_ANALYSES),
                    'free_types': list(VALID_ANALYSIS_TYPES - PREMIUM_ANALYSES)
                }), 401
        
        # Get user tier for rate limiting and features
        user_tier = getattr(current_user, 'tier', 'free') if current_user else 'free'
        user_id = current_user.id if current_user else None
        user_email = current_user.email if current_user else 'anonymous'
        
        # Log request
        logger.info(f"Analysis request: {types} for {url[:100]}... by {user_email} ({user_tier})")
        
        # Build user context
        user_context = {
            'user_id': user_id,
            'user_tier': user_tier,
            'api_key': getattr(current_user, 'api_key', None) if current_user else None,
            'request_ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'request_timestamp': start_time
        }
        
        # Execute analyses using the existing handler
        handler = AnalysisHandler()
        
        try:
            result = handler.process_selective_analysis(
                article_url=url,
                analysis_types=types,
                user_context=user_context
            )
        except Exception as analysis_error:
            logger.error(f"Analysis execution failed: {str(analysis_error)}", exc_info=True)
            return jsonify({
                'error': 'Analysis execution failed',
                'details': str(analysis_error),
                'results': {},
                'errors': {t: str(analysis_error) for t in types},
                'metadata': {
                    'total_time_seconds': round(time.time() - start_time, 2),
                    'analyses_requested': len(types),
                    'analyses_completed': 0,
                    'execution_error': True
                }
            }), 500
        
        # Format response
        total_time = time.time() - start_time
        results = result.get('results', {})
        errors = result.get('errors', {})
        
        response = {
            'results': results,
            'errors': errors,
            'metadata': {
                'total_time_seconds': round(total_time, 2),
                'analyses_requested': len(types),
                'analyses_completed': len(results),
                'analyses_failed': len(errors),
                'user_tier': user_tier,
                'execution_details': result.get('metadata', {}),
                'api_version': '2.0.0'
            }
        }
        
        # Return appropriate status code based on results
        if not results:
            # No successful analyses
            logger.warning(f"[UNIFIED_ANALYZE_ROUTE] No results from analysis for URL: {url}. Response: {response}")
            return jsonify(response), 500
        elif errors:
            # Partial success
            logger.info(f"[UNIFIED_ANALYZE_ROUTE] Partial success for URL: {url}. Response: {response}")
            return jsonify(response), 207  # Multi-Status
        else:
            # Full success
            logger.info(f"[UNIFIED_ANALYZE_ROUTE] Full success for URL: {url}. Response: {response}")
            return jsonify(response), 200
            
    except Exception as e:
        logger.error(f"[UNIFIED_ANALYZE_ROUTE] Top-level exception in /analyze. Data: {data_for_error_logging}, Error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e) if logger.level <= logging.DEBUG else 'Contact support',
            'results': {},
            'errors': {t: 'Internal server error' for t in data_for_error_logging.get('types', [])} if data_for_error_logging else {},
            'metadata': {
                'total_time_seconds': round(time.time() - start_time, 2),
                'api_version': '2.0.0',
                'error_type': 'internal_error'
            }
        }), 500

@bp.route('/analyze/types', methods=['GET'])
def get_analysis_types():
    """Get available analysis types and their requirements"""
    return jsonify({
        'available': [
            {'type': 'jargon', 'name': 'Επεξήγηση Όρων', 'requires_auth': False, 'category': 'basic'},
            {'type': 'viewpoints', 'name': 'Εναλλακτικές Οπτικές', 'requires_auth': False, 'category': 'basic'},
            {'type': 'fact-check', 'name': 'Έλεγχος Γεγονότων', 'requires_auth': False, 'category': 'verification'},
            {'type': 'bias', 'name': 'Ανάλυση Μεροληψίας', 'requires_auth': False, 'category': 'verification'},
            {'type': 'timeline', 'name': 'Χρονολόγιο', 'requires_auth': True, 'category': 'premium'},
            {'type': 'expert', 'name': 'Απόψεις Ειδικών', 'requires_auth': True, 'category': 'premium'},
            {'type': 'x-pulse', 'name': 'Κοινωνικός Παλμός', 'requires_auth': True, 'category': 'premium'}
        ],
        'free_tier': list(VALID_ANALYSIS_TYPES - PREMIUM_ANALYSES),
        'premium_tier': list(PREMIUM_ANALYSES),
        'categories': {
            'basic': ['jargon', 'viewpoints'],
            'verification': ['fact-check', 'bias'],
            'premium': ['timeline', 'expert', 'x-pulse']
        },
        'limits': {
            'max_types_per_request': 7,
            'max_url_length': 2048
        }
    })

@bp.route('/analyze/health', methods=['GET'])
def health_check():
    """Health check for the analysis API"""
    try:
        # Quick health check
        handler = AnalysisHandler()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'api_version': '2.0.0',
            'available_types': len(VALID_ANALYSIS_TYPES),
            'caching_enabled': handler.coordinator.config.enable_context_caching
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 503

@bp.route('/analyze/stats', methods=['GET'])
@optional_auth
def get_stats(current_user: User = None):
    """Get API usage statistics (admin only for now)"""
    if not current_user or getattr(current_user, 'tier', 'free') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        handler = AnalysisHandler()
        
        # Get basic stats without async call for now
        return jsonify({
            'api_version': '2.0.0',
            'configuration': {
                'caching_enabled': handler.coordinator.config.enable_context_caching,
                'core_timeout': handler.coordinator.config.core_timeout_seconds,
                'on_demand_timeout': handler.coordinator.config.on_demand_timeout_seconds,
                'valid_analysis_types': list(VALID_ANALYSIS_TYPES),
                'premium_types': list(PREMIUM_ANALYSES)
            },
            'note': 'Cache stats require async implementation'
        })
    except Exception as e:
        logger.error(f"Stats endpoint failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve stats'}), 500