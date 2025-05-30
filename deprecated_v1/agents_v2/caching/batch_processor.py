"""Batch processor for analyzing multiple stories with optimal caching"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .conversation_agent import ConversationalAgent, ConversationConfig
from ..tracing import trace_manager, SpanType


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    
    # Batch settings
    stories_per_conversation: int = 10
    max_parallel_conversations: int = 3
    conversation_timeout_minutes: int = 10
    
    # Agent settings per analysis type
    agent_configs: Dict[str, ConversationConfig] = None
    
    # Cost optimization
    prefer_cache_reuse: bool = True
    max_conversation_reuse: int = 5  # How many batches to reuse conversation
    
    def __post_init__(self):
        """Set default agent configurations"""
        if self.agent_configs is None:
            self.agent_configs = {
                "greek_perspective": ConversationConfig(
                    name="greek_perspective_batch",
                    instructions="""You are an expert analyst of Greek media and public discourse.

Analyze how Greek media covers each story I provide. For each story, examine:
- Dominant Greek narrative and consensus
- Unique Greek angles and concerns  
- What Greek media emphasizes vs ignores
- Political spin or bias detection
- Source diversity (left/right/center)
- Public sentiment if detectable

Greek media context:
- Mainstream: Kathimerini, Ta Nea, Proto Thema, SKAI
- Left: Efsyn, Avgi, Documento  
- Alternative: TOC, Liberal.gr
- Consider both Greek and English Greek sources

Provide clear, objective analysis while noting biases.""",
                    provider="anthropic",
                    cache_ttl="5m",
                    batch_size=10
                ),
                
                "international_perspective": ConversationConfig(
                    name="international_perspective_batch", 
                    instructions="""You are an expert analyst of international media and global perspectives.

Analyze how different regions cover each story I provide. For each story:
- Identify how different regions frame it
- Note cultural/political biases in coverage
- Find facts that appear globally vs locally
- Assess consensus points and major differences
- Consider geopolitical context

Key regions to analyze (adapt by story relevance):
- US: CNN, NYT, WSJ, Fox News
- UK: BBC, Guardian, Times
- EU: DW, France24, El País
- Others based on story (Asia, Middle East, etc.)

Focus on substantive differences in framing and emphasis.""",
                    provider="anthropic", 
                    cache_ttl="5m",
                    batch_size=10
                ),
                
                "fact_verification": ConversationConfig(
                    name="fact_verification_batch",
                    instructions="""You are a fact-checking and verification specialist.

For each story I provide, verify key claims using rigorous methodology:
- Find primary sources (official statements, data, documents)
- Check multiple reliable sources for each fact
- Identify contested or uncertain claims
- Note confidence levels for each verification
- Distinguish facts from speculation

Verification levels:
- Confirmed: Multiple reliable sources agree
- Disputed: Credible sources disagree  
- Partially-true: True with important caveats
- Unverifiable: Cannot confirm with available data

Source hierarchy: Official sources → Peer-reviewed research → Government data → Major news → Expert analysis → Fact-checkers""",
                    provider="anthropic",
                    cache_ttl="5m", 
                    batch_size=10
                ),
                
                "synthesis": ConversationConfig(
                    name="synthesis_batch",
                    instructions="""You are an expert narrative synthesizer and journalist.

For each story I provide along with multiple perspectives, create a unified narrative that:
- Integrates all perspectives fairly
- Presents the complete picture without bias
- Clearly attributes different viewpoints
- Highlights agreements and divergences
- Maintains neutral, professional tone
- Prioritizes verified facts over speculation

Structure each synthesis:
- Context setting (what happened)
- Multiple perspectives with clear attribution
- Areas of agreement and disagreement
- Important nuances and caveats
- Key takeaways for readers

