"""Category-based orchestrator with conditional agent activation"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from agents_v3.providers.gemini_agent import GeminiAgent
from agents_v3.providers.anthropic_agent import AnthropicAgent
from agents_v3.providers.base_agent import BaseAgent, AgentConfig, AgentRole
from agents_v3.utils.enhanced_prompt_loader import enhanced_prompt_loader
from agents_v3.utils.discovery_parser import DiscoveryParser, ParsedStory
from agents_v3.conversation_logging import logger, conversation_logger, LogLevel, MessageType
import yaml
import logging

# Set up module logger
module_logger = logging.getLogger(__name__)


@dataclass
class NewsStory:
    """Represents a discovered news story"""
    id: str
    category: str
    headline: str
    summary: str
    source: str
    url: str
    timestamp: str
    stakeholders: List[str]
    international_relevance_score: int
    
    @property
    def needs_international_context(self) -> bool:
        """Determine if international context is needed"""
        if self.category in ["science", "technology"]:
            return True  # Always need international context
        elif self.category.startswith("greek_"):
            return self.international_relevance_score >= 7
        else:  # international news
            return False  # Already international
    
    @property
    def needs_greek_context(self) -> bool:
        """Determine if Greek context is needed"""
        return True  # Always get Greek perspectives


@dataclass
class CategoryConfig:
    """Configuration for a news category"""
    name: str
    search_terms: List[str]
    sources: List[str]
    relevance_criteria: List[str]


class CategoryOrchestrator:
    """Orchestrates category-based news discovery and analysis"""
    
    def __init__(self):
        """Initialize the category orchestrator"""
        self.categories = self._load_categories()
        self.discovery_agents: Dict[str, BaseAgent] = {}
        self.context_agents: Dict[str, BaseAgent] = {}
        self.factcheck_agent: Optional[BaseAgent] = None
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
        
    def _load_categories(self) -> Dict[str, CategoryConfig]:
        """Load category configurations"""
        config_data = enhanced_prompt_loader.load_prompt("discovery_categories")
        categories_yaml = yaml.safe_load(config_data.template)
        
        categories = {}
        for cat_id, cat_data in categories_yaml["categories"].items():
            categories[cat_id] = CategoryConfig(
                name=cat_data["name"],
                search_terms=cat_data["search_terms"],
                sources=cat_data["sources"],
                relevance_criteria=cat_data.get("international_relevance_criteria", 
                                                cat_data.get("greek_relevance_criteria", []))
            )
        
        return categories
    
    async def initialize_agents(self):
        """Initialize all required agents with configured models and providers"""
        
        # Discovery agents - Gemini 2.5 Flash with search
        for cat_id, cat_config in self.categories.items():
            agent_config = AgentConfig(
                name=f"discovery_{cat_id}",
                role=AgentRole.DISCOVERY,
                instructions="",  # Will be set per discovery task
                provider="gemini",
                model="gemini-2.5-flash-preview-05-20",
                enable_search=True,
                batch_size=10,
                # Low search threshold to ensure searches are triggered
                search_threshold=0.3
            )
            
            self.discovery_agents[cat_id] = GeminiAgent(agent_config)
            self.discovery_agents[cat_id].set_message_bus(self.message_bus)
        
        # Greek Context Agent - Gemini 2.5 Flash for alternative viewpoints
        # Note: Instructions will be set dynamically per story
        greek_context_config = AgentConfig(
            name="greek_context",
            role=AgentRole.PERSPECTIVE,
            instructions="",  # Will be set per story with actual variables
            provider="gemini",
            model="gemini-2.5-flash-preview-05-20",
            enable_search=True,
            search_threshold=0.3
        )
        self.context_agents["greek"] = GeminiAgent(greek_context_config)
        
        # International Context Agent - Gemini 2.5 Flash for alternative viewpoints
        # Note: Instructions will be set dynamically per story
        intl_context_config = AgentConfig(
            name="international_context",
            role=AgentRole.PERSPECTIVE,
            instructions="",  # Will be set per story with actual variables
            provider="gemini",
            model="gemini-2.5-flash-preview-05-20",
            enable_search=True,
            search_threshold=0.3
        )
        self.context_agents["international"] = GeminiAgent(intl_context_config)
        
        # Fact-check interrogator - Gemini 2.5 Flash
        # Note: Instructions will be set dynamically per story
        factcheck_config = AgentConfig(
            name="factcheck_interrogator",
            role=AgentRole.FACT_CHECK,
            instructions="",  # Will be set per story with actual variables
            provider="gemini",
            model="gemini-2.5-flash-preview-05-20",
            enable_search=True,
            search_threshold=0.3
        )
        self.factcheck_agent = GeminiAgent(factcheck_config)
        
        # Synthesis agent - Anthropic Claude for final Greek output
        # Note: Instructions will be set dynamically per story
        synthesis_config = AgentConfig(
            name="greek_synthesis",
            role=AgentRole.SYNTHESIS,
            instructions="",  # Will be set per story with actual variables
            provider="anthropic",
            model="claude-3-5-haiku-latest",
            enable_search=False,
            cache_ttl="5m"
        )
        self.synthesis_agent = AnthropicAgent(synthesis_config)
        
        # Register all agents with message bus
        for agent in [*self.context_agents.values(), self.factcheck_agent, self.synthesis_agent]:
            agent.set_message_bus(self.message_bus)
        
        await self.message_bus.start()
        
        print(f"✅ Initialized {len(self.discovery_agents)} discovery agents")
        print(f"✅ Initialized {len(self.context_agents)} context agents")
        print(f"✅ Initialized fact-check and synthesis agents")
    
    async def discover_all_categories(self, date: str = "today") -> List[ParsedStory]:
        """Run discovery for all categories in parallel with error handling"""
        
        module_logger.info(f"Starting discovery for {len(self.categories)} categories on {date}")
        print(f"\n🔍 Starting discovery for {len(self.categories)} categories...")
        
        # Clear previous errors
        self.pipeline_errors.clear()
        
        # Create discovery tasks for all categories
        discovery_tasks = []
        for cat_id, cat_config in self.categories.items():
            task = self._discover_category_safe(cat_id, cat_config, date)
            discovery_tasks.append(task)
        
        # Run all discoveries in parallel
        results = await asyncio.gather(*discovery_tasks)
        
        # Flatten results and count successes/failures
        all_stories = []
        successful_categories = 0
        
        for cat_id, (stories, errors) in zip(self.categories.keys(), results):
            if errors:
                self.pipeline_errors[f"discovery_{cat_id}"] = errors
                module_logger.error(f"Discovery errors for {cat_id}: {errors}")
            
            if stories:
                all_stories.extend(stories)
                successful_categories += 1
                print(f"  ✓ {self.categories[cat_id].name}: {len(stories)} stories")
            else:
                print(f"  ✗ {self.categories[cat_id].name}: Failed")
        
        self.discovered_stories = all_stories
        
        print(f"\n📊 Discovery Summary:")
        print(f"  • Categories processed: {successful_categories}/{len(self.categories)}")
        print(f"  • Total stories: {len(all_stories)}")
        print(f"  • Expected stories: {len(self.categories) * 10}")
        
        if self.pipeline_errors:
            print(f"  • Errors encountered: {len(self.pipeline_errors)}")
        
        return all_stories
    
    async def _discover_category_safe(self, cat_id: str, config: CategoryConfig, date: str) -> Tuple[List[ParsedStory], List[str]]:
        """Safely discover stories with error handling"""
        try:
            return await self._discover_category(cat_id, config, date)
        except Exception as e:
            error_msg = f"Failed to discover {cat_id}: {str(e)}"
            module_logger.exception(error_msg)
            return [], [error_msg]
    
    async def _discover_category(self, cat_id: str, config: CategoryConfig, date: str) -> Tuple[List[ParsedStory], List[str]]:
        """Discover stories for a single category with robust parsing"""
        
        agent = self.discovery_agents[cat_id]
        errors = []
        
        try:
            # Create discovery prompt
            prompt = enhanced_prompt_loader.render_prompt(
                "discovery_category_agent",
                {
                    "category_name": config.name,
                    "search_terms": ", ".join(config.search_terms),
                    "preferred_sources": ", ".join(config.sources),
                    "relevance_criteria": ", ".join(config.relevance_criteria),
                    "date": date
                }
            )
            
            # Start conversation and discover
            conv_id = await agent.start_conversation("discovery")
            
            module_logger.info(f"Sending discovery request for {cat_id}")
            response = await agent.send_message(conv_id, prompt)
            
            # Log raw response for debugging
            module_logger.debug(f"Raw response from {cat_id}: {response.content[:500]}...")
            
            # Parse response with fault tolerance
            stories, parse_errors = self.discovery_parser.parse_discovery_output(
                response.content, 
                config.name
            )
            errors.extend(parse_errors)
            
            # Validate the batch
            is_valid, validation_issues = self.discovery_parser.validate_story_batch(stories)
            if not is_valid:
                errors.extend(validation_issues)
            
            await agent.end_conversation(conv_id)
            
            # Log success metrics
            module_logger.info(f"Discovery {cat_id}: {len(stories)} stories parsed, {len(errors)} errors")
            
            return stories, errors
            
        except Exception as e:
            error_msg = f"Error in category {cat_id}: {str(e)}"
            module_logger.exception(error_msg)
            errors.append(error_msg)
            return [], errors
    
    async def process_all_stories(self) -> Dict[str, Any]:
        """Process all discovered stories through the pipeline"""
        
        print(f"\n🔄 Processing {len(self.discovered_stories)} stories...")
        
        results = {}
        for story in self.discovered_stories:
            result = await self._process_single_story(story)
            results[story.id] = result
        
        return results
    
    async def _process_single_story(self, story: ParsedStory) -> Dict[str, Any]:
        """Process a single story through conditional pipeline with error handling and citation tracking"""
        
        story_id = f"{story.category}_{story.id}"
        module_logger.info(f"Processing story: {story_id}")
        
        print(f"\n📰 Processing: {story.headline_greek}")
        print(f"   Category: {story.category}")
        print(f"   International relevance: {story.international_relevance_score}/10")
        print(f"   Source: {story.source_name}")
        
        errors = []
        context_results = {}
        all_citations = []  # Collect citations from all agents
        
        try:
            # Phase 1: Context gathering (always Greek)
            print("   ✓ Activating Greek context agent")
            try:
                greek_response = await self._get_greek_context_with_citations(story)
                context_results["greek"] = greek_response["content"]
                
                # Extract citations if present
                if greek_response.get("citations"):
                    # Add source agent metadata
                    for citation in greek_response["citations"]:
                        citation["source_agent"] = "greek_context"
                    all_citations.extend(greek_response["citations"])
                    print(f"     Found {len(greek_response['citations'])} Greek sources")
                    
            except Exception as e:
                error_msg = f"Greek context failed: {str(e)}"
                errors.append(error_msg)
                module_logger.error(f"{story_id}: {error_msg}")
                context_results["greek"] = "Error retrieving Greek context"
            
            # Conditionally get international context
            if story.needs_international_context:
                print("   ✓ Activating international context agent")
                try:
                    intl_response = await self._get_international_context_with_citations(story)
                    context_results["international"] = intl_response["content"]
                    
                    # Extract citations if present
                    if intl_response.get("citations"):
                        # Add source agent metadata
                        for citation in intl_response["citations"]:
                            citation["source_agent"] = "international_context"
                        all_citations.extend(intl_response["citations"])
                        print(f"     Found {len(intl_response['citations'])} international sources")
                        
                except Exception as e:
                    error_msg = f"International context failed: {str(e)}"
                    errors.append(error_msg)
                    module_logger.error(f"{story_id}: {error_msg}")
                    context_results["international"] = "Error retrieving international context"
            else:
                print("   ✗ Skipping international context (relevance score: {})".format(
                    story.international_relevance_score))
            
            # Phase 2: Fact-checking through interrogation
            factcheck_results = {}
            try:
                factcheck_response = await self._run_factcheck_interrogation_with_citations(story, context_results)
                factcheck_results = factcheck_response.get("results", {})
                
                # Extract fact-check citations
                if factcheck_response.get("citations"):
                    # Add source agent metadata
                    for citation in factcheck_response["citations"]:
                        citation["source_agent"] = "fact_check"
                    all_citations.extend(factcheck_response["citations"])
                    print(f"   ✓ Fact-check found {len(factcheck_response['citations'])} verification sources")
                    
            except Exception as e:
                error_msg = f"Fact-checking failed: {str(e)}"
                errors.append(error_msg)
                module_logger.error(f"{story_id}: {error_msg}")
                factcheck_results = {"error": error_msg}
            
            # Phase 3: Greek synthesis with all citations
            final_synthesis = ""
            try:
                # Pass all collected citations to synthesis
                final_synthesis = await self._create_greek_synthesis_with_citations(
                    story, context_results, factcheck_results, all_citations
                )
            except Exception as e:
                error_msg = f"Synthesis failed: {str(e)}"
                errors.append(error_msg)
                module_logger.error(f"{story_id}: {error_msg}")
                final_synthesis = f"Error creating synthesis: {str(e)}"
            
            # Store any errors
            if errors:
                self.pipeline_errors[story_id] = errors
            
            # Log citation summary
            if all_citations:
                module_logger.info(f"Story {story_id}: Total {len(all_citations)} citations collected")
            
            return {
                "story": story.to_dict(),
                "context": context_results,
                "factchecks": factcheck_results,
                "synthesis": final_synthesis,
                "citations": all_citations,  # Include all citations
                "errors": errors
            }
            
        except Exception as e:
            error_msg = f"Story processing failed completely: {str(e)}"
            module_logger.exception(f"{story_id}: {error_msg}")
            return {
                "story": story.to_dict(),
                "context": {},
                "factchecks": {},
                "synthesis": "",
                "errors": [error_msg]
            }
    
    async def _get_greek_context(self, story: ParsedStory) -> str:
        """Get Greek context for a story (legacy method without citations)"""
        response = await self._get_greek_context_with_citations(story)
        return response["content"]
    
    async def _get_greek_context_with_citations(self, story: ParsedStory) -> Dict[str, Any]:
        """Get Greek context for a story with citation tracking"""
        agent = self.context_agents["greek"]
        
        prompt = enhanced_prompt_loader.render_prompt(
            "greek_context_agent",
            {
                "story_headline": story.headline_greek,
                "story_summary": story.summary,
                "story_source": story.source_name,
                "stakeholders": ", ".join(story.stakeholders)
            }
        )
        
        conv_id = await agent.start_conversation("context")
        response = await agent.send_message(conv_id, prompt)
        await agent.end_conversation(conv_id)
        
        # Extract citations from metadata if present
        citations = []
        if response.metadata and "citations" in response.metadata:
            citations = response.metadata["citations"]
        
        return {
            "content": response.content,
            "citations": citations
        }
    
    async def _get_international_context(self, story: ParsedStory) -> str:
        """Get international context for a story (legacy method without citations)"""
        response = await self._get_international_context_with_citations(story)
        return response["content"]
    
    async def _get_international_context_with_citations(self, story: ParsedStory) -> Dict[str, Any]:
        """Get international context for a story with citation tracking"""
        agent = self.context_agents["international"]
        
        prompt = enhanced_prompt_loader.render_prompt(
            "international_context_agent",
            {
                "story_headline": story.headline,
                "story_summary": story.summary,
                "story_category": story.category,
                "stakeholders": ", ".join(story.stakeholders)
            }
        )
        
        conv_id = await agent.start_conversation("context")
        response = await agent.send_message(conv_id, prompt)
        await agent.end_conversation(conv_id)
        
        # Extract citations from metadata if present
        citations = []
        if response.metadata and "citations" in response.metadata:
            citations = response.metadata["citations"]
        
        return {
            "content": response.content,
            "citations": citations
        }
    
    async def _run_factcheck_interrogation(self, story: ParsedStory, context_results: Dict[str, str]) -> Dict[str, Any]:
        """Run fact-check interrogation process (legacy method without citations)"""
        response = await self._run_factcheck_interrogation_with_citations(story, context_results)
        return response.get("results", {})
    
    async def _run_factcheck_interrogation_with_citations(self, story: ParsedStory, context_results: Dict[str, str]) -> Dict[str, Any]:
        """Run fact-check interrogation process with citation tracking"""
        
        # Combine all context responses
        context_text = "\n\n".join([
            f"=== {source.upper()} CONTEXT ===\n{content}"
            for source, content in context_results.items()
            if content and "Error" not in content
        ])
        
        if not context_text:
            return {"results": {"error": "No valid context available for fact-checking"}, "citations": []}
        
        # Get fact-check interrogator to identify claims
        prompt = enhanced_prompt_loader.render_prompt(
            "factcheck_interrogator_agent",
            {
                "story_headline": story.headline_greek,
                "context_responses": context_text
            }
        )
        
        conv_id = await self.factcheck_agent.start_conversation("factcheck")
        interrogation_response = await self.factcheck_agent.send_message(conv_id, prompt)
        
        # Parse claims and queries from response
        # In production, this would parse structured output
        # For now, return the interrogation plan
        
        # TODO: Implement actual interrogation loop where:
        # 1. Parse claims from interrogation_response
        # 2. For each claim, ask the relevant context agent to search
        # 3. Compile all fact-check results
        
        await self.factcheck_agent.end_conversation(conv_id)
        
        # Extract citations from metadata if present
        citations = []
        if interrogation_response.metadata and "citations" in interrogation_response.metadata:
            citations = interrogation_response.metadata["citations"]
        
        return {
            "results": {
                "interrogation_plan": interrogation_response.content,
                "verified_claims": []  # TODO: Implement actual verification
            },
            "citations": citations
        }
    
    async def _create_greek_synthesis(self, story: ParsedStory, context_results: Dict[str, str], 
                                     factcheck_results: Dict[str, Any]) -> str:
        """Create final Greek synthesis (legacy method without citations)"""
        response = await self._create_greek_synthesis_with_citations(
            story, context_results, factcheck_results, []
        )
        return response
    
    async def _create_greek_synthesis_with_citations(self, story: ParsedStory, context_results: Dict[str, str], 
                                     factcheck_results: Dict[str, Any], all_citations: List[Dict[str, Any]]) -> str:
        """Create final Greek synthesis with citation attribution from all Gemini agents"""
        
        # Format ALL citations transparently - no filtering or selection
        citation_text = ""
        if all_citations:
            # Simple deduplication by URL only
            unique_citations = []
            seen_urls = set()
            seen_domains = set()
            
            for citation in all_citations:
                url = citation.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_citations.append(citation)
                    
                    # Track domains for statistics
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc.replace('www.', '')
                        seen_domains.add(domain)
                    except:
                        pass
            
            # Create transparent citation list
            if unique_citations:
                citation_text = f"\n\n## Πηγές Αναφοράς - Πλήρης Διαφάνεια\n"
                citation_text += f"_Συνολικά {len(unique_citations)} μοναδικές πηγές από {len(seen_domains)} διαφορετικά domains_\n\n"
                
                # Primary source first
                citation_text += f"**Πρωτογενής Πηγή:**\n"
                citation_text += f"• [{story.source_name}]({story.url})\n\n"
                
                # All other sources in order found
                citation_text += f"**Όλες οι Πηγές που Χρησιμοποιήθηκαν:**\n"
                for i, citation in enumerate(unique_citations, 1):
                    source_agent = citation.get('source_agent', 'unknown')
                    title = citation.get('title', 'Untitled')
                    url = citation.get('url', '')
                    
                    # Show which agent found this source for transparency
                    agent_label = {
                        'greek_context': '[Ελληνικό Context]',
                        'international_context': '[Διεθνές Context]',
                        'fact_check': '[Επαλήθευση]',
                        'discovery': '[Ανακάλυψη]'
                    }.get(source_agent, '')
                    
                    citation_text += f"{i}. {agent_label} [{title}]({url})\n"
                
                module_logger.info(f"Transparent citation passing: ALL {len(unique_citations)} unique sources")
        
        # Create enhanced prompt with citations
        prompt = enhanced_prompt_loader.render_prompt(
            "greek_synthesis_agent",
            {
                "story_headline": story.headline_greek,
                "discovery_summary": story.summary,
                "greek_context": context_results.get("greek", "Δεν βρέθηκε ελληνικό context"),
                "international_context": context_results.get("international", ""),
                "factcheck_results": str(factcheck_results)
            }
        )
        
        # Add citation instruction if citations exist
        if citation_text:
            prompt += f"""

