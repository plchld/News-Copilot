"""Advanced Collaborative Agent System - Implementing true agentic intelligence"""

from typing import Dict, Any, List, Set, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import asyncio
import json
from datetime import datetime

from .base_agent import BaseAgent, AgentResult, ModelType, ComplexityLevel, AgentConfig


# Message passing system for inter-agent communication
@dataclass
class AgentMessage:
    """Message passed between agents"""
    from_agent: str
    to_agent: Optional[str]  # None for broadcast
    message_type: str
    content: Any
    priority: int = 1
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MessageBus:
    """Central message bus for agent communication"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.message_history = []
        self.message_queue = asyncio.Queue()
        
    def subscribe(self, agent_name: str, message_types: List[str]):
        """Subscribe an agent to specific message types"""
        for msg_type in message_types:
            self.subscribers[msg_type].append(agent_name)
    
    async def publish(self, message: AgentMessage):
        """Publish a message to the bus"""
        self.message_history.append(message)
        await self.message_queue.put(message)
    
    async def get_messages_for_agent(self, agent_name: str) -> List[AgentMessage]:
        """Get all pending messages for an agent"""
        messages = []
        
        # Check all messages in queue
        temp_queue = []
        while not self.message_queue.empty():
            msg = await self.message_queue.get()
            
            # Direct message or subscribed broadcast
            if msg.to_agent == agent_name or (
                msg.to_agent is None and 
                agent_name in self.subscribers.get(msg.message_type, [])
            ):
                messages.append(msg)
            else:
                temp_queue.append(msg)
        
        # Put back non-matching messages
        for msg in temp_queue:
            await self.message_queue.put(msg)
        
        return messages


# Scout Agents for initial rapid analysis
class TopicScoutAgent(BaseAgent):
    """Ultra-fast agent that identifies main topics and content type"""
    
    @classmethod
    def create(cls, grok_client: Any, message_bus: MessageBus) -> 'TopicScoutAgent':
        config = AgentConfig(
            name="TopicScoutAgent",
            description="Rapidly identifies topics and content type",
            default_model=ModelType.GROK_3_MINI,
            complexity=ComplexityLevel.SIMPLE,
            timeout_seconds=10
        )
        agent = cls(config, grok_client)
        agent.message_bus = message_bus
        return agent
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Scout for topics and broadcast findings"""
        start_time = datetime.now()
        
        try:
            # Quick topic extraction
            prompt = f"""Quickly identify:
1. Main topic category (politics/economy/health/technology/international/other)
2. Key entities mentioned (people, organizations, locations)
3. Content type (news/opinion/analysis/investigation)
4. Urgency level (breaking/current/historical)
5. Specialized domains that need analysis

Article excerpt: {context['article_text'][:1000]}...

Return JSON format."""

            schema = {
                "type": "object",
                "properties": {
                    "main_category": {"type": "string"},
                    "entities": {"type": "array", "items": {"type": "string"}},
                    "content_type": {"type": "string"},
                    "urgency": {"type": "string"},
                    "specialized_domains": {"type": "array", "items": {"type": "string"}}
                }
            }
            
            response = await self._quick_analysis(prompt, schema, context)
            
            # Broadcast findings to other agents
            await self.message_bus.publish(AgentMessage(
                from_agent=self.config.name,
                to_agent=None,
                message_type="topic_identified",
                content=response['data'],
                priority=10
            ))
            
            # Specific broadcasts based on findings
            if response['data'].get('main_category') == 'politics':
                await self.message_bus.publish(AgentMessage(
                    from_agent=self.config.name,
                    to_agent=None,
                    message_type="political_content_detected",
                    content={"entities": response['data'].get('entities', [])}
                ))
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                data=response['data'],
                model_used=ModelType.GROK_3_MINI,
                execution_time_ms=execution_time_ms,
                agent_name=self.config.name
            )
            
        except Exception as e:
            return AgentResult(success=False, error=str(e), agent_name=self.config.name)
    
    async def _quick_analysis(self, prompt: str, schema: Dict, context: Dict) -> Dict:
        """Perform quick analysis with minimal context"""
        # Simplified implementation - would use actual Grok client
        return {'data': {
            'main_category': 'politics',
            'entities': ['Example Entity'],
            'content_type': 'news',
            'urgency': 'current',
            'specialized_domains': ['elections']
        }}


