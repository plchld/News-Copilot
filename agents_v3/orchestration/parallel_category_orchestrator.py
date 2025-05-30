"""Parallel category-based orchestrator with per-story agent isolation"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from agents_v3.providers.gemini_agent import GeminiAgent
from agents_v3.providers.anthropic_agent import AnthropicAgent
from agents_v3.providers.base_agent import BaseAgent, AgentConfig, AgentRole
from agents_v3.utils.enhanced_prompt_loader import enhanced_prompt_loader
from agents_v3.utils.discovery_parser import DiscoveryParser, ParsedStory
from agents_v3.conversation_logging import logger, conversation_logger, LogLevel, MessageType
from agents_v3.utils.performance_logger import get_performance_logger, init_performance_logging
import yaml
import logging

# Set up module logger
module_logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating agent instances dynamically"""
    
    @staticmethod
    def create_context_agent(story_id: str, agent_type: str = "greek") -> BaseAgent:
        """Create a context agent for a specific story
        
        Args:
            story_id: Unique story identifier
            agent_type: "greek" or "international"
            
        Returns:
            Configured agent instance
        """
        config = AgentConfig(
            name=f"{agent_type}_context_{story_id}",
            role=AgentRole.PERSPECTIVE,
            instructions="",  # Will be set dynamically
            provider="gemini",
            model="gemini-2.5-flash-preview-05-20",
            enable_search=True,
            search_threshold=0.3
        )
        
        agent = GeminiAgent(config)
        return agent
    
    @staticmethod
    def create_factcheck_agent(story_id: str) -> BaseAgent:
        """Create a fact-check agent for a specific story
        
        Args:
            story_id: Unique story identifier
            
        Returns:
            Configured agent instance
        """
        config = AgentConfig(
            name=f"factcheck_{story_id}",
            role=AgentRole.FACT_CHECK,
            instructions="",  # Will be set dynamically
            provider="gemini",
            model="gemini-2.5-flash-preview-05-20",
            enable_search=True,
            search_threshold=0.3
        )
        
        agent = GeminiAgent(config)
        return agent


