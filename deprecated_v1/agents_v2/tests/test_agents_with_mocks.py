"""Test agents with mock data and tracing"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# Mock the openai module before importing our agents
import sys
sys.modules['openai'] = MagicMock()

# Import after mocking
import agents_v2.providers as providers
from agents_v2.providers import MultiProviderAgent
from agents_v2.agents.discovery import DiscoveryAgent, DISCOVERY_CATEGORIES
from agents_v2.agents.perspectives import (
    GreekPerspectiveAgent,
    InternationalPerspectiveAgent,
    OpposingViewAgent,
    FactVerificationAgent
)
from agents_v2.agents.synthesis import (
    NarrativeSynthesisAgent,
    JargonContextAgent,
    TimelineAgent
)
from agents_v2.agents.social_pulse import SocialPulseAgent
from agents_v2.orchestrator import NewsIntelligenceOrchestrator, OrchestrationConfig
from mock_responses import MockAgentResponses

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockResponse:
    """Mock OpenAI response"""
    def __init__(self, content: str):
        self.choices = [MagicMock(message=MagicMock(content=content))]
        self.usage = MagicMock(model_dump=lambda: {"total_tokens": 100})


async def test_discovery_agent():
    """Test discovery agent with mock data"""
    print("\n=== Testing Discovery Agent ===")
    
    category_config = DISCOVERY_CATEGORIES["greek_politics"]
    agent = DiscoveryAgent(category_config, provider="grok")
    
    # Mock the API call
    mock_response = MockResponse(MockAgentResponses.discovery_response("greek_politics"))
    
    with patch.object(agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await agent.discover(time_range="today")
        
        print(f"Category: {result.category}")
        print(f"Stories found: {len(result.stories)}")
        for story in result.stories:
            print(f"\n- {story.headline}")
            print(f"  Relevance: {story.greek_relevance}")
            print(f"  Sources: {story.initial_sources_found}")
        
        assert len(result.stories) > 0
        assert result.stories[0].greek_relevance == 1.0
        print("\n✓ Discovery agent test passed")


async def test_perspective_agents():
    """Test all perspective agents with mock data"""
    print("\n=== Testing Perspective Agents ===")
    
    topic = "EU AI Regulations"
    
    # Test Greek Perspective
    print("\n-- Greek Perspective --")
    greek_agent = GreekPerspectiveAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.greek_perspective_response())
    
    with patch.object(greek_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await greek_agent.analyze(topic)
        print(f"Summary: {result.summary[:100]}...")
        print(f"Unique angles: {result.analysis.unique_angles}")
        assert result.confidence == 0.85
    
    # Test International Perspective
    print("\n-- International Perspective --")
    intl_agent = InternationalPerspectiveAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.international_perspective_response())
    
    with patch.object(intl_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await intl_agent.analyze(topic)
        print(f"Regions covered: {result.regions_covered}")
        print(f"Regional differences: {len(result.analysis.regional_differences)}")
        assert len(result.analysis.regional_differences) > 0
    
    # Test Opposing View
    print("\n-- Opposing View --")
    opposing_agent = OpposingViewAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.opposing_view_response())
    
    with patch.object(opposing_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await opposing_agent.analyze(topic)
        print(f"Credibility: {result.credibility_assessment}")
        print(f"Mainstream gaps: {result.analysis.mainstream_gaps}")
        assert len(result.analysis.alternative_narratives) > 0
    
    # Test Fact Verification
    print("\n-- Fact Verification --")
    fact_agent = FactVerificationAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.fact_verification_response())
    
    with patch.object(fact_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await fact_agent.verify(topic)
        print(f"Overall reliability: {result.overall_reliability}")
        print(f"Verified facts: {len(result.analysis.verified_facts)}")
        assert result.overall_reliability == 0.82
    
    print("\n✓ All perspective agents tests passed")


async def test_synthesis_agents():
    """Test synthesis agents with mock data"""
    print("\n=== Testing Synthesis Agents ===")
    
    # Test Narrative Synthesis
    print("\n-- Narrative Synthesis --")
    narrative_agent = NarrativeSynthesisAgent(provider="anthropic")
    mock_response = MockResponse(MockAgentResponses.narrative_synthesis_response())
    
    with patch.object(narrative_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        perspectives = {
            "greek": "Greek perspective summary",
            "international": "International perspective",
            "opposing": "Alternative views",
            "facts": "Verified facts"
        }
        
        result = await narrative_agent.synthesize("EU AI Regulations", perspectives)
        print(f"Narrative tone: {result.narrative_tone}")
        print(f"Completeness: {result.completeness_score}")
        print(f"Introduction: {result.narrative.introduction[:50]}...")
        assert result.completeness_score == 0.85
    
    # Test Jargon Analysis
    print("\n-- Jargon Analysis --")
    jargon_agent = JargonContextAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.jargon_response())
    
    with patch.object(jargon_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        narrative = "The AI Act will impose compliance costs leading to brain drain..."
        result = await jargon_agent.process(narrative)
        print(f"Terms found: {len(result.analysis.terms)}")
        print(f"Accessibility score: {result.accessibility_score}")
        for term in result.analysis.terms:
            print(f"  - {term.term}: {term.explanation}")
    
    # Test Timeline Builder
    print("\n-- Timeline Builder --")
    timeline_agent = TimelineAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.timeline_response())
    
    with patch.object(timeline_agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await timeline_agent.build_timeline("EU AI Regulations history")
        print(f"Time span: {result.time_span}")
        print(f"Events: {len(result.timeline.events)}")
        for event in result.timeline.events:
            print(f"  - {event.date}: {event.event}")
    
    print("\n✓ All synthesis agents tests passed")


async def test_social_pulse():
    """Test social pulse agent with mock data"""
    print("\n=== Testing Social Pulse Agent ===")
    
    agent = SocialPulseAgent(provider="grok")
    mock_response = MockResponse(MockAgentResponses.social_pulse_response())
    
    with patch.object(agent, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = mock_response
        
        result = await agent.analyze("EU AI Regulations")
        print(f"Social temperature: {result.temperature}")
        print(f"Engagement level: {result.analysis.engagement_level}")
        print(f"Trending hashtags: {result.analysis.trending_hashtags}")
        print(f"Key insight: {result.key_insight}")
        
        assert result.temperature == "heated"
        print("\n✓ Social pulse agent test passed")


async def test_orchestrator():
    """Test the full orchestrator with mock data"""
    print("\n=== Testing Orchestrator ===")
    
    config = OrchestrationConfig(
        categories_to_scan=["greek_politics", "global_politics"],
        max_stories_per_category=2,
        max_stories_to_analyze=3,
        include_timeline=True,
        include_jargon=True,
        include_social_pulse=True
    )
    
    orchestrator = NewsIntelligenceOrchestrator(config)
    
    # Mock all agent API calls
    async def mock_discovery(agent, *args, **kwargs):
        """Mock discovery based on agent category"""
        category = agent.category_config["name"].lower().replace(" ", "_")
        return MockResponse(MockAgentResponses.discovery_response(category))
    
    async def mock_api_call(self, params):
        """Mock API calls based on agent type"""
        agent_name = self.name
        
        if "discovery" in agent_name:
            category = agent_name.replace("discovery_", "")
            return MockResponse(MockAgentResponses.discovery_response(category))
        elif agent_name == "greek_perspective":
            return MockResponse(MockAgentResponses.greek_perspective_response())
        elif agent_name == "international_perspective":
            return MockResponse(MockAgentResponses.international_perspective_response())
        elif agent_name == "opposing_view":
            return MockResponse(MockAgentResponses.opposing_view_response())
        elif agent_name == "fact_verification":
            return MockResponse(MockAgentResponses.fact_verification_response())
        elif agent_name == "narrative_synthesis":
            return MockResponse(MockAgentResponses.narrative_synthesis_response())
        elif agent_name == "jargon_context":
            return MockResponse(MockAgentResponses.jargon_response())
        elif agent_name == "timeline_builder":
            return MockResponse(MockAgentResponses.timeline_response())
        elif agent_name == "social_pulse":
            return MockResponse(MockAgentResponses.social_pulse_response())
        else:
            return MockResponse(json.dumps({"error": "Unknown agent"}))
    
    # Patch all agents
    with patch.object(MultiProviderAgent, '_call_api', new=mock_api_call):
        print("\nGenerating daily intelligence report...")
        report = await orchestrator.generate_daily_intelligence()
        
        print(f"\n📊 Report Summary:")
        print(f"Processing time: {report['processing_time_seconds']:.1f}s")
        print(f"Stories analyzed: {report['configuration']['stories_analyzed']}")
        
        summary = report['summary']
        print(f"\n📈 Story Distribution:")
        print(f"Total stories: {summary['total_stories']}")
        print(f"By category: {summary['by_category']}")
        print(f"Priority distribution: {summary['priority_distribution']}")
        
        print(f"\n📰 Top Stories:")
        for story in summary['top_stories']:
            print(f"- [{story['priority'].upper()}] {story['headline']}")
        
        # Check first story details
        if report['stories']:
            first_story = report['stories'][0]
            print(f"\n🔍 First Story Details:")
            print(f"ID: {first_story['id']}")
            print(f"Completeness: {first_story['metadata']['completeness_score']}")
            
            if first_story.get('narrative'):
                print(f"Has narrative: ✓")
            if first_story.get('timeline'):
                print(f"Has timeline: ✓")
            if first_story.get('social_pulse'):
                print(f"Has social pulse: ✓")
        
        assert len(report['stories']) > 0
        print("\n✓ Orchestrator test passed")


async def test_with_tracing():
    """Test with tracing enabled to show debug capabilities"""
    print("\n=== Testing with Tracing (Simulated) ===")
    
    # Since we're mocking OpenAI, we'll simulate tracing
    class MockTrace:
        def __init__(self, name):
            self.name = name
            self.spans = []
            
        def __enter__(self):
            print(f"  [TRACE START] {self.name}")
            return self
            
        def __exit__(self, *args):
            print(f"  [TRACE END] {self.name}")
            
        def add_span(self, span_type, data):
            self.spans.append((span_type, data))
            print(f"    [SPAN] {span_type}: {data}")
    
    # Simulate a traced agent run
    print("\nSimulating traced agent execution:")
    
    with MockTrace("Discovery Workflow") as trace:
        trace.add_span("agent", {"name": "discovery_greek_politics", "provider": "grok"})
        trace.add_span("generation", {"model": "grok-3", "tokens": 150})
        trace.add_span("function", {"tool": "search_web", "query": "Greek politics today"})
        
        with MockTrace("Perspective Analysis") as sub_trace:
            sub_trace.add_span("agent", {"name": "greek_perspective", "provider": "grok"})
            sub_trace.add_span("generation", {"model": "grok-3", "tokens": 200})
    
    print("\n✓ Tracing simulation completed")


async def main():
    """Run all tests"""
    print("🧪 Running News Copilot Agents v2 Tests with Mocks\n")
    
    try:
        await test_discovery_agent()
        await test_perspective_agents()
        await test_synthesis_agents()
        await test_social_pulse()
        await test_orchestrator()
        await test_with_tracing()
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())