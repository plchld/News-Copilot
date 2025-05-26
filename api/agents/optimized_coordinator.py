"""
Optimized Agent Coordinator - User-Driven Analysis Architecture
Splits core analysis (immediate) from on-demand analysis (user-triggered)
"""

import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

from .base_agent import BaseAgent, AgentResult, ModelType
from .jargon_agent import JargonAgent
from .viewpoints_agent import ViewpointsAgent
from .fact_check_agent import FactCheckAgent
from .bias_agent import BiasAnalysisAgent
from .timeline_agent import TimelineAgent
from .expert_agent import ExpertOpinionsAgent
from .x_pulse_agent import XPulseAgent


logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Available analysis types"""
    # Core analysis (immediate)
    JARGON = "jargon"
    VIEWPOINTS = "viewpoints"
    
    # On-demand analysis (user-triggered)
    FACT_CHECK = "fact-check"
    BIAS = "bias"
    TIMELINE = "timeline"
    EXPERT = "expert"
    X_PULSE = "x-pulse"


class RequestType(Enum):
    """Request types for different execution paths"""
    CORE_ANALYSIS = "core_analysis"
    ON_DEMAND = "on_demand"


@dataclass
class OptimizedCoordinatorConfig:
    """Configuration for optimized coordinator"""
    # Core analysis settings
    core_parallel_limit: int = 2  # Only jargon + viewpoints
    core_timeout_seconds: int = 30
    
    # On-demand settings
    on_demand_timeout_seconds: int = 120
    
    # Caching settings
    cache_ttl_minutes: int = 60
    max_cache_size: int = 1000
    
    # Performance settings
    enable_result_caching: bool = True
    enable_context_caching: bool = True


class AnalysisCache:
    """Intelligent caching for analysis results and context"""
    
    def __init__(self, config: OptimizedCoordinatorConfig):
        self.config = config
        self.core_results = {}      # session_id -> core results
        self.article_contexts = {}  # session_id -> processed article data
        self.user_sessions = {}     # session_id -> user session data
        self.cache_timestamps = {}  # session_id -> timestamp
        
    async def store_core_analysis(self, session_id: str, results: Dict[str, AgentResult], 
                                 article_context: Dict[str, Any]) -> None:
        """Store core analysis results and article context"""
        if not self.config.enable_result_caching:
            return
            
        timestamp = datetime.now()
        
        # Store core results
        self.core_results[session_id] = {
            'jargon': results.get('jargon'),
            'viewpoints': results.get('viewpoints'),
            'timestamp': timestamp
        }
        
        # Store enhanced article context for on-demand use
        self.article_contexts[session_id] = {
            'article_text': article_context.get('article_text'),
            'article_url': article_context.get('article_url'),
            'user_tier': article_context.get('user_tier'),
            'user_id': article_context.get('user_id'),
            'session_id': session_id,
            'core_analysis_completed': True,
            'core_results_summary': self._extract_core_summary(results),
            'timestamp': timestamp
        }
        
        self.cache_timestamps[session_id] = timestamp
        
        # Clean old cache entries
        await self._cleanup_expired_cache()
        
        logger.info(
            f"[CACHE] Stored core analysis for session {session_id} | "
            f"Cache size: {len(self.core_results)} sessions"
        )
    
    async def get_enhanced_context(self, session_id: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        """Get enhanced context for on-demand analysis"""
        if not self.config.enable_context_caching:
            return None
            
        # Check if we have cached context
        if session_id not in self.article_contexts:
            logger.warning(f"[CACHE] No cached context found for session {session_id}")
            return None
        
        # Check cache expiry
        if await self._is_cache_expired(session_id):
            logger.warning(f"[CACHE] Cached context expired for session {session_id}")
            await self._remove_session_cache(session_id)
            return None
        
        base_context = self.article_contexts[session_id].copy()
        
        # Add analysis-specific enhancements
        base_context.update({
            'request_type': RequestType.ON_DEMAND.value,
            'analysis_type': analysis_type,
            'has_core_results': True,
            'core_results': self.core_results.get(session_id, {}),
            'cache_hit': True
        })
        
        logger.info(
            f"[CACHE] Retrieved enhanced context for session {session_id} | "
            f"Analysis: {analysis_type} | "
            f"Cache age: {(datetime.now() - base_context['timestamp']).total_seconds():.1f}s"
        )
        
        return base_context
    
    def _extract_core_summary(self, results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Extract summary from core results for context enhancement"""
        summary = {}
        
        if 'jargon' in results and results['jargon'].success:
            jargon_data = results['jargon'].data or {}
            summary['simplified_terms'] = jargon_data.get('simplified_terms', [])
            summary['key_concepts'] = [term.get('term', '') for term in summary['simplified_terms'][:5]]
        
        if 'viewpoints' in results and results['viewpoints'].success:
            viewpoints_data = results['viewpoints'].data or {}
            summary['main_perspectives'] = viewpoints_data.get('perspectives', [])
            summary['stakeholder_groups'] = [p.get('stakeholder', '') for p in summary['main_perspectives'][:3]]
        
        return summary
    
    async def _is_cache_expired(self, session_id: str) -> bool:
        """Check if cache entry is expired"""
        if session_id not in self.cache_timestamps:
            return True
        
        cache_time = self.cache_timestamps[session_id]
        expiry_time = cache_time + timedelta(minutes=self.config.cache_ttl_minutes)
        return datetime.now() > expiry_time
    
    async def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > timedelta(minutes=self.config.cache_ttl_minutes):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self._remove_session_cache(session_id)
        
        if expired_sessions:
            logger.info(f"[CACHE] Cleaned up {len(expired_sessions)} expired cache entries")
    
    async def _remove_session_cache(self, session_id: str) -> None:
        """Remove all cache entries for a session"""
        self.core_results.pop(session_id, None)
        self.article_contexts.pop(session_id, None)
        self.cache_timestamps.pop(session_id, None)