class StoryProcessor:
    """Processes a single story with its own isolated agents"""
    
    def __init__(self, story: ParsedStory, message_bus):
        """Initialize story processor
        
        Args:
            story: The story to process
            message_bus: Shared message bus for agent communication
        """
        self.story = story
        self.message_bus = message_bus
        self.story_id = f"{story.category}_{story.id}"
        
        # Story-specific agents (created on demand)
        self.greek_context_agent: Optional[BaseAgent] = None
        self.intl_context_agent: Optional[BaseAgent] = None
        self.factcheck_agent: Optional[BaseAgent] = None
        
        # Results storage
        self.context_results = {}
        self.citations = []
        self.errors = []
    
    async def process(self) -> Dict[str, Any]:
        """Process the story through all phases
        
        Returns:
            Complete analysis results
        """
        module_logger.info(f"Starting processing for story: {self.story_id}")
        
        try:
            # Phase 1: Context gathering (always Greek, conditionally international)
            await self._gather_contexts()
            
            # Phase 2: Fact-checking with interrogation
            factcheck_results = await self._run_factcheck()
            
            # Phase 3: Cleanup agents to free resources
            await self._cleanup_agents()
            
            return {
                "story": self.story.to_dict(),
                "context": self.context_results,
                "factchecks": factcheck_results,
                "citations": self.citations,
                "errors": self.errors
            }
            
        except Exception as e:
            error_msg = f"Story processing failed: {str(e)}"
            module_logger.exception(f"{self.story_id}: {error_msg}")
            self.errors.append(error_msg)
            
            # Cleanup on error
            await self._cleanup_agents()
            
            return {
                "story": self.story.to_dict(),
                "context": self.context_results,
                "factchecks": {},
                "citations": self.citations,
                "errors": self.errors
            }
    
    async def _gather_contexts(self):
        """Gather Greek and optionally international context"""
        
        # Always get Greek context
        module_logger.info(f"{self.story_id}: Creating Greek context agent")
        self.greek_context_agent = AgentFactory.create_context_agent(self.story_id, "greek")
        self.greek_context_agent.set_message_bus(self.message_bus)
        
        try:
            greek_response = await self._get_greek_context()
            self.context_results["greek"] = greek_response["content"]
            
            if greek_response.get("citations"):
                for citation in greek_response["citations"]:
                    citation["source_agent"] = "greek_context"
                self.citations.extend(greek_response["citations"])
                module_logger.info(f"{self.story_id}: Found {len(greek_response['citations'])} Greek sources")
                
        except Exception as e:
            error_msg = f"Greek context failed: {str(e)}"
            self.errors.append(error_msg)
            module_logger.error(f"{self.story_id}: {error_msg}")
            self.context_results["greek"] = "Error retrieving Greek context"
        
        # Conditionally get international context
        if self.story.needs_international_context:
            module_logger.info(f"{self.story_id}: Creating international context agent")
            self.intl_context_agent = AgentFactory.create_context_agent(self.story_id, "international")
            self.intl_context_agent.set_message_bus(self.message_bus)
            
            try:
                intl_response = await self._get_international_context()
                self.context_results["international"] = intl_response["content"]
                
                if intl_response.get("citations"):
                    for citation in intl_response["citations"]:
                        citation["source_agent"] = "international_context"
                    self.citations.extend(intl_response["citations"])
                    module_logger.info(f"{self.story_id}: Found {len(intl_response['citations'])} international sources")
                    
            except Exception as e:
                error_msg = f"International context failed: {str(e)}"
                self.errors.append(error_msg)
                module_logger.error(f"{self.story_id}: {error_msg}")
                self.context_results["international"] = "Error retrieving international context"
    
    async def _get_greek_context(self) -> Dict[str, Any]:
        """Get Greek context for the story"""
        agent = self.greek_context_agent
        
        prompt = enhanced_prompt_loader.render_prompt(
            "greek_context_agent",
            {
                "story_headline": self.story.headline_greek,
                "story_summary": self.story.summary,
                "story_source": self.story.source_name,
                "stakeholders": ", ".join(self.story.stakeholders)
            }
        )
        
        conv_id = await agent.start_conversation("context")
        response = await agent.send_message(conv_id, prompt)
        await agent.end_conversation(conv_id)
        
        citations = []
        if response.metadata and "citations" in response.metadata:
            citations = response.metadata["citations"]
        
        return {
            "content": response.content,
            "citations": citations
        }
    
    async def _get_international_context(self) -> Dict[str, Any]:
        """Get international context for the story"""
        agent = self.intl_context_agent
        
        prompt = enhanced_prompt_loader.render_prompt(
            "international_context_agent",
            {
                "story_headline": self.story.headline,
                "story_summary": self.story.summary,
                "story_category": self.story.category,
                "stakeholders": ", ".join(self.story.stakeholders)
            }
        )
        
        conv_id = await agent.start_conversation("context")
        response = await agent.send_message(conv_id, prompt)
        await agent.end_conversation(conv_id)
        
        citations = []
        if response.metadata and "citations" in response.metadata:
            citations = response.metadata["citations"]
        
        return {
            "content": response.content,
            "citations": citations
        }
    
    async def _run_factcheck(self) -> Dict[str, Any]:
        """Run complete fact-check interrogation process"""
        
        # Create fact-check agent for this story
        module_logger.info(f"{self.story_id}: Creating fact-check agent")
        self.factcheck_agent = AgentFactory.create_factcheck_agent(self.story_id)
        self.factcheck_agent.set_message_bus(self.message_bus)
        
        # Combine all context responses
        context_text = "\n\n".join([
            f"=== {source.upper()} CONTEXT ===\n{content}"
            for source, content in self.context_results.items()
            if content and "Error" not in content
        ])
        
        if not context_text:
            return {"error": "No valid context available for fact-checking"}
        
        try:
            # Step 1: Get fact-check interrogator to identify claims
            prompt = enhanced_prompt_loader.render_prompt(
                "factcheck_interrogator_agent",
                {
                    "story_headline": self.story.headline_greek,
                    "context_responses": context_text
                }
            )
            
            conv_id = await self.factcheck_agent.start_conversation("factcheck")
            interrogation_response = await self.factcheck_agent.send_message(conv_id, prompt)
            
            # Step 2: Parse claims from the response
            claims = self._parse_claims_from_response(interrogation_response.content)
            
            # Step 3: For each claim, ask context agents to verify
            verified_claims = []
            for claim in claims:
                verification = await self._verify_claim(claim)
                verified_claims.append(verification)
            
            # Step 4: Compile final fact-check results
            factcheck_response = await self._compile_factcheck_results(conv_id, verified_claims)
            
            await self.factcheck_agent.end_conversation(conv_id)
            
            # Extract any additional citations
            if factcheck_response.metadata and "citations" in factcheck_response.metadata:
                for citation in factcheck_response.metadata["citations"]:
                    citation["source_agent"] = "fact_check"
                self.citations.extend(factcheck_response.metadata["citations"])
            
            return {
                "interrogation_plan": interrogation_response.content,
                "verified_claims": verified_claims,
                "summary": factcheck_response.content
            }
            
        except Exception as e:
            error_msg = f"Fact-checking failed: {str(e)}"
            self.errors.append(error_msg)
            module_logger.error(f"{self.story_id}: {error_msg}")
            return {"error": error_msg}
    
    def _parse_claims_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse claims from fact-checker's interrogation response
        
        Args:
            response_text: The interrogation plan from fact-checker
            
        Returns:
            List of claims to verify
        """
        claims = []
        
        # Simple parsing - look for numbered claims or bullet points
        lines = response_text.split('\n')
        claim_patterns = [
            r'^\d+\.\s+(.+)',  # 1. Claim text
            r'^-\s+(.+)',      # - Claim text
            r'^•\s+(.+)',      # • Claim text
            r'^Claim\s+\d+:\s+(.+)',  # Claim 1: text
        ]
        
        import re
        for line in lines:
            line = line.strip()
            for pattern in claim_patterns:
                match = re.match(pattern, line)
                if match:
                    claim_text = match.group(1).strip()
                    # Determine which agent should verify this
                    agent_type = "greek"
                    if any(word in claim_text.lower() for word in ["international", "global", "world", "foreign"]):
                        agent_type = "international" if self.intl_context_agent else "greek"
                    
                    claims.append({
                        "text": claim_text,
                        "agent_type": agent_type,
                        "original_line": line
                    })
                    break
        
        # If no structured claims found, create a general verification request
        if not claims and len(response_text) > 50:
            claims.append({
                "text": "Verify the main claims in the story",
                "agent_type": "greek",
                "original_line": "General verification"
            })
        
        module_logger.info(f"{self.story_id}: Parsed {len(claims)} claims for verification")
        return claims
    
    async def _verify_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single claim using the appropriate context agent
        
        Args:
            claim: Claim to verify with agent_type specified
            
        Returns:
            Verification result
        """
        agent_type = claim["agent_type"]
        agent = self.greek_context_agent if agent_type == "greek" else self.intl_context_agent
        
        if not agent:
            return {
                "claim": claim["text"],
                "verified": False,
                "evidence": "Agent not available",
                "sources": []
            }
        
        # Create verification prompt
        verification_prompt = f"""Please verify the following claim using search:

Claim: {claim["text"]}

Instructions:
1. Search for evidence supporting or refuting this claim
2. Find authoritative sources
3. Provide a clear verdict: TRUE, FALSE, or PARTIALLY TRUE
4. Include source links

Focus on factual verification with credible sources."""
        
        try:
            conv_id = await agent.start_conversation("verification")
            response = await agent.send_message(conv_id, verification_prompt)
            await agent.end_conversation(conv_id)
            
            # Extract citations from this verification
            sources = []
            if response.metadata and "citations" in response.metadata:
                sources = response.metadata["citations"]
                for citation in sources:
                    citation["source_agent"] = f"fact_verify_{agent_type}"
                    citation["claim_verified"] = claim["text"]
                self.citations.extend(sources)
            
            return {
                "claim": claim["text"],
                "verified": True,
                "evidence": response.content,
                "sources": sources
            }
            
        except Exception as e:
            module_logger.error(f"{self.story_id}: Failed to verify claim: {str(e)}")
            return {
                "claim": claim["text"],
                "verified": False,
                "evidence": f"Verification failed: {str(e)}",
                "sources": []
            }
    
    async def _compile_factcheck_results(self, conv_id: str, verified_claims: List[Dict[str, Any]]) -> Any:
        """Compile all verification results into a summary
        
        Args:
            conv_id: Fact-checker conversation ID
            verified_claims: List of verification results
            
        Returns:
            Compiled summary response
        """
        # Format verified claims for the fact-checker
        claims_summary = "\n\n".join([
            f"**Claim**: {vc['claim']}\n**Evidence**: {vc['evidence']}\n**Sources**: {len(vc['sources'])} found"
            for vc in verified_claims
        ])
        
        compile_prompt = f"""Based on the verification results below, provide a fact-check summary in Greek:

{claims_summary}

Create a clear, concise summary that:
1. Lists verified facts vs unverified claims
2. Highlights any false or misleading information
3. Provides overall credibility assessment
4. Cites key sources

Output in Greek for the final report."""
        
        response = await self.factcheck_agent.send_message(conv_id, compile_prompt)
        return response
    
    async def _cleanup_agents(self):
        """Clean up agent resources"""
        agents_to_cleanup = [
            self.greek_context_agent,
            self.intl_context_agent,
            self.factcheck_agent
        ]
        
        for agent in agents_to_cleanup:
            if agent:
                try:
                    # Unregister from message bus
                    if hasattr(agent, 'agent_id'):
                        self.message_bus.unregister_agent(agent.agent_id)
                except Exception as e:
                    module_logger.warning(f"Failed to cleanup agent: {str(e)}")