Write clearly and accessibly while being comprehensive.""",
                    provider="anthropic",
                    cache_ttl="5m",
                    batch_size=8  # Synthesis requires more context per story
                )
            }


class BatchAnalysisProcessor:
    """Processor for analyzing stories in optimal batches with caching"""
    
    def __init__(self, config: BatchProcessingConfig):
        """Initialize batch processor
        
        Args:
            config: Batch processing configuration
        """
        self.config = config
        
        # Initialize conversational agents for each analysis type
        self.agents: Dict[str, ConversationalAgent] = {}
        for agent_type, agent_config in config.agent_configs.items():
            self.agents[agent_type] = ConversationalAgent(agent_config)
        
        # Track active conversations for reuse
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
    async def process_stories_batch(
        self,
        stories: List[Dict[str, Any]],
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """Process a batch of stories with optimal caching
        
        Args:
            stories: List of stories to analyze
            analysis_types: Types of analysis to perform
            
        Returns:
            Dictionary with analysis results and processing stats
        """
        if analysis_types is None:
            analysis_types = ["greek_perspective", "international_perspective", "fact_verification"]
        
        # Validate analysis types
        invalid_types = set(analysis_types) - set(self.agents.keys())
        if invalid_types:
            raise ValueError(f"Unknown analysis types: {invalid_types}")
        
        with trace_manager.trace("Batch Story Analysis") as trace_id:
            trace_manager.add_trace_metadata({
                "total_stories": len(stories),
                "analysis_types": analysis_types,
                "batch_config": {
                    "stories_per_conversation": self.config.stories_per_conversation,
                    "max_parallel": self.config.max_parallel_conversations
                }
            })
            
            # Split stories into optimal batches
            story_batches = self._create_optimal_batches(stories, analysis_types)
            
            # Process each analysis type
            all_results = {}
            processing_stats = {}
            
            for analysis_type in analysis_types:
                with trace_manager.span(
                    SpanType.CUSTOM,
                    f"Process {analysis_type}",
                    analysis_type=analysis_type,
                    batches=len(story_batches[analysis_type])
                ):
                    
                    type_results, type_stats = await self._process_analysis_type(
                        analysis_type,
                        story_batches[analysis_type]
                    )
                    
                    all_results[analysis_type] = type_results
                    processing_stats[analysis_type] = type_stats
            
            # Synthesis step if requested
            if "synthesis" in analysis_types and len(analysis_types) > 1:
                synthesis_results = await self._synthesize_perspectives(
                    stories,
                    all_results
                )
                all_results["synthesis"] = synthesis_results
        
        return {
            "results": all_results,
            "processing_stats": processing_stats,
            "summary": self._generate_processing_summary(stories, all_results, processing_stats)
        }
    
    def _create_optimal_batches(
        self,
        stories: List[Dict[str, Any]],
        analysis_types: List[str]
    ) -> Dict[str, List[List[Dict[str, Any]]]]:
        """Create optimal batches for each analysis type"""
        
        batches = {}
        
        for analysis_type in analysis_types:
            agent_config = self.config.agent_configs[analysis_type]
            batch_size = agent_config.batch_size
            
            # Split stories into batches
            type_batches = []
            for i in range(0, len(stories), batch_size):
                batch = stories[i:i + batch_size]
                type_batches.append(batch)
            
            batches[analysis_type] = type_batches
        
        return batches
    
    async def _process_analysis_type(
        self,
        analysis_type: str,
        story_batches: List[List[Dict[str, Any]]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process all batches for a specific analysis type"""
        
        agent = self.agents[analysis_type]
        all_results = []
        
        # Try to reuse existing conversation or start new one
        conversation_id = await self._get_or_create_conversation(analysis_type)
        
        batch_stats = {
            "total_batches": len(story_batches),
            "conversation_reused": conversation_id in self.active_conversations,
            "total_stories": sum(len(batch) for batch in story_batches),
            "start_time": time.time()
        }
        
        try:
            # Process batches sequentially to maintain cache benefits
            for batch_idx, story_batch in enumerate(story_batches):
                with trace_manager.span(
                    SpanType.CUSTOM,
                    f"Process Batch {batch_idx + 1}/{len(story_batches)}",
                    batch_idx=batch_idx,
                    batch_size=len(story_batch)
                ):
                    
                    batch_results = await agent.process_story_batch(
                        conversation_id,
                        story_batch
                    )
                    all_results.extend(batch_results)
            
            # Get conversation statistics
            conv_stats = agent.get_conversation_stats(conversation_id)
            batch_stats.update({
                "conversation_stats": conv_stats,
                "processing_time": time.time() - batch_stats["start_time"]
            })
            
            # Decide whether to keep conversation for reuse
            if self._should_keep_conversation(analysis_type, conv_stats):
                self.active_conversations[conversation_id] = {
                    "analysis_type": analysis_type,
                    "created_at": time.time(),
                    "reuse_count": self.active_conversations.get(conversation_id, {}).get("reuse_count", 0) + 1
                }
            else:
                # End conversation and get final stats
                final_stats = await agent.end_conversation(conversation_id)
                batch_stats["final_conversation_stats"] = final_stats
                self.active_conversations.pop(conversation_id, None)
        
        except Exception as e:
            # Clean up on error
            if conversation_id in self.active_conversations:
                await agent.end_conversation(conversation_id)
                self.active_conversations.pop(conversation_id, None)
            raise e
        
        return all_results, batch_stats
    
    async def _get_or_create_conversation(self, analysis_type: str) -> str:
        """Get existing conversation or create new one for analysis type"""
        
        # Look for reusable conversation
        for conv_id, conv_info in list(self.active_conversations.items()):
            if (conv_info["analysis_type"] == analysis_type and 
                conv_info["reuse_count"] < self.config.max_conversation_reuse):
                
                # Check if conversation is still fresh (within cache TTL)
                age_minutes = (time.time() - conv_info["created_at"]) / 60
                cache_ttl_minutes = 5 if self.config.agent_configs[analysis_type].cache_ttl == "5m" else 60
                
                if age_minutes < cache_ttl_minutes * 0.8:  # Use 80% of cache time for safety
                    return conv_id
                else:
                    # Conversation too old, remove it
                    agent = self.agents[analysis_type]
                    await agent.end_conversation(conv_id)
                    self.active_conversations.pop(conv_id, None)
        
        # Create new conversation
        agent = self.agents[analysis_type]
        return await agent.start_conversation(analysis_type)
    
    def _should_keep_conversation(self, analysis_type: str, conv_stats: Dict[str, Any]) -> bool:
        """Decide whether to keep conversation for reuse"""
        
        # Keep if under reuse limit and cache hit ratio is good
        reuse_count = self.active_conversations.get(conv_stats["conversation_id"], {}).get("reuse_count", 0)
        cache_hit_ratio = conv_stats.get("tokens", {}).get("cache_read", 0) / max(conv_stats.get("tokens", {}).get("total_input", 1), 1)
        
        return (
            reuse_count < self.config.max_conversation_reuse and
            cache_hit_ratio > 0.3 and  # Good cache utilization
            conv_stats.get("active_for_minutes", 0) < 8  # Not too old
        )
    
    async def _synthesize_perspectives(
        self,
        stories: List[Dict[str, Any]],
        analysis_results: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Synthesize multiple perspectives for each story"""
        
        if "synthesis" not in self.agents:
            return []
        
        synthesis_agent = self.agents["synthesis"]
        conversation_id = await synthesis_agent.start_conversation("synthesis")
        
        synthesis_results = []
        
        try:
            # Group results by story
            story_perspectives = {}
            for analysis_type, results in analysis_results.items():
                if analysis_type == "synthesis":
                    continue
                    
                for result in results:
                    story_id = result.get("story_id", "unknown")
                    if story_id not in story_perspectives:
                        story_perspectives[story_id] = {}
                    story_perspectives[story_id][analysis_type] = result
            
            # Synthesize each story
            for story in stories:
                story_id = story.get("id", "unknown")
                if story_id in story_perspectives:
                    
                    # Create synthesis prompt
                    synthesis_prompt = self._create_synthesis_prompt(
                        story,
                        story_perspectives[story_id]
                    )
                    
                    # Process synthesis
                    response = await synthesis_agent._send_message(
                        conversation_id,
                        "user", 
                        synthesis_prompt,
                        cache_conversation=True
                    )
                    
                    synthesis_results.append({
                        "story_id": story_id,
                        "headline": story.get("headline", ""),
                        "synthesis": response,
                        "perspectives_used": list(story_perspectives[story_id].keys())
                    })
            
            # End synthesis conversation
            await synthesis_agent.end_conversation(conversation_id)
            
        except Exception as e:
            await synthesis_agent.end_conversation(conversation_id)
            raise e
        
        return synthesis_results
    
    def _create_synthesis_prompt(
        self,
        story: Dict[str, Any],
        perspectives: Dict[str, Dict[str, Any]]
    ) -> str:
        """Create synthesis prompt from multiple perspectives"""
        
        prompt = f"""
# Story Synthesis Request

## Story: {story.get('headline', 'Unknown')}
**Category:** {story.get('category', 'general')}
**Why Important:** {story.get('why_important', '')}

## Perspectives to Synthesize:

"""
        
        for perspective_type, analysis in perspectives.items():
            prompt += f"""
### {perspective_type.replace('_', ' ').title()}:
{analysis.get('analysis', {}).get('raw_content', 'No analysis available')[:500]}...

"""
        
        prompt += """
## Synthesis Task:
Create a unified 400-word narrative that:
1. Integrates all perspectives fairly
2. Clearly attributes different viewpoints  
3. Highlights key agreements and disagreements
4. Maintains neutral tone
5. Prioritizes verified facts
6. Provides clear takeaways for Greek readers

Focus on creating a complete picture that helps readers understand all angles.
"""
        
        return prompt
    
    def _generate_processing_summary(
        self,
        stories: List[Dict[str, Any]],
        results: Dict[str, List[Dict[str, Any]]],
        stats: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of processing results"""
        
        total_analyses = sum(len(results[analysis_type]) for analysis_type in results)
        total_processing_time = sum(s.get("processing_time", 0) for s in stats.values())
        
        # Calculate cache efficiency
        total_cache_read = sum(
            s.get("conversation_stats", {}).get("tokens", {}).get("cache_read", 0)
            for s in stats.values()
        )
        total_input_tokens = sum(
            s.get("conversation_stats", {}).get("tokens", {}).get("total_input", 0)
            for s in stats.values()
        )
        
        cache_hit_ratio = total_cache_read / max(total_input_tokens, 1)
        
        return {
            "stories_processed": len(stories),
            "total_analyses": total_analyses,
            "analysis_types": list(results.keys()),
            "processing_time_seconds": total_processing_time,
            "avg_time_per_story": total_processing_time / len(stories) if stories else 0,
            "cache_performance": {
                "total_input_tokens": total_input_tokens,
                "total_cache_read": total_cache_read,
                "cache_hit_ratio": cache_hit_ratio,
                "estimated_cost_savings": cache_hit_ratio * 0.9  # 90% savings on cache hits
            },
            "conversations_reused": sum(
                1 for s in stats.values() 
                if s.get("conversation_reused", False)
            )
        }
    
    async def cleanup_old_conversations(self):
        """Clean up old conversations across all agents"""
        cleanup_tasks = []
        for agent in self.agents.values():
            cleanup_tasks.append(agent.cleanup_old_conversations())
        
        await asyncio.gather(*cleanup_tasks)
        
        # Also clean up our tracking
        current_time = time.time()
        to_remove = []
        for conv_id, conv_info in self.active_conversations.items():
            age_minutes = (current_time - conv_info["created_at"]) / 60
            if age_minutes > 30:  # 30 minute max age
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            self.active_conversations.pop(conv_id, None)