class CoreAnalysisCoordinator:
    """Handles immediate jargon + viewpoints analysis"""
    
    def __init__(self, grok_client: Any, cache: AnalysisCache, 
                 config: OptimizedCoordinatorConfig):
        self.grok_client = grok_client
        self.cache = cache
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.CoreCoordinator")
        
        # Initialize core agents
        self.core_agents = {
            AnalysisType.JARGON: JargonAgent.create(grok_client),
            AnalysisType.VIEWPOINTS: ViewpointsAgent.create(grok_client)
        }
    
    async def execute_core_analysis(
        self,
        article_url: str,
        article_text: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute core analysis (jargon + viewpoints) in parallel"""
        start_time = datetime.now()
        session_id = user_context.get('session_id') or f"core_{start_time.strftime('%Y%m%d_%H%M%S')}_{id(self):x}"
        
        self.logger.info(
            f"[CORE_ANALYSIS] Starting session {session_id} | "
            f"URL: {article_url[:100]}... | "
            f"Article length: {len(article_text)} chars | "
            f"User: {user_context.get('user_id', 'anonymous')} ({user_context.get('user_tier', 'free')})"
        )
        
        # Build context for core analysis
        context = {
            'article_url': article_url,
            'article_text': article_text,
            'session_id': session_id,
            'request_type': RequestType.CORE_ANALYSIS.value,
            'user_tier': user_context.get('user_tier', 'free'),
            'user_id': user_context.get('user_id'),
            **user_context
        }
        
        try:
            # Execute jargon and viewpoints in parallel with timeout
            jargon_task = self.core_agents[AnalysisType.JARGON].execute(context)
            viewpoints_task = self.core_agents[AnalysisType.VIEWPOINTS].execute(context)
            
            self.logger.info(f"[CORE_ANALYSIS] {session_id} - Executing jargon + viewpoints in parallel")
            
            # Use timeout for core analysis
            jargon_result, viewpoints_result = await asyncio.wait_for(
                asyncio.gather(jargon_task, viewpoints_task),
                timeout=self.config.core_timeout_seconds
            )
            
            # Prepare results
            results = {
                'jargon': jargon_result,
                'viewpoints': viewpoints_result
            }
            
            # Cache results for future on-demand requests
            await self.cache.store_core_analysis(session_id, results, context)
            
            # Calculate execution metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            total_tokens = sum(r.tokens_used or 0 for r in results.values())
            success_count = sum(1 for r in results.values() if r.success)
            
            self.logger.info(
                f"[CORE_ANALYSIS] {session_id} - COMPLETED | "
                f"Duration: {execution_time:.2f}s | "
                f"Success: {success_count}/2 | "
                f"Tokens: {total_tokens}"
            )
            
            # Return structured response
            return {
                'session_id': session_id,
                'success': success_count > 0,
                'results': {
                    'jargon': results['jargon'].data if results['jargon'].success else None,
                    'viewpoints': results['viewpoints'].data if results['viewpoints'].success else None
                },
                'metadata': {
                    'execution_time_seconds': execution_time,
                    'total_tokens_used': total_tokens,
                    'successful_analyses': success_count,
                    'failed_analyses': 2 - success_count,
                    'cached_for_on_demand': True
                },
                'errors': {
                    'jargon': results['jargon'].error if not results['jargon'].success else None,
                    'viewpoints': results['viewpoints'].error if not results['viewpoints'].success else None
                }
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Core analysis timed out after {self.config.core_timeout_seconds} seconds"
            self.logger.error(f"[CORE_ANALYSIS] {session_id} - {error_msg}")
            
            return {
                'session_id': session_id,
                'success': False,
                'error': error_msg,
                'metadata': {
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'timeout_occurred': True
                }
            }
            
        except Exception as e:
            error_msg = f"Core analysis failed: {str(e)}"
            self.logger.error(f"[CORE_ANALYSIS] {session_id} - {error_msg}")
            
            return {
                'session_id': session_id,
                'success': False,
                'error': error_msg,
                'metadata': {
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'exception_occurred': True
                }
            }


class OnDemandCoordinator:
    """Handles user-triggered specific analyses"""
    
    def __init__(self, grok_client: Any, cache: AnalysisCache, 
                 config: OptimizedCoordinatorConfig):
        self.grok_client = grok_client
        self.cache = cache
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.OnDemandCoordinator")
        
        # Initialize on-demand agents
        self.on_demand_agents = {
            AnalysisType.FACT_CHECK: FactCheckAgent.create(grok_client),
            AnalysisType.BIAS: BiasAnalysisAgent.create(grok_client),
            AnalysisType.TIMELINE: TimelineAgent.create(grok_client),
            AnalysisType.EXPERT: ExpertOpinionsAgent.create(grok_client),
            AnalysisType.X_PULSE: XPulseAgent.create(grok_client)
        }
    
    async def execute_on_demand(
        self,
        analysis_type: str,
        session_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute specific on-demand analysis"""
        start_time = datetime.now()
        
        try:
            # Validate analysis type
            analysis_enum = AnalysisType(analysis_type)
        except ValueError:
            error_msg = f"Invalid analysis type: {analysis_type}"
            self.logger.error(f"[ON_DEMAND] {session_id} - {error_msg}")
            return {'success': False, 'error': error_msg}
        
        self.logger.info(
            f"[ON_DEMAND] Starting {analysis_type} for session {session_id} | "
            f"User: {user_context.get('user_id', 'anonymous') if user_context else 'anonymous'}"
        )
        
        # Get enhanced context from cache
        enhanced_context = await self.cache.get_enhanced_context(session_id, analysis_type)
        
        if not enhanced_context:
            error_msg = f"No cached context found for session {session_id}. Please run core analysis first."
            self.logger.error(f"[ON_DEMAND] {session_id} - {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'requires_core_analysis': True
            }
        
        # Add user context if provided
        if user_context:
            enhanced_context.update(user_context)
        
        try:
            # Execute the specific agent
            agent = self.on_demand_agents[analysis_enum]
            
            self.logger.info(
                f"[ON_DEMAND] {session_id} - Executing {analysis_type} agent | "
                f"Cache hit: {enhanced_context.get('cache_hit', False)}"
            )
            
            # Execute with timeout
            result = await asyncio.wait_for(
                agent.execute(enhanced_context),
                timeout=self.config.on_demand_timeout_seconds
            )
            
            # Calculate execution metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"[ON_DEMAND] {session_id} - {analysis_type} COMPLETED | "
                f"Duration: {execution_time:.2f}s | "
                f"Success: {result.success} | "
                f"Tokens: {result.tokens_used or 0}"
            )
            
            return {
                'session_id': session_id,
                'analysis_type': analysis_type,
                'success': result.success,
                'result': result.data if result.success else None,
                'error': result.error if not result.success else None,
                'metadata': {
                    'execution_time_seconds': execution_time,
                    'tokens_used': result.tokens_used or 0,
                    'model_used': result.model_used.value if result.model_used else None,
                    'cache_hit': enhanced_context.get('cache_hit', False)
                }
            }
            
        except asyncio.TimeoutError:
            error_msg = f"{analysis_type} analysis timed out after {self.config.on_demand_timeout_seconds} seconds"
            self.logger.error(f"[ON_DEMAND] {session_id} - {error_msg}")
            
            return {
                'session_id': session_id,
                'analysis_type': analysis_type,
                'success': False,
                'error': error_msg,
                'metadata': {
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'timeout_occurred': True
                }
            }
            
        except Exception as e:
            error_msg = f"{analysis_type} analysis failed: {str(e)}"
            self.logger.error(f"[ON_DEMAND] {session_id} - {error_msg}")
            
            return {
                'session_id': session_id,
                'analysis_type': analysis_type,
                'success': False,
                'error': error_msg,
                'metadata': {
                    'execution_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'exception_occurred': True
                }
            }