# Collaborative Analysis Agents
class CollaborativeBiasAgent(BaseAgent):
    """Bias agent that collaborates with other agents"""
    
    def __init__(self, config: AgentConfig, grok_client: Any, message_bus: MessageBus):
        super().__init__(config, grok_client)
        self.message_bus = message_bus
        self.collected_insights = {}
        
        # Subscribe to relevant messages
        message_bus.subscribe(config.name, [
            "political_content_detected",
            "loaded_language_found",
            "fact_check_completed",
            "source_bias_identified"
        ])
    
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute with collaboration"""
        # Collect messages from other agents
        messages = await self.message_bus.get_messages_for_agent(self.config.name)
        
        # Incorporate insights from other agents
        for msg in messages:
            if msg.message_type == "political_content_detected":
                self.collected_insights['political_entities'] = msg.content.get('entities', [])
            elif msg.message_type == "loaded_language_found":
                self.collected_insights['loaded_terms'] = msg.content
        
        # Enhanced context with collaborative insights
        enhanced_context = {
            **context,
            'collaborative_insights': self.collected_insights
        }
        
        # Perform bias analysis with enhanced context
        result = await self._analyze_with_insights(enhanced_context)
        
        # Share findings with other agents
        if result.success and result.data.get('political_lean'):
            await self.message_bus.publish(AgentMessage(
                from_agent=self.config.name,
                to_agent=None,
                message_type="bias_detected",
                content={
                    'political_lean': result.data['political_lean'],
                    'confidence': result.data.get('confidence', 'medium')
                }
            ))
        
        return result


# Dynamic Agent Spawner
class DynamicAgentSpawner:
    """Spawns specialized agents based on content analysis"""
    
    def __init__(self, grok_client: Any, message_bus: MessageBus):
        self.grok_client = grok_client
        self.message_bus = message_bus
        self.spawned_agents = {}
    
    async def analyze_and_spawn(self, scout_results: Dict[str, Any]) -> List[BaseAgent]:
        """Spawn specialized agents based on scout findings"""
        spawned = []
        
        main_category = scout_results.get('main_category', '')
        domains = scout_results.get('specialized_domains', [])
        
        # Spawn category-specific agents
        if main_category == 'politics' and 'elections' in domains:
            agent = await self._spawn_election_agent()
            spawned.append(agent)
        
        if main_category == 'economy':
            agent = await self._spawn_economic_agent()
            spawned.append(agent)
        
        if 'COVID' in str(scout_results.get('entities', [])):
            agent = await self._spawn_health_crisis_agent()
            spawned.append(agent)
        
        # International content needs comparative analysis
        entities = scout_results.get('entities', [])
        countries = [e for e in entities if self._is_country(e)]
        if len(countries) > 1:
            agent = await self._spawn_comparative_agent(countries)
            spawned.append(agent)
        
        return spawned
    
    async def _spawn_election_agent(self) -> BaseAgent:
        """Spawn specialized election analysis agent"""
        config = AgentConfig(
            name="ElectionAnalysisAgent",
            description="Specialized election and polling analysis",
            default_model=ModelType.GROK_3,
            complexity=ComplexityLevel.HIGH
        )
        
        # Create a specialized agent with election-specific logic
        agent = ElectionSpecialistAgent(config, self.grok_client, self.message_bus)
        self.spawned_agents['election'] = agent
        return agent
    
    def _is_country(self, entity: str) -> bool:
        """Check if entity is a country name"""
        countries = ['Ελλάδα', 'Γερμανία', 'ΗΠΑ', 'Τουρκία', 'Κίνα', 'Ρωσία']
        return entity in countries


# Synthesis and Meta-Analysis
class InsightSynthesisAgent(BaseAgent):
    """Synthesizes insights from all agents into coherent analysis"""
    
    def __init__(self, config: AgentConfig, grok_client: Any, message_bus: MessageBus):
        super().__init__(config, grok_client)
        self.message_bus = message_bus
    
    async def synthesize(self, all_results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """Synthesize all agent results into unified insights"""
        
        # Collect all successful results
        insights = {}
        for agent_type, result in all_results.items():
            if result.success:
                insights[agent_type] = result.data
        
        # Look for patterns and contradictions
        contradictions = self._find_contradictions(insights)
        patterns = self._identify_patterns(insights)
        confidence_scores = self._aggregate_confidence(insights)
        
        # Create synthesis prompt
        synthesis_prompt = f"""
Synthesize these analysis results into a coherent summary:
{json.dumps(insights, ensure_ascii=False)}

Identify:
1. Key findings across all analyses
2. Contradictions found: {contradictions}
3. Recurring patterns: {patterns}
4. Overall confidence level
5. Gaps in analysis
6. Unexpected insights

