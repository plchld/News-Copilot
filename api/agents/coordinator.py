"""Agent Coordinator - Orchestrates multiple agents for parallel execution"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentResult
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
    JARGON = "jargon"
    VIEWPOINTS = "viewpoints"
    FACT_CHECK = "fact-check"
    BIAS = "bias"
    TIMELINE = "timeline"
    EXPERT = "expert"
    X_PULSE = "x-pulse"


@dataclass
class CoordinatorConfig:
    """Configuration for the agent coordinator"""
    max_parallel_agents: int = 4
    enable_streaming: bool = True
    timeout_seconds: int = 300
    retry_failed_agents: bool = True
    cost_limit_per_request: float = 1.0  # Dollar limit


class AgentCoordinator:
    """Coordinates multiple agents for efficient parallel execution"""
    
    def __init__(self, grok_client: Any, config: Optional[CoordinatorConfig] = None):
        self.grok_client = grok_client
        self.config = config or CoordinatorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize all available agents
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[AnalysisType, BaseAgent]:
        """Initialize all available agents"""
        return {
            AnalysisType.JARGON: JargonAgent.create(self.grok_client),
            AnalysisType.VIEWPOINTS: ViewpointsAgent.create(self.grok_client),
            AnalysisType.FACT_CHECK: FactCheckAgent.create(self.grok_client),
            AnalysisType.BIAS: BiasAnalysisAgent.create(self.grok_client),
            AnalysisType.TIMELINE: TimelineAgent.create(self.grok_client),
            AnalysisType.EXPERT: ExpertOpinionsAgent.create(self.grok_client),
            AnalysisType.X_PULSE: XPulseAgent.create(self.grok_client),
        }
    
    async def analyze_article(
        self,
        article_url: str,
        article_text: str,
        analysis_types: List[AnalysisType],
        user_context: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Any] = None
    ) -> Dict[str, AgentResult]:
        """
        Analyze an article using multiple agents in parallel
        
        Args:
            article_url: URL of the article
            article_text: Extracted article text
            analysis_types: List of analysis types to perform
            user_context: Optional user context (tier, preferences, etc.)
            stream_callback: Optional callback for streaming results
            
        Returns:
            Dictionary mapping analysis types to their results
        """
        start_time = datetime.now()
        session_id = f"session_{start_time.strftime('%Y%m%d_%H%M%S')}_{id(self):x}"
        
        self.logger.info(
            f"[COORDINATOR] Starting analysis session {session_id} | "
            f"URL: {article_url[:100]}... | "
            f"Article length: {len(article_text)} chars | "
            f"Requested types: {[t.value for t in analysis_types]} | "
            f"User: {user_context.get('user_id', 'anonymous')} ({user_context.get('tier', 'free') if user_context else 'free'})"
        )
        
        # Build context for all agents
        context = {
            'article_url': article_url,
            'article_text': article_text,
            'user_tier': user_context.get('tier', 'free') if user_context else 'free',
            'user_id': user_context.get('user_id') if user_context else None,
            'session_id': session_id,
            **(user_context or {})
        }
        
        # Validate requested analysis types
        valid_types = [t for t in analysis_types if t in self.agents]
        if len(valid_types) < len(analysis_types):
            invalid = set(analysis_types) - set(valid_types)
            self.logger.warning(
                f"[COORDINATOR] {session_id} - Invalid analysis types requested: {invalid} | "
                f"Valid types: {[t.value for t in valid_types]}"
            )
        
        self.logger.info(
            f"[COORDINATOR] {session_id} - Executing {len(valid_types)} agents | "
            f"Strategy: {'streaming' if self.config.enable_streaming and stream_callback else 'parallel'} | "
            f"Max parallel: {self.config.max_parallel_agents}"
        )
        
        # Execute agents based on strategy
        if self.config.enable_streaming and stream_callback:
            results = await self._execute_streaming(valid_types, context, stream_callback)
        else:
            results = await self._execute_parallel(valid_types, context)
        
        # Log execution summary
        total_time = (datetime.now() - start_time).total_seconds()
        total_tokens = sum(r.tokens_used or 0 for r in results.values())
        total_cost = self._estimate_total_cost(results)
        successful_agents = [t.value for t, r in results.items() if r.success]
        failed_agents = [t.value for t, r in results.items() if not r.success]
        
        self.logger.info(
            f"[COORDINATOR] {session_id} - COMPLETED | "
            f"Duration: {total_time:.2f}s | "
            f"Successful: {len(successful_agents)}/{len(results)} ({successful_agents}) | "
            f"Failed: {len(failed_agents)} ({failed_agents}) | "
            f"Total tokens: {total_tokens} | "
            f"Est. cost: ${total_cost:.4f}"
        )
        
        return results
    
    async def _execute_parallel(
        self,
        analysis_types: List[AnalysisType],
        context: Dict[str, Any]
    ) -> Dict[AnalysisType, AgentResult]:
        """Execute agents in parallel batches"""
        results = {}
        session_id = context.get('session_id', 'unknown')
        
        # Group agents by priority (based on complexity)
        priority_groups = self._group_by_priority(analysis_types)
        
        self.logger.info(
            f"[COORDINATOR] {session_id} - Parallel execution plan: "
            f"{dict((p, [t.value for t in types]) for p, types in priority_groups.items())}"
        )
        
        for priority, types in priority_groups.items():
            batch_start = datetime.now()
            self.logger.info(
                f"[COORDINATOR] {session_id} - Starting priority {priority} batch: "
                f"{[t.value for t in types]} ({len(types)} agents)"
            )
            
            # Execute batch in parallel (respecting max parallel limit)
            batch_tasks = []
            
            for analysis_type in types:
                agent = self.agents[analysis_type]
                task = self._execute_agent_with_retry(agent, context, analysis_type)
                batch_tasks.append((analysis_type, task))
            
            # Wait for batch to complete
            batch_results = {}
            for analysis_type, task in batch_tasks:
                try:
                    result = await task
                    results[analysis_type] = result
                    batch_results[analysis_type.value] = 'SUCCESS' if result.success else f'FAILED: {result.error}'
                except Exception as e:
                    error_msg = str(e)
                    self.logger.error(
                        f"[COORDINATOR] {session_id} - Exception in {analysis_type.value}: {error_msg}"
                    )
                    results[analysis_type] = AgentResult(
                        success=False,
                        error=error_msg,
                        agent_name=analysis_type.value
                    )
                    batch_results[analysis_type.value] = f'EXCEPTION: {error_msg}'
            
            batch_time = (datetime.now() - batch_start).total_seconds()
            self.logger.info(
                f"[COORDINATOR] {session_id} - Priority {priority} batch completed in {batch_time:.2f}s | "
                f"Results: {batch_results}"
            )
        
        return results
    
    async def _execute_streaming(
        self,
        analysis_types: List[AnalysisType],
        context: Dict[str, Any],
        stream_callback: Any
    ) -> Dict[AnalysisType, AgentResult]:
        """Execute agents and stream results as they complete"""
        results = {}
        
        # Create all tasks
        tasks = []
        for analysis_type in analysis_types:
            agent = self.agents[analysis_type]
            task = self._execute_agent_with_retry(agent, context, analysis_type)
            tasks.append((analysis_type, task))
        
        # Process results as they complete
        for analysis_type, task in tasks:
            try:
                result = await task
                results[analysis_type] = result
                
                # Stream the result immediately
                if result.success and stream_callback:
                    await stream_callback(analysis_type, result)
                    
            except Exception as e:
                self.logger.error(f"Failed to execute {analysis_type}: {str(e)}")
                results[analysis_type] = AgentResult(
                    success=False,
                    error=str(e),
                    agent_name=analysis_type.value
                )
        
        return results
    
    async def _execute_agent_with_retry(
        self,
        agent: BaseAgent,
        context: Dict[str, Any],
        analysis_type: AnalysisType
    ) -> AgentResult:
        """Execute an agent with retry logic"""
        max_retries = 3 if self.config.retry_failed_agents else 1
        session_id = context.get('session_id', 'unknown')
        agent_start = datetime.now()
        
        self.logger.info(
            f"[AGENT] {session_id} - Starting {analysis_type.value} agent | "
            f"Max retries: {max_retries} | "
            f"Default model: {agent.config.default_model.value} | "
            f"Complexity: {agent.config.complexity.name}"
        )
        
        for attempt in range(max_retries):
            attempt_start = datetime.now()
            try:
                # Add retry count to context for model selection
                retry_context = {**context, 'retry_count': attempt}
                
                self.logger.info(
                    f"[AGENT] {session_id} - {analysis_type.value} attempt {attempt + 1}/{max_retries} | "
                    f"Context: user_tier={retry_context.get('user_tier')}, "
                    f"article_length={len(retry_context.get('article_text', ''))}, "
                    f"retry_count={attempt}"
                )
                
                # Execute agent
                result = await agent.execute(retry_context)
                
                attempt_time = (datetime.now() - attempt_start).total_seconds()
                
                if result.success:
                    total_time = (datetime.now() - agent_start).total_seconds()
                    self.logger.info(
                        f"[AGENT] {session_id} - {analysis_type.value} SUCCESS | "
                        f"Attempt: {attempt + 1}/{max_retries} | "
                        f"Attempt time: {attempt_time:.2f}s | "
                        f"Total time: {total_time:.2f}s | "
                        f"Model used: {result.model_used.value if result.model_used else 'unknown'} | "
                        f"Tokens: {result.tokens_used or 0} | "
                        f"Data keys: {list(result.data.keys()) if result.data else []}"
                    )
                    return result
                
                # Log failure and potentially retry
                self.logger.warning(
                    f"[AGENT] {session_id} - {analysis_type.value} FAILED attempt {attempt + 1} | "
                    f"Time: {attempt_time:.2f}s | "
                    f"Error: {result.error} | "
                    f"Model: {result.model_used.value if result.model_used else 'unknown'}"
                )
                
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    self.logger.info(
                        f"[AGENT] {session_id} - {analysis_type.value} retrying in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)  # Exponential backoff
                
            except Exception as e:
                attempt_time = (datetime.now() - attempt_start).total_seconds()
                error_msg = str(e)
                
                self.logger.error(
                    f"[AGENT] {session_id} - {analysis_type.value} EXCEPTION attempt {attempt + 1} | "
                    f"Time: {attempt_time:.2f}s | "
                    f"Error: {error_msg}"
                )
                
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    self.logger.info(
                        f"[AGENT] {session_id} - {analysis_type.value} retrying after exception in {backoff_time}s..."
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    raise
        
        # All retries failed
        total_time = (datetime.now() - agent_start).total_seconds()
        final_error = f"Failed after {max_retries} attempts"
        
        self.logger.error(
            f"[AGENT] {session_id} - {analysis_type.value} EXHAUSTED RETRIES | "
            f"Total time: {total_time:.2f}s | "
            f"Final error: {final_error}"
        )
        
        return AgentResult(
            success=False,
            error=final_error,
            agent_name=analysis_type.value
        )
    
    def _group_by_priority(self, analysis_types: List[AnalysisType]) -> Dict[int, List[AnalysisType]]:
        """Group analysis types by execution priority"""
        # Priority based on dependencies and complexity
        priority_map = {
            AnalysisType.JARGON: 1,  # Simple, can run first
            AnalysisType.TIMELINE: 1,  # Independent
            AnalysisType.VIEWPOINTS: 2,  # Needs search
            AnalysisType.FACT_CHECK: 2,  # Needs search
            AnalysisType.EXPERT: 2,  # Needs search
            AnalysisType.BIAS: 3,  # Complex reasoning
            AnalysisType.X_PULSE: 3,  # Most complex with sub-agents
        }
        
        groups = {}
        for analysis_type in analysis_types:
            priority = priority_map.get(analysis_type, 2)
            if priority not in groups:
                groups[priority] = []
            groups[priority].append(analysis_type)
        
        return dict(sorted(groups.items()))
    
    def _estimate_total_cost(self, results: Dict[AnalysisType, AgentResult]) -> float:
        """Estimate total cost of all agent executions"""
        total_cost = 0.0
        
        for result in results.values():
            if result.tokens_used and result.model_used:
                # Rough cost estimates per 1K tokens
                cost_per_1k = {
                    'grok-3-mini': 0.01,
                    'grok-3': 0.025
                }
                model_name = result.model_used.value if hasattr(result.model_used, 'value') else str(result.model_used)
                rate = cost_per_1k.get(model_name, 0.01)
                total_cost += (result.tokens_used / 1000) * rate
        
        return total_cost
    
    async def analyze_single(
        self,
        article_url: str,
        article_text: str,
        analysis_type: AnalysisType,
        user_context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Analyze using a single agent (for backward compatibility)"""
        results = await self.analyze_article(
            article_url=article_url,
            article_text=article_text,
            analysis_types=[analysis_type],
            user_context=user_context
        )
        return results.get(analysis_type, AgentResult(
            success=False,
            error="Analysis type not found",
            agent_name=analysis_type.value
        ))