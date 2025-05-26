"""
Optimized API Endpoints for User-Driven Analysis Architecture
Supports core analysis (immediate) and on-demand analysis (user-triggered)
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .agents.optimized_coordinator import OptimizedAgentCoordinator, OptimizedCoordinatorConfig
from .grok_client import GrokClient


logger = logging.getLogger(__name__)


# Request/Response Models
class CoreAnalysisRequest(BaseModel):
    """Request for core analysis (jargon + viewpoints)"""
    article_url: str = Field(..., description="URL of the article to analyze")
    article_text: str = Field(..., description="Extracted article text")
    user_id: Optional[str] = Field(None, description="User identifier")
    user_tier: str = Field("free", description="User tier (free/premium/admin)")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class OnDemandAnalysisRequest(BaseModel):
    """Request for on-demand analysis"""
    session_id: str = Field(..., description="Session ID from core analysis")
    user_id: Optional[str] = Field(None, description="User identifier")
    user_tier: str = Field("free", description="User tier (free/premium/admin)")


class CoreAnalysisResponse(BaseModel):
    """Response for core analysis"""
    session_id: str
    success: bool
    results: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]
    errors: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OnDemandAnalysisResponse(BaseModel):
    """Response for on-demand analysis"""
    session_id: str
    analysis_type: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any]
    requires_core_analysis: Optional[bool] = None


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    cached_sessions: int
    cache_size_mb: float
    config: Dict[str, Any]


# Global coordinator instance
coordinator: Optional[OptimizedAgentCoordinator] = None


def get_coordinator() -> OptimizedAgentCoordinator:
    """Get the global coordinator instance"""
    global coordinator
    if coordinator is None:
        # Initialize with default config
        grok_client = GrokClient()
        config = OptimizedCoordinatorConfig(
            core_timeout_seconds=30,
            on_demand_timeout_seconds=120,
            cache_ttl_minutes=60,
            enable_result_caching=True,
            enable_context_caching=True
        )
        coordinator = OptimizedAgentCoordinator(grok_client, config)
    return coordinator


# API Endpoints
app = FastAPI(title="News-Copilot Optimized API", version="2.0.0")


@app.post("/analyze/core", response_model=CoreAnalysisResponse)
async def analyze_core(
    request: CoreAnalysisRequest,
    coordinator: OptimizedAgentCoordinator = Depends(get_coordinator)
) -> CoreAnalysisResponse:
    """
    Execute core analysis (jargon + viewpoints) immediately.
    This is the first call users make when clicking "Analyze".
    Results are cached for subsequent on-demand requests.
    """
    start_time = datetime.now()
    
    logger.info(
        f"[API] Core analysis request | "
        f"URL: {request.article_url[:100]}... | "
        f"User: {request.user_id or 'anonymous'} ({request.user_tier}) | "
        f"Article length: {len(request.article_text)} chars"
    )
    
    try:
        # Build user context
        user_context = {
            'user_id': request.user_id,
            'user_tier': request.user_tier,
            'session_id': request.session_id,
            'api_endpoint': 'core_analysis',
            'request_timestamp': start_time.isoformat()
        }
        
        # Execute core analysis
        result = await coordinator.analyze_core(
            article_url=request.article_url,
            article_text=request.article_text,
            user_context=user_context
        )
        
        # Log completion
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[API] Core analysis completed | "
            f"Session: {result.get('session_id')} | "
            f"Success: {result.get('success')} | "
            f"Duration: {execution_time:.2f}s"
        )
        
        return CoreAnalysisResponse(**result)
        
    except Exception as e:
        error_msg = f"Core analysis failed: {str(e)}"
        logger.error(f"[API] {error_msg}")
        
        return CoreAnalysisResponse(
            session_id=request.session_id or "error",
            success=False,
            error=error_msg,
            metadata={
                'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                'api_error': True
            }
        )


@app.post("/analyze/on-demand/{analysis_type}", response_model=OnDemandAnalysisResponse)
async def analyze_on_demand(
    analysis_type: str,
    request: OnDemandAnalysisRequest,
    coordinator: OptimizedAgentCoordinator = Depends(get_coordinator)
) -> OnDemandAnalysisResponse:
    """
    Execute on-demand analysis for specific features.
    Requires a valid session_id from previous core analysis.
    
    Available analysis types:
    - fact-check: Fact checking and verification
    - bias: Political bias analysis
    - timeline: Timeline and chronology
    - expert: Expert opinions and analysis
    - x-pulse: X/Twitter discourse analysis
    """
    start_time = datetime.now()
    
    logger.info(
        f"[API] On-demand analysis request | "
        f"Type: {analysis_type} | "
        f"Session: {request.session_id} | "
        f"User: {request.user_id or 'anonymous'} ({request.user_tier})"
    )
    
    try:
        # Validate analysis type
        valid_types = ['fact-check', 'bias', 'timeline', 'expert', 'x-pulse']
        if analysis_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type '{analysis_type}'. Valid types: {valid_types}"
            )
        
        # Build user context
        user_context = {
            'user_id': request.user_id,
            'user_tier': request.user_tier,
            'api_endpoint': 'on_demand_analysis',
            'request_timestamp': start_time.isoformat()
        }
        
        # Execute on-demand analysis
        result = await coordinator.analyze_on_demand(
            analysis_type=analysis_type,
            session_id=request.session_id,
            user_context=user_context
        )
        
        # Log completion
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[API] On-demand analysis completed | "
            f"Type: {analysis_type} | "
            f"Session: {request.session_id} | "
            f"Success: {result.get('success')} | "
            f"Duration: {execution_time:.2f}s"
        )
        
        return OnDemandAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"On-demand analysis failed: {str(e)}"
        logger.error(f"[API] {error_msg}")
        
        return OnDemandAnalysisResponse(
            session_id=request.session_id,
            analysis_type=analysis_type,
            success=False,
            error=error_msg,
            metadata={
                'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                'api_error': True
            }
        )


@app.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    coordinator: OptimizedAgentCoordinator = Depends(get_coordinator)
) -> CacheStatsResponse:
    """
    Get cache statistics for monitoring and debugging.
    Useful for understanding system performance and resource usage.
    """
    try:
        stats = await coordinator.get_cache_stats()
        return CacheStatsResponse(**stats)
    except Exception as e:
        logger.error(f"[API] Failed to get cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")


@app.delete("/cache/session/{session_id}")
async def clear_session_cache(
    session_id: str,
    coordinator: OptimizedAgentCoordinator = Depends(get_coordinator)
) -> Dict[str, str]:
    """
    Clear cache for a specific session.
    Useful for testing or when users want to start fresh.
    """
    try:
        # Access the cache directly to clear session
        await coordinator.cache._remove_session_cache(session_id)
        
        logger.info(f"[API] Cleared cache for session {session_id}")
        return {"message": f"Cache cleared for session {session_id}"}
        
    except Exception as e:
        logger.error(f"[API] Failed to clear cache for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session cache")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring system status.
    """
    try:
        coordinator = get_coordinator()
        cache_stats = await coordinator.get_cache_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cache_sessions": cache_stats["cached_sessions"],
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"[API] Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Legacy endpoint for backward compatibility
@app.post("/analyze")
async def analyze_legacy(
    request: CoreAnalysisRequest,
    coordinator: OptimizedAgentCoordinator = Depends(get_coordinator)
) -> Dict[str, Any]:
    """
    Legacy endpoint for backward compatibility.
    Redirects to core analysis but includes a migration notice.
    """
    logger.warning(
        f"[API] Legacy endpoint used | "
        f"User: {request.user_id or 'anonymous'} | "
        f"Consider migrating to /analyze/core"
    )
    
    # Execute core analysis
    result = await analyze_core(request, coordinator)
    
    # Add migration notice
    result_dict = result.dict()
    result_dict['migration_notice'] = {
        'message': 'This endpoint is deprecated. Use /analyze/core for core analysis and /analyze/on-demand/{type} for specific features.',
        'new_endpoints': {
            'core_analysis': '/analyze/core',
            'on_demand_analysis': '/analyze/on-demand/{analysis_type}'
        }
    }
    
    return result_dict


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"[API] HTTP Exception: {exc.status_code} - {exc.detail}")
    return {"error": exc.detail, "status_code": exc.status_code}


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"[API] Unhandled exception: {str(exc)}")
    return {"error": "Internal server error", "status_code": 500}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the coordinator on startup"""
    global coordinator
    logger.info("[API] Starting optimized News-Copilot API v2.0.0")
    
    # Initialize coordinator
    coordinator = get_coordinator()
    
    logger.info(
        f"[API] Coordinator initialized | "
        f"Core timeout: {coordinator.config.core_timeout_seconds}s | "
        f"On-demand timeout: {coordinator.config.on_demand_timeout_seconds}s | "
        f"Cache TTL: {coordinator.config.cache_ttl_minutes}min"
    )


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("[API] Shutting down optimized News-Copilot API")
    
    if coordinator:
        # Could add cleanup logic here if needed
        pass 