Provide a unified narrative in Greek.
"""
        
        response = await self._call_grok(
            prompt=synthesis_prompt,
            schema=None,  # Free-form synthesis
            model=ModelType.GROK_3,
            search_params=None,
            context={}
        )
        
        return {
            'unified_analysis': response['data'],
            'contradictions': contradictions,
            'patterns': patterns,
            'confidence_scores': confidence_scores,
            'agent_consensus': self._calculate_consensus(insights)
        }
    
    def _find_contradictions(self, insights: Dict) -> List[Dict]:
        """Identify contradictions between agent findings"""
        contradictions = []
        
        # Example: Bias agent says "left-leaning" but fact-checker finds "neutral sources"
        if 'bias' in insights and 'fact_check' in insights:
            bias_lean = insights['bias'].get('political_lean')
            sources = insights['fact_check'].get('source_analysis', {})
            
            if bias_lean == 'αριστερά' and sources.get('bias') == 'neutral':
                contradictions.append({
                    'type': 'bias_source_mismatch',
                    'description': 'Article appears left-leaning but uses neutral sources'
                })
        
        return contradictions
    
    def _identify_patterns(self, insights: Dict) -> List[str]:
        """Identify recurring patterns across analyses"""
        patterns = []
        
        # Check for consistent themes
        mentioned_entities = set()
        for agent_data in insights.values():
            if isinstance(agent_data, dict):
                entities = agent_data.get('entities', [])
                mentioned_entities.update(entities)
        
        if len(mentioned_entities) > 5:
            patterns.append(f"Complex story involving {len(mentioned_entities)} entities")
        
        return patterns
    
    def _aggregate_confidence(self, insights: Dict) -> Dict[str, float]:
        """Aggregate confidence scores from all agents"""
        scores = {}
        for agent, data in insights.items():
            if isinstance(data, dict) and 'confidence' in data:
                scores[agent] = data['confidence']
        return scores
    
    def _calculate_consensus(self, insights: Dict) -> float:
        """Calculate overall consensus level between agents"""
        # Simplified consensus calculation
        return 0.75  # Placeholder


# Pattern Recognition and Memory
class PatternMemoryAgent(BaseAgent):
    """Maintains memory of patterns across analyses"""
    
    def __init__(self, config: AgentConfig, grok_client: Any):
        super().__init__(config, grok_client)
        self.pattern_memory = {}
        self.analysis_history = []
    
    async def analyze_with_memory(self, context: Dict[str, Any]) -> AgentResult:
        """Analyze while checking against historical patterns"""
        
        # Extract current patterns
        current_patterns = await self._extract_patterns(context)
        
        # Check against memory
        similar_patterns = self._search_memory(current_patterns)
        
        # Identify trends
        trends = self._identify_trends(current_patterns, similar_patterns)
        
        # Update memory
        self._update_memory(current_patterns)
        
        return AgentResult(
            success=True,
            data={
                'current_patterns': current_patterns,
                'historical_matches': similar_patterns,
                'identified_trends': trends,
                'pattern_evolution': self._track_evolution(current_patterns)
            },
            agent_name=self.config.name
        )
    
    async def _extract_patterns(self, context: Dict[str, Any]) -> Dict:
        """Extract patterns from current article"""
        # Simplified pattern extraction
        return {
            'narrative_type': 'political_conflict',
            'entities': ['Entity1', 'Entity2'],
            'sentiment_pattern': 'escalating',
            'timestamp': datetime.now()
        }
    
    def _search_memory(self, patterns: Dict) -> List[Dict]:
        """Search memory for similar patterns"""
        similar = []
        for memory_id, memory_pattern in self.pattern_memory.items():
            similarity = self._calculate_similarity(patterns, memory_pattern)
            if similarity > 0.7:
                similar.append({
                    'pattern': memory_pattern,
                    'similarity': similarity,
                    'date': memory_pattern.get('timestamp')
                })
        return similar
    
    def _calculate_similarity(self, pattern1: Dict, pattern2: Dict) -> float:
        """Calculate similarity between two patterns"""
        # Simplified similarity calculation
        return 0.8
    
    def _identify_trends(self, current: Dict, historical: List[Dict]) -> List[str]:
        """Identify trends from pattern history"""
        trends = []
        if len(historical) > 3:
            trends.append(f"Recurring {current['narrative_type']} narrative detected")
        return trends
    
    def _update_memory(self, patterns: Dict):
        """Update pattern memory"""
        memory_id = f"pattern_{datetime.now().timestamp()}"
        self.pattern_memory[memory_id] = patterns
    
    def _track_evolution(self, patterns: Dict) -> Dict:
        """Track how patterns evolve over time"""
        return {'evolution_stage': 'emerging'}


# Advanced Coordinator with full collaborative features
class CollaborativeCoordinator:
    """Orchestrates the full power of collaborative agent system"""
    
    def __init__(self, grok_client: Any):
        self.grok_client = grok_client
        self.message_bus = MessageBus()
        self.agent_spawner = DynamicAgentSpawner(grok_client, self.message_bus)
        self.pattern_memory = PatternMemoryAgent(
            AgentConfig("PatternMemory", "Pattern recognition", ModelType.GROK_3, ComplexityLevel.HIGH),
            grok_client
        )
    
    async def analyze_with_full_power(
        self,
        article_url: str,
        article_text: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute full collaborative analysis"""
        
        # Phase 1: Scout Analysis (parallel, ultra-fast)
        scout_results = await self._run_scouts(article_text)
        
        # Phase 2: Dynamic Agent Spawning
        specialized_agents = await self.agent_spawner.analyze_and_spawn(scout_results['topic'])
        
        # Phase 3: Collaborative Deep Analysis
        deep_results = await self._run_collaborative_analysis(
            article_text, scout_results, specialized_agents
        )
        
        # Phase 4: Pattern Recognition
        pattern_insights = await self.pattern_memory.analyze_with_memory({
            'article_text': article_text,
            'scout_results': scout_results,
            'deep_results': deep_results
        })
        
        # Phase 5: Synthesis and Meta-Analysis
        synthesis_agent = InsightSynthesisAgent(
            AgentConfig("Synthesis", "Insight synthesis", ModelType.GROK_3, ComplexityLevel.VERY_HIGH),
            self.grok_client,
            self.message_bus
        )
        
        final_synthesis = await synthesis_agent.synthesize(deep_results)
        
        # Phase 6: Quality Assurance through Consensus
        consensus_result = await self._run_consensus_validation(deep_results)
        
        return {
            'scout_insights': scout_results,
            'deep_analysis': deep_results,
            'pattern_insights': pattern_insights.data,
            'synthesis': final_synthesis,
            'consensus_validation': consensus_result,
            'collaborative_messages': len(self.message_bus.message_history),
            'spawned_specialists': [a.config.name for a in specialized_agents]
        }
    
    async def _run_scouts(self, article_text: str) -> Dict[str, Any]:
        """Run all scout agents in parallel"""
        # Initialize scouts
        topic_scout = TopicScoutAgent.create(self.grok_client, self.message_bus)
        
        # Run scouts in parallel
        context = {'article_text': article_text}
        scout_tasks = [
            topic_scout.execute(context),
            # Add more scouts as needed
        ]
        
        results = await asyncio.gather(*scout_tasks)
        
        return {
            'topic': results[0].data if results[0].success else {}
        }
    
    async def _run_collaborative_analysis(
        self,
        article_text: str,
        scout_results: Dict,
        specialized_agents: List[BaseAgent]
    ) -> Dict[str, AgentResult]:
        """Run deep analysis with agent collaboration"""
        
        # Standard agents + specialized ones
        all_agents = {
            # Standard agents would be initialized here
            # 'bias': CollaborativeBiasAgent(...),
            # 'fact_check': CollaborativeFactChecker(...),
        }
        
        # Add specialized agents
        for agent in specialized_agents:
            all_agents[agent.config.name] = agent
        
        # Execute all agents (they'll collaborate via message bus)
        context = {
            'article_text': article_text,
            'scout_insights': scout_results
        }
        
        tasks = []
        for name, agent in all_agents.items():
            tasks.append(agent.execute(context))
        
        results = await asyncio.gather(*tasks)
        
        return {name: result for name, result in zip(all_agents.keys(), results)}
    
    async def _run_consensus_validation(self, results: Dict[str, AgentResult]) -> Dict:
        """Run consensus validation across all agent results"""
        
        # Example: Multiple agents vote on key claims
        consensus_items = []
        
        # Extract claims from different agents
        all_claims = []
        for agent_name, result in results.items():
            if result.success and 'claims' in result.data:
                all_claims.extend(result.data['claims'])
        
        # Have agents vote on each claim
        # (Simplified - in reality, would re-run agents in validation mode)
        for claim in all_claims[:5]:  # Top 5 claims
            votes = {
                'verified': 3,
                'unverified': 1,
                'uncertain': 1
            }
            consensus_items.append({
                'claim': claim,
                'consensus': 'verified' if votes['verified'] > 2 else 'disputed',
                'confidence': votes['verified'] / sum(votes.values())
            })
        
        return {
            'consensus_items': consensus_items,
            'overall_reliability': 0.8,
            'agent_agreement_score': 0.75
        }