"""
Agent Coordinator for Django
Orchestrates all analysis agents
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import AgentResult, BaseAgent
from .jargon_agent import JargonAgent
from .viewpoints_agent import ViewpointsAgent
from .fact_check_agent import FactCheckAgent
from .timeline_agent import TimelineAgent

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Coordinates multiple analysis agents"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.agents = self._initialize_agents()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all available agents"""
        return {
            'jargon': JargonAgent(),
            'viewpoints': ViewpointsAgent(),
            'fact_check': FactCheckAgent(),
            'timeline': TimelineAgent(),
        }
    
    async def analyze_article(
        self,
        article_content: str,
        article_id: Optional[str] = None,
        analysis_types: List[str] = None
    ) -> Dict[str, AgentResult]:
        """
        Run analysis agents on article content
        
        Args:
            article_content: The article text to analyze
            article_id: Optional article ID for caching
            analysis_types: List of analysis types to run (default: all)
            
        Returns:
            Dictionary mapping agent names to their results
        """
        start_time = datetime.now()
        
        # Determine which agents to run
        if analysis_types is None or 'all' in analysis_types:
            agents_to_run = self.agents
        else:
            agents_to_run = {
                name: agent 
                for name, agent in self.agents.items() 
                if name in analysis_types
            }
        
        logger.info(f"Running {len(agents_to_run)} agents on article {article_id or 'unknown'}")
        
        # Create tasks for each agent
        tasks = []
        for name, agent in agents_to_run.items():
            task = self._run_agent_with_semaphore(
                agent, 
                article_content, 
                article_id=article_id
            )
            tasks.append((name, task))
        
        # Run all agents concurrently
        results = {}
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                
                if result.success:
                    logger.info(f"Agent {name} completed successfully")
                else:
                    logger.error(f"Agent {name} failed: {result.error}")
                    
            except Exception as e:
                logger.error(f"Unexpected error running agent {name}: {str(e)}")
                results[name] = AgentResult(
                    success=False,
                    error=str(e),
                    agent_name=name
                )
        
        # Log summary
        total_time = (datetime.now() - start_time).total_seconds()
        successful = sum(1 for r in results.values() if r.success)
        logger.info(
            f"Analysis completed in {total_time:.2f}s - "
            f"{successful}/{len(results)} agents successful"
        )
        
        return results
    
    async def _run_agent_with_semaphore(
        self,
        agent: BaseAgent,
        article_content: str,
        **kwargs
    ) -> AgentResult:
        """Run a single agent with semaphore control"""
        async with self.semaphore:
            return await agent.execute_with_monitoring(article_content, **kwargs)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agents.keys())
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all agents"""
        return {
            name: agent.config.description
            for name, agent in self.agents.items()
        }