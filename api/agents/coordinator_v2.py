"""Enhanced Agent Coordinator with Quality Control and Chat-based Refinement"""

import asyncio
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime
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
    JARGON = "jargon"
    VIEWPOINTS = "viewpoints"
    FACT_CHECK = "fact-check"
    BIAS = "bias"
    TIMELINE = "timeline"
    EXPERT = "expert"
    X_PULSE = "x-pulse"


@dataclass
class QualityCheckResult:
    """Result of quality check on agent output"""
    passed: bool
    issues: List[str] = None
    refinement_prompt: Optional[str] = None
    severity: str = "minor"  # minor, major, critical


@dataclass
class CoordinatorConfig:
    """Configuration for the agent coordinator"""
    max_parallel_agents: int = 4
    enable_streaming: bool = True
    timeout_seconds: int = 300
    retry_failed_agents: bool = True
    cost_limit_per_request: float = 1.0
    enable_quality_control: bool = True
    max_refinement_attempts: int = 2
    quality_threshold: float = 0.8


class EnhancedAgentCoordinator:
    """Coordinates agents with quality control and refinement capabilities"""
    
    def __init__(self, grok_client: Any, config: Optional[CoordinatorConfig] = None):
        self.grok_client = grok_client
        self.config = config or CoordinatorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize all available agents
        self.agents = self._initialize_agents()
        
        # Quality control functions for each analysis type
        self.quality_checkers = self._initialize_quality_checkers()
        
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
    
    def _initialize_quality_checkers(self) -> Dict[AnalysisType, Callable]:
        """Initialize quality check functions for each analysis type"""
        return {
            AnalysisType.JARGON: self._check_jargon_quality,
            AnalysisType.VIEWPOINTS: self._check_viewpoints_quality,
            AnalysisType.FACT_CHECK: self._check_fact_check_quality,
            AnalysisType.BIAS: self._check_bias_quality,
            AnalysisType.TIMELINE: self._check_timeline_quality,
            AnalysisType.EXPERT: self._check_expert_quality,
            AnalysisType.X_PULSE: self._check_x_pulse_quality,
        }
    
    async def refine_agent_result(
        self,
        agent: BaseAgent,
        initial_result: AgentResult,
        quality_result: QualityCheckResult,
        context: Dict[str, Any]
    ) -> AgentResult:
        """
        Refine agent result using conversation-based approach
        
        Uses xAI's conversation capability to iteratively improve results
        """
        try:
            # Build conversation history
            conversation_history = [
                {
                    "role": "assistant",
                    "content": json.dumps(initial_result.data, ensure_ascii=False)
                },
                {
                    "role": "user", 
                    "content": quality_result.refinement_prompt
                }
            ]
            
            # Add conversation history to context
            refinement_context = {
                **context,
                'conversation_history': conversation_history,
                'is_refinement': True,
                'refinement_attempt': 1
            }
            
            # Execute agent with conversation history
            refined_result = await agent.execute(refinement_context)
            
            if refined_result.success:
                self.logger.info(
                    f"Successfully refined {agent.config.name} output"
                )
                return refined_result
            else:
                self.logger.warning(
                    f"Refinement failed for {agent.config.name}: {refined_result.error}"
                )
                return initial_result
                
        except Exception as e:
            self.logger.error(f"Error during refinement: {str(e)}")
            return initial_result
    
    async def analyze_article_with_quality_control(
        self,
        article_url: str,
        article_text: str,
        analysis_types: List[AnalysisType],
        user_context: Optional[Dict[str, Any]] = None,
        stream_callback: Optional[Any] = None
    ) -> Dict[str, AgentResult]:
        """
        Analyze article with quality control and refinement
        """
        start_time = datetime.now()
        
        # Build context for all agents
        context = {
            'article_url': article_url,
            'article_text': article_text,
            'user_tier': user_context.get('tier', 'free') if user_context else 'free',
            'user_id': user_context.get('user_id') if user_context else None,
            'conversation_history': [],  # For chat-based refinement
            **user_context or {}
        }
        
        # Execute with quality control
        results = {}
        tasks = []
        
        for analysis_type in analysis_types:
            if analysis_type in self.agents:
                task = self._execute_with_quality_control(analysis_type, context)
                tasks.append((analysis_type, task))
        
        # Process all analyses concurrently
        for analysis_type, task in tasks:
            try:
                result = await task
                results[analysis_type] = result
                
                # Stream if successful and callback provided
                if result.success and stream_callback:
                    await stream_callback(analysis_type, result)
                    
            except Exception as e:
                self.logger.error(f"Failed to execute {analysis_type}: {str(e)}")
                results[analysis_type] = AgentResult(
                    success=False,
                    error=str(e),
                    agent_name=analysis_type.value
                )
        
        # Log summary
        total_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Completed {len(results)} analyses in {total_time:.2f}s with quality control")
        
        return results
    
    async def _execute_with_quality_control(
        self,
        analysis_type: AnalysisType,
        context: Dict[str, Any]
    ) -> AgentResult:
        """Execute agent with quality control and potential refinement"""
        agent = self.agents[analysis_type]
        quality_checker = self.quality_checkers.get(analysis_type)
        
        # Initial execution
        result = await agent.execute(context)
        
        if not result.success or not self.config.enable_quality_control:
            return result
        
        # Quality check
        quality_result = quality_checker(result.data, context)
        
        if quality_result.passed:
            self.logger.info(f"{analysis_type} passed quality check")
            return result
        
        # Refinement needed
        self.logger.warning(f"{analysis_type} needs refinement: {quality_result.issues}")
        
        # Attempt refinement through chat
        refined_result = await self._refine_through_chat(
            agent=agent,
            original_result=result,
            quality_result=quality_result,
            context=context,
            analysis_type=analysis_type
        )
        
        return refined_result or result
    
    async def _refine_through_chat(
        self,
        agent: BaseAgent,
        original_result: AgentResult,
        quality_result: QualityCheckResult,
        context: Dict[str, Any],
        analysis_type: AnalysisType
    ) -> Optional[AgentResult]:
        """Refine agent result through chat-based interaction"""
        
        for attempt in range(self.config.max_refinement_attempts):
            # Build refinement conversation
            conversation_history = context.get('conversation_history', [])
            
            # Add original result to history
            if attempt == 0:
                conversation_history.append({
                    "role": "assistant",
                    "content": json.dumps(original_result.data, ensure_ascii=False)
                })
            
            # Add refinement request
            refinement_message = self._build_refinement_message(
                quality_result=quality_result,
                analysis_type=analysis_type,
                attempt=attempt
            )
            
            conversation_history.append({
                "role": "user",
                "content": refinement_message
            })
            
            # Update context with conversation history
            refined_context = {
                **context,
                'conversation_history': conversation_history,
                'refinement_attempt': attempt + 1
            }
            
            # Execute refinement
            refined_result = await self._execute_refinement(
                agent=agent,
                context=refined_context,
                analysis_type=analysis_type
            )
            
            if not refined_result.success:
                continue
            
            # Check refined quality
            new_quality_result = self.quality_checkers[analysis_type](
                refined_result.data, context
            )
            
            if new_quality_result.passed:
                self.logger.info(f"{analysis_type} refinement successful on attempt {attempt + 1}")
                return refined_result
            
            # Add refined result to history for next attempt
            conversation_history.append({
                "role": "assistant",
                "content": json.dumps(refined_result.data, ensure_ascii=False)
            })
            
            quality_result = new_quality_result
        
        self.logger.warning(f"{analysis_type} refinement failed after {self.config.max_refinement_attempts} attempts")
        return None
    
    async def _execute_refinement(
        self,
        agent: BaseAgent,
        context: Dict[str, Any],
        analysis_type: AnalysisType
    ) -> AgentResult:
        """Execute agent with conversation history for refinement"""
        try:
            # Build chat messages from conversation history
            messages = []
            
            # Add system message
            messages.append({
                "role": "system",
                "content": f"You are refining a {analysis_type.value} analysis. Address the specific issues mentioned."
            })
            
            # Add conversation history
            for msg in context.get('conversation_history', []):
                messages.append(msg)
            
            # Use grok-3 for all refinements
            model = ModelType.GROK_3
            
            # Call Grok with conversation
            response = await self.grok_client.chat.completions.create(
                model=model.value,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            refined_data = json.loads(response.choices[0].message.content)
            
            return AgentResult(
                success=True,
                data=refined_data,
                model_used=model,
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else 0,
                agent_name=agent.config.name
            )
            
        except Exception as e:
            self.logger.error(f"Refinement error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                agent_name=agent.config.name
            )
    
    def _build_refinement_message(
        self,
        quality_result: QualityCheckResult,
        analysis_type: AnalysisType,
        attempt: int
    ) -> str:
        """Build refinement request message"""
        if quality_result.refinement_prompt:
            return quality_result.refinement_prompt
        
        issues_text = "\n".join([f"- {issue}" for issue in quality_result.issues])
        
        return f"""The {analysis_type.value} analysis needs improvement. Issues found:
{issues_text}

Please provide a refined analysis that addresses these issues. Ensure all output is in Greek and follows the expected schema."""
    
    # Quality check functions for each analysis type
    
    def _check_jargon_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of jargon analysis"""
        issues = []
        
        # Check if terms exist
        terms = data.get('terms', [])
        if not terms:
            issues.append("No terms identified")
        
        # Check term quality
        for term in terms:
            if not term.get('term'):
                issues.append("Term missing name")
            if not term.get('explanation'):
                issues.append(f"Term '{term.get('term', 'unknown')}' missing explanation")
            elif len(term.get('explanation', '')) < 20:
                issues.append(f"Term '{term.get('term', 'unknown')}' has too short explanation")
        
        # Check if explanations are in Greek
        for term in terms:
            explanation = term.get('explanation', '')
            if explanation and not any(ord(c) >= 0x0370 and ord(c) <= 0x03FF for c in explanation):
                issues.append(f"Term '{term.get('term', 'unknown')}' explanation not in Greek")
        
        passed = len(issues) == 0
        return QualityCheckResult(
            passed=passed,
            issues=issues,
            severity="minor" if len(issues) < 3 else "major"
        )
    
    def _check_viewpoints_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of alternative viewpoints"""
        issues = []
        
        # Check structure
        if not isinstance(data, dict):
            issues.append("Invalid data structure")
            return QualityCheckResult(passed=False, issues=issues, severity="critical")
        
        # Check for viewpoints
        viewpoints = data.get('alternative_viewpoints', data.get('viewpoints', []))
        if not viewpoints:
            issues.append("No alternative viewpoints found")
        elif len(viewpoints) < 3:
            issues.append("Too few viewpoints (minimum 3 expected)")
        
        # Check viewpoint quality
        for i, viewpoint in enumerate(viewpoints):
            if isinstance(viewpoint, str):
                if len(viewpoint) < 50:
                    issues.append(f"Viewpoint {i+1} too short")
                if not viewpoint.strip().endswith('.'):
                    issues.append(f"Viewpoint {i+1} incomplete")
        
        passed = len(issues) == 0
        return QualityCheckResult(
            passed=passed,
            issues=issues,
            refinement_prompt="Please provide at least 3-5 alternative viewpoints with proper citations in Greek." if not passed else None
        )
    
    def _check_fact_check_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of fact-checking analysis"""
        issues = []
        
        # Check overall credibility
        if 'overall_credibility' not in data:
            issues.append("Missing overall credibility assessment")
        
        # Check claims
        claims = data.get('claims', [])
        if not claims:
            issues.append("No claims analyzed")
        else:
            for i, claim in enumerate(claims):
                if not claim.get('statement'):
                    issues.append(f"Claim {i+1} missing statement")
                if 'verified' not in claim:
                    issues.append(f"Claim {i+1} missing verification status")
                if not claim.get('sources'):
                    issues.append(f"Claim {i+1} missing sources")
        
        passed = len(issues) == 0
        return QualityCheckResult(
            passed=passed,
            issues=issues,
            severity="major" if len(issues) > 2 else "minor"
        )
    
    def _check_bias_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of bias analysis"""
        issues = []
        
        # Check Greek political spectrum analysis
        spectrum = data.get('political_spectrum_analysis_greek', {})
        if not spectrum:
            issues.append("Missing Greek political spectrum analysis")
        else:
            if not spectrum.get('economic_axis_placement'):
                issues.append("Missing economic axis placement")
            if not spectrum.get('economic_axis_justification'):
                issues.append("Missing economic axis justification")
            if not spectrum.get('social_axis_placement'):
                issues.append("Missing social axis placement")
            if not spectrum.get('social_axis_justification'):
                issues.append("Missing social axis justification")
        
        # Check language analysis
        language = data.get('language_and_framing_analysis', {})
        if not language:
            issues.append("Missing language and framing analysis")
        
        passed = len(issues) == 0
        return QualityCheckResult(
            passed=passed,
            issues=issues,
            refinement_prompt="Please provide complete Greek political spectrum analysis with justifications." if not passed else None
        )
    
    def _check_timeline_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of timeline analysis"""
        issues = []
        
        # Check events
        events = data.get('events', [])
        if not events:
            issues.append("No events in timeline")
        elif len(events) < 3:
            issues.append("Too few events in timeline")
        
        # Check event quality
        for i, event in enumerate(events):
            if not event.get('date'):
                issues.append(f"Event {i+1} missing date")
            if not event.get('title'):
                issues.append(f"Event {i+1} missing title")
            if not event.get('description'):
                issues.append(f"Event {i+1} missing description")
        
        # Check chronological order
        if len(events) > 1:
            dates = [e.get('date', '') for e in events]
            if dates != sorted(dates):
                issues.append("Events not in chronological order")
        
        passed = len(issues) == 0
        return QualityCheckResult(passed=passed, issues=issues)
    
    def _check_expert_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of expert opinions"""
        issues = []
        
        # Check experts
        experts = data.get('experts', [])
        if not experts:
            issues.append("No expert opinions found")
        
        # Check expert quality
        for i, expert in enumerate(experts):
            if not expert.get('name'):
                issues.append(f"Expert {i+1} missing name")
            if not expert.get('credentials'):
                issues.append(f"Expert {i+1} missing credentials")
            if not expert.get('opinion'):
                issues.append(f"Expert {i+1} missing opinion")
        
        passed = len(issues) == 0
        return QualityCheckResult(passed=passed, issues=issues)
    
    def _check_x_pulse_quality(self, data: Dict[str, Any], context: Dict[str, Any]) -> QualityCheckResult:
        """Check quality of X Pulse analysis"""
        issues = []
        
        # Check overall summary
        if not data.get('overall_discourse_summary'):
            issues.append("Missing overall discourse summary")
        
        # Check themes
        themes = data.get('discussion_themes', [])
        if not themes:
            issues.append("No discussion themes identified")
        elif len(themes) < 2:
            issues.append("Too few themes (minimum 2 expected)")
        
        # Check theme quality
        for i, theme in enumerate(themes):
            if not theme.get('theme_title'):
                issues.append(f"Theme {i+1} missing title")
            if not theme.get('theme_summary'):
                issues.append(f"Theme {i+1} missing summary")
            if not theme.get('sentiment_around_theme'):
                issues.append(f"Theme {i+1} missing sentiment analysis")
        
        passed = len(issues) == 0
        return QualityCheckResult(
            passed=passed,
            issues=issues,
            severity="major" if len(issues) > 3 else "minor",
            refinement_prompt="Please identify at least 3-5 discussion themes with sentiment analysis." if not passed else None
        )