ΚΡΙΣΙΜΟ - ΠΛΗΡΗΣ ΔΙΑΦΑΝΕΙΑ ΠΗΓΩΝ: Ένα από τα κύρια πλεονεκτήματά μας είναι η παροχή ολοκληρωμένων απόψεων από πολλαπλές πηγές.
Παρακάτω βλέπετε ΟΛΕΣ τις {len(unique_citations)} πηγές που χρησιμοποιήθηκαν στην ανάλυση:

{citation_text}

ΟΔΗΓΙΕΣ ΕΝΣΩΜΑΤΩΣΗΣ:
1. Χρησιμοποιήστε όσο το δυνατόν περισσότερες πηγές για να δείξετε την πολυφωνία
2. Αναφέρετε συγκεκριμένες πηγές με [1], [2], [3] κλπ. όταν παρουσιάζετε διαφορετικές απόψεις
3. Τονίστε όταν πολλαπλές πηγές συμφωνούν (π.χ. "Σύμφωνα με πηγές [1,3,5]...")
4. Επισημάνετε διαφορετικές οπτικές (π.χ. "Ενώ η [2] τονίζει..., η [4] επισημαίνει...")
5. Στο τέλος, συμπεριλάβετε μια σύντομη σημείωση για τον αριθμό και την ποικιλία των πηγών

