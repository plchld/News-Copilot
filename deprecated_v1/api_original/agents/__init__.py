"""News Copilot Agentic Architecture

This package implements an intelligent agent-based system for news analysis
with dynamic model selection and nested agent capabilities.
"""

from .base_agent import BaseAgent, AnalysisAgent, NestedAgent, AgentConfig, ModelType, ComplexityLevel, AgentResult
from .optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, AnalysisType, OptimizedCoordinatorConfig as CoordinatorConfig
from .jargon_agent import JargonAgent
from .viewpoints_agent import ViewpointsAgent
from .fact_check_agent import FactCheckAgent
from .bias_agent import BiasAnalysisAgent
from .timeline_agent import TimelineAgent
from .expert_agent import ExpertOpinionsAgent
from .x_pulse_agent import XPulseAgent

__all__ = [
    'BaseAgent',
    'AnalysisAgent',
    'NestedAgent',
    'AgentConfig',
    'ModelType',
    'ComplexityLevel',
    'AgentResult',
    'AgentCoordinator',
    'AnalysisType',
    'CoordinatorConfig',
    'JargonAgent',
    'ViewpointsAgent',
    'FactCheckAgent',
    'BiasAnalysisAgent',
    'TimelineAgent',
    'ExpertOpinionsAgent',
    'XPulseAgent'
]