class OptimizedAgentCoordinator:
    """Main coordinator that orchestrates core and on-demand analysis"""
    
    def __init__(self, grok_client: Any, config: Optional[OptimizedCoordinatorConfig] = None):
        self.grok_client = grok_client
        self.config = config or OptimizedCoordinatorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache and coordinators
        self.cache = AnalysisCache(self.config)
        self.core_coordinator = CoreAnalysisCoordinator(grok_client, self.cache, self.config)
        self.on_demand_coordinator = OnDemandCoordinator(grok_client, self.cache, self.config)
    
    async def analyze_core(
        self,
        article_url: str,
        article_text: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute core analysis (jargon + viewpoints)"""
        return await self.core_coordinator.execute_core_analysis(
            article_url, article_text, user_context or {}
        )
    
    async def analyze_on_demand(
        self,
        analysis_type: str,
        session_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute on-demand analysis"""
        return await self.on_demand_coordinator.execute_on_demand(
            analysis_type, session_id, user_context
        )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return {
            'cached_sessions': len(self.cache.core_results),
            'cache_size_mb': self._estimate_cache_size(),
            'config': {
                'cache_ttl_minutes': self.config.cache_ttl_minutes,
                'max_cache_size': self.config.max_cache_size,
                'caching_enabled': self.config.enable_result_caching
            }
        }
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB"""
        # Rough estimation - would need more sophisticated calculation in production
        total_items = (
            len(self.cache.core_results) + 
            len(self.cache.article_contexts) + 
            len(self.cache.user_sessions)
        )
        return total_items * 0.1  # Rough estimate: 100KB per cached item 