Θυμηθείτε: Η αξία μας είναι στην ΠΟΛΥΦΩΝΙΑ και στις ΠΟΛΛΑΠΛΕΣ ΟΠΤΙΚΕΣ ΓΩΝΙΕΣ."""
        
        conv_id = await self.synthesis_agent.start_conversation("synthesis")
        response = await self.synthesis_agent.send_message(conv_id, prompt)
        await self.synthesis_agent.end_conversation(conv_id)
        
        # Log synthesis completion with citation info
        if all_citations:
            logger.log_message(
                conversation_id=conv_id,
                agent_name=self.synthesis_agent.config.name,
                provider=self.synthesis_agent.config.provider,
                message_type=MessageType.SYSTEM,
                content=f"Synthesis completed with {len(unique_citations)} unique citations from Gemini agents",
                level=LogLevel.INFO
            )
        
        return response.content
    
    async def run_daily_analysis(self, date: str = "today") -> Dict[str, Any]:
        """Run the complete daily news analysis pipeline with comprehensive error tracking"""
        
        start_time = time.time()
        
        try:
            # Initialize agents
            module_logger.info(f"Starting daily analysis for {date}")
            await self.initialize_agents()
            
            # Phase 1: Discover all categories
            stories = await self.discover_all_categories(date)
            
            if not stories:
                module_logger.error("No stories discovered!")
                return {
                    "session_id": self.session_id,
                    "date": date,
                    "total_stories": 0,
                    "results": {},
                    "errors": self.pipeline_errors,
                    "summary": {
                        "status": "failed",
                        "reason": "No stories discovered"
                    }
                }
            
            # Phase 2-4: Process all stories
            results = await self.process_all_stories()
            
            # Calculate statistics
            end_time = time.time()
            duration_minutes = (end_time - start_time) / 60
            
            successful_stories = sum(1 for r in results.values() if not r.get("errors"))
            failed_stories = len(results) - successful_stories
            
            # Create summary
            summary = {
                "status": "completed",
                "duration_minutes": round(duration_minutes, 2),
                "stories_discovered": len(stories),
                "stories_processed": len(results),
                "stories_successful": successful_stories,
                "stories_failed": failed_stories,
                "categories_processed": len(set(s.category for s in stories)),
                "international_context_calls": sum(1 for s in stories if s.needs_international_context),
                "total_errors": len(self.pipeline_errors)
            }
            
            # Log final summary
            module_logger.info(f"Daily analysis completed: {summary}")
            
            # Print summary
            print("\n📊 Final Analysis Summary:")
            print(f"  • Duration: {summary['duration_minutes']} minutes")
            print(f"  • Stories discovered: {summary['stories_discovered']}")
            print(f"  • Stories processed: {summary['stories_successful']}/{summary['stories_processed']}")
            print(f"  • International context calls: {summary['international_context_calls']}")
            
            if summary['total_errors'] > 0:
                print(f"  • ⚠️ Total errors: {summary['total_errors']}")
            
            # Cleanup
            await self.message_bus.stop()
            
            return {
                "session_id": self.session_id,
                "date": date,
                "total_stories": len(stories),
                "results": results,
                "errors": self.pipeline_errors,
                "summary": summary
            }
            
        except Exception as e:
            module_logger.exception(f"Critical error in daily analysis: {e}")
            print(f"❌ Error in daily analysis: {e}")
            
            # Try to clean up
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
                "summary": {
                    "status": "failed",
                    "reason": str(e)
                }
            }