"""Main orchestrator for multi-agent news intelligence system"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from ..agents.discovery import DiscoveryAgent, DISCOVERY_CATEGORIES
from ..agents.perspectives import (
    GreekPerspectiveAgent,
    InternationalPerspectiveAgent,
    OpposingViewAgent,
    FactVerificationAgent
)
from ..agents.synthesis import (
    NarrativeSynthesisAgent,
    JargonContextAgent,
    TimelineAgent
)
from ..agents.social_pulse import SocialPulseAgent
from .orchestration_config import OrchestrationConfig, StorySelectionCriteria, StoryPriority

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class StoryIntelligence:
    """Complete intelligence for a single story"""
    story_id: str
    headline: str
    category: str
    priority: StoryPriority
    
    # Discovery data
    discovery_data: Dict[str, Any]
    
    # Perspectives
    perspectives: Dict[str, Any] = field(default_factory=dict)
    
    # Synthesis
    narrative: Optional[Dict[str, Any]] = None
    jargon: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    
    # Social
    social_pulse: Optional[Dict[str, Any]] = None
    
    # Metadata
    processing_time: float = 0.0
    completeness_score: float = 0.0
    errors: List[str] = field(default_factory=list)


class NewsIntelligenceOrchestrator:
    """Orchestrates multi-agent news analysis pipeline"""
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        """Initialize orchestrator
        
        Args:
            config: Orchestration configuration
        """
        self.config = config or OrchestrationConfig()
        self.selection_criteria = StorySelectionCriteria()
        
        # Initialize agents (lazy loading)
        self._agents_initialized = False
        self._discovery_agents: Dict[str, DiscoveryAgent] = {}
        self._perspective_agents: Dict[str, Any] = {}
        self._synthesis_agents: Dict[str, Any] = {}
        self._social_agent: Optional[SocialPulseAgent] = None
        
    async def _initialize_agents(self):
        """Initialize all agents with configured providers"""
        if self._agents_initialized:
            return
        
        # Discovery agents
        for category_key, category_config in DISCOVERY_CATEGORIES.items():
            if category_key in self.config.categories_to_scan:
                self._discovery_agents[category_key] = DiscoveryAgent(
                    category_config,
                    provider=self.config.discovery_provider
                )
        
        # Perspective agents
        self._perspective_agents = {
            "greek": GreekPerspectiveAgent(self.config.greek_perspective_provider),
            "international": InternationalPerspectiveAgent(self.config.international_provider),
            "opposing": OpposingViewAgent(self.config.opposing_view_provider),
            "facts": FactVerificationAgent(self.config.fact_check_provider)
        }
        
        # Synthesis agents
        self._synthesis_agents = {
            "narrative": NarrativeSynthesisAgent(self.config.synthesis_provider),
            "jargon": JargonContextAgent(self.config.jargon_provider),
            "timeline": TimelineAgent(self.config.timeline_provider)
        }
        
        # Social agent
        self._social_agent = SocialPulseAgent(self.config.social_provider)
        
        self._agents_initialized = True
        logger.info("All agents initialized successfully")
    
    async def generate_daily_intelligence(self,
                                        focus_topics: Optional[List[str]] = None,
                                        priority_categories: Optional[List[str]] = None
                                        ) -> Dict[str, Any]:
        """Generate complete daily news intelligence
        
        Args:
            focus_topics: Optional specific topics to prioritize
            priority_categories: Optional categories to prioritize
            
        Returns:
            Complete intelligence report
        """
        start_time = datetime.now()
        
        # Initialize agents
        await self._initialize_agents()
        
        # Phase 1: Discovery
        logger.info("Phase 1: Starting discovery across categories")
        discovered_stories = await self._phase1_discovery(priority_categories)
        
        # Select stories for deep analysis
        selected_stories = self._select_stories_for_analysis(
            discovered_stories,
            focus_topics
        )
        
        logger.info(f"Selected {len(selected_stories)} stories for deep analysis")
        
        # Phase 2-4: Deep analysis for each story
        story_intelligences = []
        
        # Process stories with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 stories in parallel
        
        async def process_story(story_data: Tuple[str, Dict]):
            async with semaphore:
                story_id, story = story_data
                intelligence = await self._analyze_story(story_id, story)
                return intelligence
        
        # Process all stories
        tasks = [process_story(story) for story in selected_stories]
        story_intelligences = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_intelligences = []
        for intel in story_intelligences:
            if isinstance(intel, Exception):
                logger.error(f"Story processing failed: {intel}")
            else:
                valid_intelligences.append(intel)
        
        # Generate final report
        processing_time = (datetime.now() - start_time).total_seconds()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
            "configuration": {
                "categories_scanned": self.config.categories_to_scan,
                "stories_analyzed": len(valid_intelligences),
                "providers_used": {
                    "discovery": self.config.discovery_provider,
                    "synthesis": self.config.synthesis_provider
                }
            },
            "stories": [self._format_story_output(intel) for intel in valid_intelligences],
            "summary": self._generate_executive_summary(valid_intelligences)
        }
        
        logger.info(f"Intelligence generation completed in {processing_time:.1f} seconds")
        
        return report
    
    async def _phase1_discovery(self, 
                              priority_categories: Optional[List[str]] = None
                              ) -> Dict[str, List[Dict]]:
        """Phase 1: Discover stories across categories
        
        Args:
            priority_categories: Categories to prioritize
            
        Returns:
            Dict mapping category to discovered stories
        """
        discovered_stories = {}
        
        # Determine which categories to scan
        categories_to_scan = priority_categories or self.config.categories_to_scan
        
        # Run discovery in parallel
        discovery_tasks = []
        for category in categories_to_scan:
            if category in self._discovery_agents:
                agent = self._discovery_agents[category]
                task = agent.discover(time_range=self.config.discovery_time_range)
                discovery_tasks.append((category, task))
        
        # Gather results
        results = await asyncio.gather(
            *[task for _, task in discovery_tasks],
            return_exceptions=True
        )
        
        # Process results
        for (category, _), result in zip(discovery_tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Discovery failed for {category}: {result}")
                discovered_stories[category] = []
            else:
                # Rank stories within category
                ranked_stories = self._discovery_agents[category].rank_stories(
                    result.stories
                )
                discovered_stories[category] = [
                    story.model_dump() for story in ranked_stories[:self.config.max_stories_per_category]
                ]
        
        return discovered_stories
    
    def _select_stories_for_analysis(self,
                                   discovered_stories: Dict[str, List[Dict]],
                                   focus_topics: Optional[List[str]] = None
                                   ) -> List[Tuple[str, Dict]]:
        """Select top stories for deep analysis
        
        Args:
            discovered_stories: Stories by category
            focus_topics: Optional topics to prioritize
            
        Returns:
            List of (story_id, story_data) tuples
        """
        # Flatten all stories with metadata
        all_stories = []
        for category, stories in discovered_stories.items():
            for idx, story in enumerate(stories):
                story_id = f"{category}_{idx}_{datetime.now().strftime('%Y%m%d')}"
                story_with_meta = {
                    **story,
                    "story_id": story_id,
                    "category": category
                }
                all_stories.append((story_id, story_with_meta))
        
        # Apply selection criteria
        eligible_stories = [
            (sid, story) for sid, story in all_stories
            if self.selection_criteria.meets_criteria(story)
        ]
        
        # Calculate priorities
        story_priorities = []
        for sid, story in eligible_stories:
            priority_score = self.selection_criteria.calculate_priority(story)
            
            # Boost for focus topics
            if focus_topics:
                headline_lower = story["headline"].lower()
                for topic in focus_topics:
                    if topic.lower() in headline_lower:
                        priority_score += 0.2
                        break
            
            story_priorities.append((sid, story, priority_score))
        
        # Sort by priority and select top stories
        story_priorities.sort(key=lambda x: x[2], reverse=True)
        selected = story_priorities[:self.config.max_stories_to_analyze]
        
        return [(sid, story) for sid, story, _ in selected]
    
    async def _analyze_story(self, story_id: str, story_data: Dict) -> StoryIntelligence:
        """Analyze a single story through all phases
        
        Args:
            story_id: Unique story identifier
            story_data: Story discovery data
            
        Returns:
            Complete StoryIntelligence
        """
        start_time = datetime.now()
        
        intelligence = StoryIntelligence(
            story_id=story_id,
            headline=story_data["headline"],
            category=story_data["category"],
            priority=self._calculate_story_priority(story_data),
            discovery_data=story_data
        )
        
        try:
            # Phase 2: Multi-perspective analysis
            perspectives = await self._phase2_perspectives(story_data)
            intelligence.perspectives = perspectives
            
            # Phase 3: Synthesis
            synthesis_results = await self._phase3_synthesis(
                story_data,
                perspectives
            )
            intelligence.narrative = synthesis_results.get("narrative")
            intelligence.jargon = synthesis_results.get("jargon")
            intelligence.timeline = synthesis_results.get("timeline")
            
            # Phase 4: Social pulse (optional)
            if self.config.include_social_pulse:
                intelligence.social_pulse = await self._phase4_social_pulse(story_data)
            
            # Calculate completeness
            intelligence.completeness_score = self._calculate_completeness(intelligence)
            
        except Exception as e:
            logger.error(f"Error analyzing story {story_id}: {e}")
            intelligence.errors.append(str(e))
        
        intelligence.processing_time = (datetime.now() - start_time).total_seconds()
        
        return intelligence
    
    async def _phase2_perspectives(self, story_data: Dict) -> Dict[str, Any]:
        """Phase 2: Gather multiple perspectives
        
        Args:
            story_data: Story information
            
        Returns:
            Dictionary of perspectives
        """
        topic_summary = f"{story_data['headline']}. {story_data['why_important']}"
        
        # Run perspective agents in parallel
        tasks = {
            "greek": self._perspective_agents["greek"].analyze(
                topic_summary,
                story_headline=story_data["headline"],
                key_facts=story_data.get("key_facts", [])
            ),
            "international": self._perspective_agents["international"].analyze(
                topic_summary,
                story_category=story_data["category"]
            ),
            "opposing": self._perspective_agents["opposing"].analyze(
                topic_summary,
                claimed_facts=story_data.get("key_facts", [])
            ),
            "facts": self._perspective_agents["facts"].verify(
                topic_summary,
                claims_to_verify=story_data.get("key_facts", [])
            )
        }
        
        # Gather with timeout
        results = {}
        for name, task in tasks.items():
            try:
                result = await asyncio.wait_for(
                    task,
                    timeout=self.config.agent_timeout_seconds
                )
                results[name] = result.model_dump() if hasattr(result, 'model_dump') else result
            except asyncio.TimeoutError:
                logger.warning(f"Perspective agent {name} timed out")
                results[name] = {"error": "timeout"}
            except Exception as e:
                logger.error(f"Perspective agent {name} failed: {e}")
                results[name] = {"error": str(e)}
        
        return results
    
    async def _phase3_synthesis(self,
                              story_data: Dict,
                              perspectives: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Synthesize and enrich
        
        Args:
            story_data: Story information
            perspectives: Gathered perspectives
            
        Returns:
            Synthesis results
        """
        results = {}
        
        # Narrative synthesis (required)
        try:
            narrative = await self._synthesis_agents["narrative"].synthesize(
                topic=story_data["headline"],
                perspectives=perspectives,
                verified_facts=perspectives.get("facts", {}).get("analysis", {}).get("verified_facts", [])
            )
            results["narrative"] = narrative.model_dump()
        except Exception as e:
            logger.error(f"Narrative synthesis failed: {e}")
            results["narrative"] = {"error": str(e)}
        
        # Jargon analysis (optional)
        if self.config.include_jargon and "narrative" in results:
            try:
                main_text = results["narrative"].get("narrative", {}).get("main_narrative", "")
                if main_text:
                    jargon = await self._synthesis_agents["jargon"].process(main_text)
                    results["jargon"] = jargon.model_dump()
            except Exception as e:
                logger.error(f"Jargon analysis failed: {e}")
        
        # Timeline (optional)
        if self.config.include_timeline:
            try:
                timeline = await self._synthesis_agents["timeline"].build_timeline(
                    topic_summary=f"{story_data['headline']}. {story_data['why_important']}"
                )
                results["timeline"] = timeline.model_dump()
            except Exception as e:
                logger.error(f"Timeline building failed: {e}")
        
        return results
    
    async def _phase4_social_pulse(self, story_data: Dict) -> Optional[Dict[str, Any]]:
        """Phase 4: Analyze social media pulse
        
        Args:
            story_data: Story information
            
        Returns:
            Social pulse analysis or None
        """
        try:
            result = await self._social_agent.analyze(
                topic_summary=story_data["headline"],
                time_window="24h"
            )
            return result.model_dump()
        except Exception as e:
            logger.error(f"Social pulse analysis failed: {e}")
            return None
    
    def _calculate_story_priority(self, story_data: Dict) -> StoryPriority:
        """Calculate story priority level
        
        Args:
            story_data: Story information
            
        Returns:
            StoryPriority enum value
        """
        score = self.selection_criteria.calculate_priority(story_data)
        
        if score >= 0.8:
            return StoryPriority.URGENT
        elif score >= 0.6:
            return StoryPriority.HIGH
        elif score >= 0.4:
            return StoryPriority.MEDIUM
        else:
            return StoryPriority.LOW
    
    def _calculate_completeness(self, intelligence: StoryIntelligence) -> float:
        """Calculate completeness score for story intelligence
        
        Args:
            intelligence: Story intelligence data
            
        Returns:
            Completeness score (0.0-1.0)
        """
        components = {
            "perspectives": 0.4,  # 40% weight
            "narrative": 0.3,     # 30% weight
            "timeline": 0.1,      # 10% weight
            "jargon": 0.1,        # 10% weight
            "social": 0.1         # 10% weight
        }
        
        score = 0.0
        
        # Check perspectives
        if intelligence.perspectives:
            valid_perspectives = sum(
                1 for p in ["greek", "international", "opposing", "facts"]
                if p in intelligence.perspectives and "error" not in intelligence.perspectives[p]
            )
            score += components["perspectives"] * (valid_perspectives / 4)
        
        # Check narrative
        if intelligence.narrative and "error" not in intelligence.narrative:
            score += components["narrative"]
        
        # Check optional components
        if intelligence.timeline and "error" not in intelligence.timeline:
            score += components["timeline"]
        
        if intelligence.jargon and "error" not in intelligence.jargon:
            score += components["jargon"]
        
        if intelligence.social_pulse:
            score += components["social"]
        
        return min(score, 1.0)
    
    def _format_story_output(self, intelligence: StoryIntelligence) -> Dict[str, Any]:
        """Format story intelligence for output
        
        Args:
            intelligence: Story intelligence data
            
        Returns:
            Formatted output
        """
        return {
            "id": intelligence.story_id,
            "headline": intelligence.headline,
            "category": intelligence.category,
            "priority": intelligence.priority.value,
            "greek_relevance": intelligence.discovery_data.get("greek_relevance", 0),
            "narrative": intelligence.narrative,
            "perspectives": intelligence.perspectives,
            "jargon": intelligence.jargon,
            "timeline": intelligence.timeline,
            "social_pulse": intelligence.social_pulse,
            "metadata": {
                "processing_time": intelligence.processing_time,
                "completeness_score": intelligence.completeness_score,
                "errors": intelligence.errors
            }
        }
    
    def _generate_executive_summary(self, intelligences: List[StoryIntelligence]) -> Dict[str, Any]:
        """Generate executive summary of all stories
        
        Args:
            intelligences: List of story intelligences
            
        Returns:
            Executive summary
        """
        # Group by category
        by_category = {}
        for intel in intelligences:
            cat = intel.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(intel)
        
        # Count priorities
        priority_counts = {
            "urgent": sum(1 for i in intelligences if i.priority == StoryPriority.URGENT),
            "high": sum(1 for i in intelligences if i.priority == StoryPriority.HIGH),
            "medium": sum(1 for i in intelligences if i.priority == StoryPriority.MEDIUM),
            "low": sum(1 for i in intelligences if i.priority == StoryPriority.LOW)
        }
        
        # Calculate averages
        avg_completeness = sum(i.completeness_score for i in intelligences) / len(intelligences) if intelligences else 0
        avg_processing_time = sum(i.processing_time for i in intelligences) / len(intelligences) if intelligences else 0
        
        return {
            "total_stories": len(intelligences),
            "by_category": {cat: len(stories) for cat, stories in by_category.items()},
            "priority_distribution": priority_counts,
            "average_completeness": round(avg_completeness, 2),
            "average_processing_time": round(avg_processing_time, 1),
            "top_stories": [
                {
                    "headline": intel.headline,
                    "category": intel.category,
                    "priority": intel.priority.value
                }
                for intel in sorted(intelligences, key=lambda x: x.priority.value)[:3]
            ]
        }