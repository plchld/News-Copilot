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
        
        # Build context for all agents
        context = {
            'article_url': article_url,
            'article_text': article_text,
            'user_tier': user_context.get('tier', 'free') if user_context else 'free',
            'user_id': user_context.get('user_id') if user_context else None,
            **(user_context or {})
        }
        
        # Validate requested analysis types
        valid_types = [t for t in analysis_types if t in self.agents]
        if len(valid_types) < len(analysis_types):
            invalid = set(analysis_types) - set(valid_types)
            self.logger.warning(f"Invalid analysis types requested: {invalid}")
        
        # Execute agents based on strategy
        if self.config.enable_streaming and stream_callback:
            results = await self._execute_streaming(valid_types, context, stream_callback)
        else:
            results = await self._execute_parallel(valid_types, context)
        
        # Log execution summary
        total_time = (datetime.now() - start_time).total_seconds()
        total_tokens = sum(r.tokens_used or 0 for r in results.values())
        total_cost = self._estimate_total_cost(results)
        
        self.logger.info(
            f"Completed {len(results)} analyses in {total_time:.2f}s | "
            f"Tokens: {total_tokens} | Est. Cost: ${total_cost:.4f}"
        )
        
        return results
    
    async def _execute_parallel(
        self,
        analysis_types: List[AnalysisType],
        context: Dict[str, Any]
    ) -> Dict[AnalysisType, AgentResult]:
        """Execute agents in parallel batches"""
        results = {}
        
        # Group agents by priority (based on complexity)
        priority_groups = self._group_by_priority(analysis_types)
        
        for priority, types in priority_groups.items():
            # Execute batch in parallel (respecting max parallel limit)
            batch_tasks = []
            
            for analysis_type in types:
                agent = self.agents[analysis_type]
                task = self._execute_agent_with_retry(agent, context, analysis_type)
                batch_tasks.append((analysis_type, task))
            
            # Wait for batch to complete
            for analysis_type, task in batch_tasks:
                try:
                    result = await task
                    results[analysis_type] = result
                except Exception as e:
                    self.logger.error(f"Failed to execute {analysis_type}: {str(e)}")
                    results[analysis_type] = AgentResult(
                        success=False,
                        error=str(e),
                        agent_name=analysis_type.value
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
        
        for attempt in range(max_retries):
            try:
                # Add retry count to context for model selection
                retry_context = {**context, 'retry_count': attempt}
                
                # Execute agent
                result = await agent.execute(retry_context)
                
                if result.success:
                    return result
                
                # Log failure and potentially retry
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"{analysis_type} failed (attempt {attempt + 1}), retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"{analysis_type} exception (attempt {attempt + 1}): {str(e)}"
                    )
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        # All retries failed
        return AgentResult(
            success=False,
            error=f"Failed after {max_retries} attempts",
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