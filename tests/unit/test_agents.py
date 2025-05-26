#!/usr/bin/env python3
"""
Test script for the agentic architecture
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AsyncOpenAI
from agents.optimized_coordinator import OptimizedAgentCoordinator as AgentCoordinator, AnalysisType, OptimizedCoordinatorConfig as CoordinatorConfig
from agents.base_agent import AgentResult


# Mock Grok client for testing
class MockGrokClient:
    """Mock Grok client for testing without API calls"""
    
    def __init__(self):
        self.chat = self
        self.completions = self
    
    async def create(self, **kwargs):
        """Mock API response"""
        analysis_type = kwargs.get('messages', [{}])[0].get('content', '')
        
        # Return different mock data based on analysis type
        if 'jargon' in str(kwargs).lower():
            content = {
                "terms": [
                    {"term": "ΔΝΤ", "explanation": "Διεθνές Νομισματικό Ταμείο - διεθνής οργανισμός"},
                    {"term": "Brexit", "explanation": "Η έξοδος της Βρετανίας από την ΕΕ"}
                ]
            }
        elif 'fact' in str(kwargs).lower():
            content = {
                "overall_credibility": "μέτρια",
                "claims": [
                    {
                        "statement": "Η ανεργία μειώθηκε στο 10%",
                        "verified": True,
                        "explanation": "Επιβεβαιώνεται από ΕΛΣΤΑΤ",
                        "sources": ["elstat.gr"]
                    }
                ],
                "red_flags": [],
                "missing_context": "Δεν αναφέρεται η εποχικότητα"
            }
        else:
            content = {"mock": "data"}
        
        # Mock response object
        class MockResponse:
            class Choice:
                class Message:
                    def __init__(self, content):
                        self.content = content
                
                def __init__(self, content):
                    self.message = self.Message(content)
            
            class Usage:
                total_tokens = 1000
            
            def __init__(self, content):
                self.choices = [self.Choice(content)]
                self.usage = self.Usage()
        
        return MockResponse(content)


async def test_single_agent():
    """Test a single agent execution"""
    print("\n=== Testing Single Agent ===")
    
    # Initialize mock client
    grok_client = MockGrokClient()
    
    # Create coordinator
    config = CoordinatorConfig(enable_streaming=False)
    coordinator = AgentCoordinator(grok_client, config)
    
    # Test article
    article_text = """
    Το ΔΝΤ προειδοποιεί για επιβράδυνση της παγκόσμιας οικονομίας.
    Η ανεργία στην Ελλάδα μειώθηκε στο 10% σύμφωνα με τα τελευταία στοιχεία.
    Ο πρωθυπουργός δήλωσε ότι η κυβέρνηση θα συνεχίσει τις μεταρρυθμίσεις.
    """
    
    # Test jargon agent
    result = await coordinator.analyze_single(
        article_url="https://example.gr/article",
        article_text=article_text,
        analysis_type=AnalysisType.JARGON,
        user_context={'tier': 'free'}
    )
    
    print(f"Agent: {result.agent_name}")
    print(f"Success: {result.success}")
    print(f"Model used: {result.model_used}")
    print(f"Execution time: {result.execution_time_ms}ms")
    print(f"Data: {result.data}")


async def test_parallel_agents():
    """Test parallel agent execution"""
    print("\n=== Testing Parallel Agents ===")
    
    # Initialize mock client
    grok_client = MockGrokClient()
    
    # Create coordinator
    config = CoordinatorConfig(enable_streaming=False)
    coordinator = AgentCoordinator(grok_client, config)
    
    # Test article
    article_text = """
    Το ΔΝΤ προειδοποιεί για επιβράδυνση της παγκόσμιας οικονομίας.
    Η ανεργία στην Ελλάδα μειώθηκε στο 10% σύμφωνα με τα τελευταία στοιχεία.
    """
    
    # Test multiple agents
    start_time = datetime.now()
    
    results = await coordinator.analyze_article(
        article_url="https://example.gr/article",
        article_text=article_text,
        analysis_types=[
            AnalysisType.JARGON,
            AnalysisType.FACT_CHECK,
            AnalysisType.BIAS
        ],
        user_context={'tier': 'premium'}
    )
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    print(f"\nTotal execution time: {total_time:.2f}s")
    print(f"Number of agents run: {len(results)}")
    
    for analysis_type, result in results.items():
        print(f"\n{analysis_type.value}:")
        print(f"  Success: {result.success}")
        print(f"  Model: {result.model_used.value if result.model_used else 'N/A'}")
        print(f"  Time: {result.execution_time_ms}ms")
        if result.error:
            print(f"  Error: {result.error}")


async def test_with_real_api():
    """Test with real Grok API (requires API key)"""
    print("\n=== Testing with Real API ===")
    
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("Skipping real API test - XAI_API_KEY not set")
        return
    
    # Initialize real client
    grok_client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
    
    # Create coordinator
    config = CoordinatorConfig(
        enable_streaming=False,
        max_parallel_agents=2  # Limit parallel calls
    )
    coordinator = AgentCoordinator(grok_client, config)
    
    # Test with real article
    article_url = "https://www.kathimerini.gr/economy/562789123/mitsotakis-sto-davos-choris-ependyseis-den-yparxei-anaptyxi/"
    
    # For testing, use a sample article text
    article_text = """
    Ο Πρωθυπουργός Κυριάκος Μητσοτάκης μίλησε στο Νταβός για την ανάγκη επενδύσεων.
    Τόνισε ότι χωρίς επενδύσεις δεν υπάρχει ανάπτυξη και ότι η Ελλάδα έχει γίνει
    πιο ελκυστική για τους επενδυτές. Το ΔΝΤ προβλέπει ανάπτυξη 2,3% για το 2024.
    """
    
    print(f"Using sample article text")
    print(f"Article length: {len(article_text)} characters")
    
    # Test jargon analysis only (to save API costs)
    result = await coordinator.analyze_single(
        article_url=article_url,
        article_text=article_text[:2000],  # Limit text for testing
        analysis_type=AnalysisType.JARGON,
        user_context={'tier': 'free'}
    )
    
    print(f"\nJargon Analysis Result:")
    print(f"Success: {result.success}")
    print(f"Model: {result.model_used.value if result.model_used else 'N/A'}")
    print(f"Tokens used: {result.tokens_used}")
    
    if result.success and result.data:
        terms = result.data.get('terms', [])
        print(f"Terms found: {len(terms)}")
        for term in terms[:3]:  # Show first 3
            print(f"  - {term.get('term')}: {term.get('explanation', '')[:50]}...")


async def test_x_pulse_nested():
    """Test X Pulse with nested agents"""
    print("\n=== Testing X Pulse Nested Agents ===")
    
    # This would require more complex mocking or real API
    print("X Pulse testing requires real API integration")
    print("Nested agent architecture is ready for testing with real Grok API")


async def main():
    """Run all tests"""
    print("Testing News Copilot Agentic Architecture")
    print("=========================================")
    
    # Run tests
    await test_single_agent()
    await test_parallel_agents()
    await test_with_real_api()
    await test_x_pulse_nested()
    
    print("\n✓ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())