class ParallelCategoryOrchestrator:
    """Orchestrates parallel category-based news discovery and analysis with per-story agents"""
    
    def __init__(self):
        """Initialize the parallel orchestrator"""
        self.categories = self._load_categories()
        self.discovery_agents: Dict[str, BaseAgent] = {}
        self.synthesis_agent: Optional[BaseAgent] = None
        
        # Initialize parser
        self.discovery_parser = DiscoveryParser()
        
        # Initialize message bus
        from agents_v3.communication import message_bus
        self.message_bus = message_bus
        
        # Session tracking
        self.session_id = f"news_{int(time.time())}"
        self.discovered_stories: List[ParsedStory] = []
        
        # Error tracking
        self.pipeline_errors: Dict[str, List[str]] = {}
        
        # Concurrency control
        self.max_concurrent_stories = 5  # Process 5 stories in parallel per category
        
        # Initialize enhanced performance logging
        self.perf_logger = init_performance_logging(self.session_id)
    
    def _load_categories(self) -> Dict[str, Any]:
        """Load category configurations"""
        config_data = enhanced_prompt_loader.load_prompt("discovery_categories")
        categories_yaml = yaml.safe_load(config_data.template)
        
        categories = {}
        for cat_id, cat_data in categories_yaml["categories"].items():
            categories[cat_id] = {
                "name": cat_data["name"],
                "search_terms": cat_data["search_terms"],
                "sources": cat_data["sources"],
                "relevance_criteria": cat_data.get("international_relevance_criteria", 
                                                   cat_data.get("greek_relevance_criteria", []))
            }
        
        return categories
    
    async def initialize_agents(self):
        """Initialize discovery and synthesis agents only"""
        
        # Discovery agents - one per category
        for cat_id, cat_config in self.categories.items():
            agent_config = AgentConfig(
                name=f"discovery_{cat_id}",
                role=AgentRole.DISCOVERY,
                instructions="",  # Will be set per discovery task
                provider="gemini",
                model="gemini-2.5-flash-preview-05-20",
                enable_search=True,
                batch_size=10,
                search_threshold=0.3
            )
            
            self.discovery_agents[cat_id] = GeminiAgent(agent_config)
            self.discovery_agents[cat_id].set_message_bus(self.message_bus)
        
        # Single synthesis agent for final Greek output
        synthesis_config = AgentConfig(
            name="greek_synthesis",
            role=AgentRole.SYNTHESIS,
            instructions="",
            provider="anthropic",
            model="claude-3-5-haiku-latest",
            enable_search=False,
            cache_ttl="5m"
        )
        self.synthesis_agent = AnthropicAgent(synthesis_config)
        self.synthesis_agent.set_message_bus(self.message_bus)
        
        await self.message_bus.start()
        
        print(f"✅ Initialized {len(self.discovery_agents)} discovery agents")
        print(f"✅ Initialized synthesis agent")
        print(f"✅ Ready to spawn per-story agents on demand")
    
    async def discover_all_categories(self, date: str = "today") -> List[ParsedStory]:
        """Run discovery for all categories in parallel"""
        
        module_logger.info(f"Starting discovery for {len(self.categories)} categories on {date}")
        print(f"\n🔍 Starting discovery for {len(self.categories)} categories...")
        
        self.pipeline_errors.clear()
        
        # Create discovery tasks for all categories
        discovery_tasks = []
        for cat_id, cat_config in self.categories.items():
            task = self._discover_category_safe(cat_id, cat_config, date)
            discovery_tasks.append(task)
        
        # Run all discoveries in parallel
        results = await asyncio.gather(*discovery_tasks)
        
        # Process results
        all_stories = []
        successful_categories = 0
        
        for cat_id, (stories, errors) in zip(self.categories.keys(), results):
            if errors:
                self.pipeline_errors[f"discovery_{cat_id}"] = errors
                module_logger.error(f"Discovery errors for {cat_id}: {errors}")
            
            if stories:
                all_stories.extend(stories)
                successful_categories += 1
                print(f"  ✓ {self.categories[cat_id]['name']}: {len(stories)} stories")
            else:
                print(f"  ✗ {self.categories[cat_id]['name']}: Failed")
        
        self.discovered_stories = all_stories
        
        print(f"\n📊 Discovery Summary:")
        print(f"  • Categories processed: {successful_categories}/{len(self.categories)}")
        print(f"  • Total stories: {len(all_stories)}")
        
        return all_stories
    
    async def _discover_category_safe(self, cat_id: str, config: Dict[str, Any], date: str) -> Tuple[List[ParsedStory], List[str]]:
        """Safely discover stories with error handling"""
        try:
            return await self._discover_category(cat_id, config, date)
        except Exception as e:
            error_msg = f"Failed to discover {cat_id}: {str(e)}"
            module_logger.exception(error_msg)
            return [], [error_msg]
    
    async def _discover_category(self, cat_id: str, config: Dict[str, Any], date: str) -> Tuple[List[ParsedStory], List[str]]:
        """Discover stories for a single category"""
        
        agent = self.discovery_agents[cat_id]
        errors = []
        
        try:
            # Create discovery prompt
            prompt = enhanced_prompt_loader.render_prompt(
                "discovery_category_agent",
                {
                    "category_name": config["name"],
                    "search_terms": ", ".join(config["search_terms"]),
                    "preferred_sources": ", ".join(config["sources"]),
                    "relevance_criteria": ", ".join(config["relevance_criteria"]),
                    "date": date
                }
            )
            
            # Log conversation start
            conv_id = await agent.start_conversation("discovery")
            self.perf_logger.log_conversation_start(
                agent_name=f"discovery_{cat_id}",
                conversation_id=conv_id,
                conversation_type="discovery"
            )
            
            # Send discovery request and measure performance
            start_time = time.time()
            response = await agent.send_message(conv_id, prompt)
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log message exchange with performance metrics
            self.perf_logger.log_message_exchange(
                agent_name=f"discovery_{cat_id}",
                conversation_id=conv_id,
                message=prompt[:200],  # Preview of discovery prompt
                response=response.content[:200],  # Preview of response
                duration_ms=duration_ms,
                tokens_used=response.tokens_used,
                cost=response.cost_estimate
            )
            
            # Debug: Show raw response for immediate debugging
            print(f"🔍 Discovery response from {cat_id} ({len(response.content)} chars, {duration_ms}ms):")
            print("─" * 80)
            print(response.content[:1200])  # Show more content
            print("─" * 80)
            
            # Parse response with detailed logging
            parsing_start = time.time()
            stories, parse_errors = self.discovery_parser.parse_discovery_output(
                response.content, 
                config["name"]
            )
            parsing_duration = int((time.time() - parsing_start) * 1000)
            
            # Log parsing results
            parsing_success = len(stories) > 0 and len(parse_errors) == 0
            self.perf_logger.log_parsing_attempt(
                agent_name=f"discovery_{cat_id}",
                content=response.content,  # Full content for debugging
                success=parsing_success,
                error_msg="; ".join(parse_errors) if parse_errors else None,
                parsed_items=len(stories)
            )
            errors.extend(parse_errors)
            
            await agent.end_conversation(conv_id)
            
            return stories, errors
            
        except Exception as e:
            error_msg = f"Error in category {cat_id}: {str(e)}"
            module_logger.exception(error_msg)
            errors.append(error_msg)
            return [], errors
    
    async def process_all_stories(self) -> Dict[str, Any]:
        """Process all discovered stories in parallel with per-story agents"""
        
        print(f"\n🔄 Processing {len(self.discovered_stories)} stories with parallel agents...")
        
        # Group stories by category for better organization
        stories_by_category = {}
        for story in self.discovered_stories:
            if story.category not in stories_by_category:
                stories_by_category[story.category] = []
            stories_by_category[story.category].append(story)
        
        all_results = {}
        
        # Process each category's stories in parallel batches
        for category, stories in stories_by_category.items():
            print(f"\n📁 Processing {category} ({len(stories)} stories)...")
            
            # Process stories in batches to control concurrency
            for i in range(0, len(stories), self.max_concurrent_stories):
                batch = stories[i:i + self.max_concurrent_stories]
                batch_tasks = []
                
                for story in batch:
                    processor = StoryProcessor(story, self.message_bus)
                    batch_tasks.append(processor.process())
                
                # Process batch in parallel
                batch_results = await asyncio.gather(*batch_tasks)
                
                # Store results
                for story, result in zip(batch, batch_results):
                    story_id = f"{story.category}_{story.id}"
                    
                    # Add synthesis to each result
                    if not result.get("errors"):
                        result["synthesis"] = await self._create_synthesis_for_story(story, result)
                    
                    all_results[story_id] = result
                    
                    # Progress indication
                    if result.get("errors"):
                        print(f"  ✗ {story.headline_greek[:50]}... (errors: {len(result['errors'])})")
                    else:
                        citations_count = len(result.get("citations", []))
                        print(f"  ✓ {story.headline_greek[:50]}... ({citations_count} sources)")
        
        print(f"\n✅ Completed processing all {len(all_results)} stories")
        return all_results
    
    async def _create_synthesis_for_story(self, story: ParsedStory, result: Dict[str, Any]) -> str:
        """Create Greek synthesis for a single story"""
        
        # Format citations
        citation_text = ""
        if result.get("citations"):
            unique_citations = []
            seen_urls = set()
            
            for citation in result["citations"]:
                url = citation.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_citations.append(citation)
            
            if unique_citations:
                citation_text = f"\n\n## Πηγές ({len(unique_citations)} συνολικά)\n"
                for i, citation in enumerate(unique_citations, 1):
                    title = citation.get('title', 'Untitled')
                    url = citation.get('url', '')
                    citation_text += f"{i}. [{title}]({url})\n"
        
        # Create synthesis prompt
        prompt = enhanced_prompt_loader.render_prompt(
            "greek_synthesis_agent",
            {
                "story_headline": story.headline_greek,
                "discovery_summary": story.summary,
                "greek_context": result["context"].get("greek", "Δεν βρέθηκε"),
                "international_context": result["context"].get("international", ""),
                "factcheck_results": str(result.get("factchecks", {}))
            }
        )
        
        if citation_text:
            prompt += f"\n\nΠΗΓΕΣ ΓΙΑ ΑΝΑΦΟΡΑ:{citation_text}"
        
        conv_id = await self.synthesis_agent.start_conversation("synthesis")
        response = await self.synthesis_agent.send_message(conv_id, prompt)
        await self.synthesis_agent.end_conversation(conv_id)
        
        return response.content
    
    async def run_daily_analysis(self, date: str = "today") -> Dict[str, Any]:
        """Run the complete daily news analysis pipeline"""
        
        start_time = time.time()
        
        try:
            # Initialize agents
            await self.initialize_agents()
            
            # Phase 1: Discover all categories
            stories = await self.discover_all_categories(date)
            
            if not stories:
                return {
                    "session_id": self.session_id,
                    "date": date,
                    "total_stories": 0,
                    "results": {},
                    "errors": self.pipeline_errors,
                    "summary": {"status": "failed", "reason": "No stories discovered"}
                }
            
            # Phase 2-4: Process all stories with parallel agents
            results = await self.process_all_stories()
            
            # Calculate statistics
            end_time = time.time()
            duration_minutes = (end_time - start_time) / 60
            
            successful_stories = sum(1 for r in results.values() if not r.get("errors"))
            failed_stories = len(results) - successful_stories
            total_citations = sum(len(r.get("citations", [])) for r in results.values())
            
            # Create summary
            summary = {
                "status": "completed",
                "duration_minutes": round(duration_minutes, 2),
                "stories_discovered": len(stories),
                "stories_processed": len(results),
                "stories_successful": successful_stories,
                "stories_failed": failed_stories,
                "total_citations": total_citations,
                "agents_spawned": len(stories) * 2,  # Rough estimate
                "architecture": "parallel_per_story"
            }
            
            print("\n📊 Final Analysis Summary:")
            print(f"  • Duration: {summary['duration_minutes']} minutes")
            print(f"  • Stories processed: {summary['stories_successful']}/{summary['stories_processed']}")
            print(f"  • Total citations: {summary['total_citations']}")
            print(f"  • Agents spawned: ~{summary['agents_spawned']}")
            
            # Cleanup
            await self.message_bus.stop()
            
            # Generate and print performance report
            self.perf_logger.print_performance_report()
            
            return {
                "session_id": self.session_id,
                "date": date,
                "total_stories": len(stories),
                "results": results,
                "errors": self.pipeline_errors,
                "summary": summary,
                "performance": self.perf_logger.get_performance_summary()
            }
            
        except Exception as e:
            module_logger.exception(f"Critical error in daily analysis: {e}")
            
            try:
                await self.message_bus.stop()
            except:
                pass
                
            return {
                "session_id": self.session_id,
                "date": date,
                "total_stories": 0,
                "results": {},
                "errors": {**self.pipeline_errors, "critical": str(e)},
                "summary": {"status": "failed", "reason": str(e)}
            }