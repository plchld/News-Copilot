"""
News Agent Coordinator - Orchestrates all AI agents for news analysis
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.jargon_agent import JargonAgent
from agents.viewpoints_agent import ViewpointsAgent
from agents.fact_check_agent import FactCheckAgent
from agents.bias_agent import BiasAnalysisAgent
from agents.timeline_agent import TimelineAgent
from agents.expert_agent import ExpertOpinionsAgent
from config.config import XAI_API_KEY, AGENT_CONFIG


@dataclass
class AnalysisResult:
    """Result from an agent analysis"""
    agent_name: str
    status: str  # 'success', 'error', 'timeout'
    data: Dict[str, Any]
    duration: float
    error_message: Optional[str] = None


class NewsAgentCoordinator:
    """Coordinates all news analysis agents"""
    
    def __init__(self):
        self.api_key = XAI_API_KEY
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all analysis agents"""
        if not self.api_key:
            raise ValueError("XAI_API_KEY not configured")
        
        # Import GrokClient
        from core.grok_client import GrokClient
        grok_client = GrokClient()
            
        return {
            "jargon": JargonAgent.create(grok_client),
            "viewpoints": ViewpointsAgent.create(grok_client),
            "fact_check": FactCheckAgent.create(grok_client),
            "bias": BiasAnalysisAgent.create(grok_client),
            "timeline": TimelineAgent.create(grok_client),
            "expert": ExpertOpinionsAgent.create(grok_client)
        }
    
    async def analyze_article_full(self, content: str, url: str) -> Dict[str, AnalysisResult]:
        """
        Run full analysis with all agents
        
        Args:
            content: Article content
            url: Article URL
            
        Returns:
            Dictionary of analysis results by agent name
        """
        print(f"[Coordinator] Starting full analysis for article...")
        start_time = datetime.now()
        
        # Create analysis tasks
        tasks = {}
        for agent_name, agent in self.agents.items():
            task = asyncio.create_task(
                self._run_agent_analysis(agent, agent_name, content, url)
            )
            tasks[agent_name] = task
        
        # Wait for all analyses to complete
        results = {}
        for agent_name, task in tasks.items():
            try:
                result = await task
                results[agent_name] = result
                status = "✓" if result.status == "success" else "✗"
                print(f"[Coordinator] {status} {agent_name}: {result.duration:.1f}s")
            except Exception as e:
                results[agent_name] = AnalysisResult(
                    agent_name=agent_name,
                    status="error",
                    data={},
                    duration=0,
                    error_message=str(e)
                )
                print(f"[Coordinator] ✗ {agent_name}: {str(e)}")
        
        total_duration = (datetime.now() - start_time).total_seconds()
        print(f"[Coordinator] Full analysis completed in {total_duration:.1f}s")
        
        return results
    
    async def analyze_article_subset(self, content: str, url: str, 
                                   agent_names: List[str]) -> Dict[str, AnalysisResult]:
        """
        Run analysis with specific agents only
        
        Args:
            content: Article content
            url: Article URL
            agent_names: List of agent names to run
            
        Returns:
            Dictionary of analysis results
        """
        print(f"[Coordinator] Starting subset analysis: {agent_names}")
        
        # Filter agents
        available_agents = {name: agent for name, agent in self.agents.items() 
                          if name in agent_names}
        
        if not available_agents:
            raise ValueError(f"No valid agents found in: {agent_names}")
        
        # Create tasks
        tasks = {}
        for agent_name, agent in available_agents.items():
            task = asyncio.create_task(
                self._run_agent_analysis(agent, agent_name, content, url)
            )
            tasks[agent_name] = task
        
        # Wait for completion
        results = {}
        for agent_name, task in tasks.items():
            try:
                result = await task
                results[agent_name] = result
                status = "✓" if result.status == "success" else "✗"
                print(f"[Coordinator] {status} {agent_name}: {result.duration:.1f}s")
            except Exception as e:
                results[agent_name] = AnalysisResult(
                    agent_name=agent_name,
                    status="error",
                    data={},
                    duration=0,
                    error_message=str(e)
                )
        
        return results
    
    async def _run_agent_analysis(self, agent: Any, agent_name: str, 
                                 content: str, url: str) -> AnalysisResult:
        """Run analysis for a single agent"""
        start_time = datetime.now()
        
        try:
            # Check if agent has analyze method
            if hasattr(agent, 'analyze'):
                result = await agent.analyze(content, url)
                
                # Convert result to dict if needed
                if hasattr(result, 'dict'):
                    data = result.dict()
                elif hasattr(result, '__dict__'):
                    data = result.__dict__
                else:
                    data = result
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return AnalysisResult(
                    agent_name=agent_name,
                    status="success",
                    data=data,
                    duration=duration
                )
            else:
                # Try alternative method calls
                if hasattr(agent, 'process'):
                    result = await agent.process(content, url)
                else:
                    raise AttributeError(f"Agent {agent_name} has no analyze or process method")
                
                duration = (datetime.now() - start_time).total_seconds()
                return AnalysisResult(
                    agent_name=agent_name,
                    status="success",
                    data=result,
                    duration=duration
                )
                
        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            return AnalysisResult(
                agent_name=agent_name,
                status="timeout",
                data={},
                duration=duration,
                error_message="Analysis timed out"
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return AnalysisResult(
                agent_name=agent_name,
                status="error",
                data={},
                duration=duration,
                error_message=str(e)
            )
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agents.keys())
    
    def get_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all agents"""
        agent_info = {}
        for name, agent in self.agents.items():
            agent_info[name] = {
                'name': name,
                'description': getattr(agent, '__doc__', 'No description'),
                'config': AGENT_CONFIG.get(name, {}),
                'available': True
            }
        return agent_info
    
    def format_results_for_storage(self, results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """Format analysis results for storage"""
        formatted = {}
        metadata = {
            'total_agents': len(results),
            'successful_agents': len([r for r in results.values() if r.status == "success"]),
            'failed_agents': len([r for r in results.values() if r.status != "success"]),
            'total_duration': sum(r.duration for r in results.values()),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        for agent_name, result in results.items():
            if result.status == "success":
                formatted[agent_name] = result.data
            else:
                formatted[agent_name] = {
                    "error": result.error_message,
                    "status": result.status,
                    "duration": result.duration
                }
        
        return {
            'analyses': formatted,
            'metadata': metadata
        }