#!/usr/bin/env python3
"""
Test script for enhanced agent logging
This script demonstrates the granular logging capabilities for debugging performance and empty responses
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

# Import agent modules
try:
    from agents.coordinator import AgentCoordinator, AnalysisType, CoordinatorConfig
    from grok_client import GrokClient
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the api/ directory")
    exit(1)


async def test_performance_logging():
    """Test performance logging with a simple jargon analysis"""
    print("\n" + "="*80)
    print("TESTING ENHANCED LOGGING SYSTEM")
    print("="*80)
    
    # Initialize clients
    grok_client = GrokClient()
    config = CoordinatorConfig(
        max_parallel_agents=2,
        enable_streaming=False,
        timeout_seconds=120
    )
    coordinator = AgentCoordinator(grok_client, config)
    
    # Test context
    test_context = {
        'user_id': 'test_user_123',
        'user_tier': 'premium',
        'article_url': 'https://www.kathimerini.gr/test-article',
        'article_text': """
        Η Τράπεζα της Ελλάδος ανακοίνωσε την εφαρμογή νέων μακροπροληπτικών μέτρων για τη στήριξη της χρηματοπιστωτικής σταθερότητας. 
        Τα μέτρα αφορούν στον περιορισμό του συστημικού κινδύνου και την ενίσχυση της κεφαλαιακής επάρκειας των πιστωτικών ιδρυμάτων.
        Ο διοικητής της ΤτΕ τόνισε ότι η εφαρμογή των μέτρων θα συμβάλει στη μείωση της συστημικής ευαλωτότητας του τραπεζικού τομέα.
        """
    }
    
    # Test different analysis types
    analysis_types = [
        AnalysisType.JARGON,
        AnalysisType.VIEWPOINTS
    ]
    
    print(f"\n[TEST] Starting analysis with {len(analysis_types)} agents...")
    print(f"[TEST] Analysis types: {[t.value for t in analysis_types]}")
    print(f"[TEST] Article length: {len(test_context['article_text'])} characters")
    print(f"[TEST] User tier: {test_context['user_tier']}")
    
    try:
        # Execute analysis with enhanced logging
        start_time = datetime.now()
        
        results = await coordinator.analyze_article(
            article_url=test_context['article_url'],
            article_text=test_context['article_text'],
            analysis_types=analysis_types,
            user_context=test_context
        )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n[TEST] Analysis completed in {total_time:.2f}s")
        print(f"[TEST] Results received for: {list(results.keys())}")
        
        # Analyze results for performance insights
        for analysis_type, result in results.items():
            print(f"\n[RESULT_ANALYSIS] {analysis_type.value}:")
            print(f"  Success: {result.success}")
            print(f"  Execution time: {result.execution_time_ms}ms")
            print(f"  Model used: {result.model_used.value if result.model_used else 'unknown'}")
            print(f"  Tokens used: {result.tokens_used or 0}")
            
            if result.success and result.data:
                data_summary = {}
                for key, value in result.data.items():
                    if isinstance(value, list):
                        data_summary[key] = f"{len(value)} items"
                    elif isinstance(value, str):
                        data_summary[key] = f"{len(value)} chars"
                    else:
                        data_summary[key] = type(value).__name__
                print(f"  Data structure: {data_summary}")
            elif result.success and not result.data:
                print(f"  ⚠️  EMPTY RESPONSE DETECTED - This would trigger validation logging")
            else:
                print(f"  Error: {result.error}")
    
    except Exception as e:
        print(f"\n[TEST] Exception during analysis: {e}")
        import traceback
        traceback.print_exc()


async def test_x_pulse_nested_logging():
    """Test nested agent logging with X-Pulse analysis"""
    print("\n" + "="*80)
    print("TESTING X-PULSE NESTED AGENT LOGGING")
    print("="*80)
    
    # Initialize clients
    grok_client = GrokClient()
    config = CoordinatorConfig(
        max_parallel_agents=1,
        enable_streaming=False,
        timeout_seconds=180
    )
    coordinator = AgentCoordinator(grok_client, config)
    
    # Test context for X-Pulse
    test_context = {
        'user_id': 'test_user_456',
        'user_tier': 'free',
        'article_url': 'https://www.protothema.gr/test-article',
        'article_text': """
        Ο πρωθυπουργός ανακοίνωσε νέα μέτρα στήριξης για τις μικρομεσαίες επιχειρήσεις που πλήττονται από την ενεργειακή κρίση.
        Τα μέτρα περιλαμβάνουν επιδοτήσεις ρεύματος, φοροαπαλλαγές και επιχορηγήσεις για την ψηφιακή μετάβαση.
        Η αντιπολίτευση χαρακτήρισε τα μέτρα ανεπαρκή και ζήτησε πιο στοχευμένες παρεμβάσεις.
        """
    }
    
    print(f"\n[X_PULSE_TEST] Starting X-Pulse analysis...")
    print(f"[X_PULSE_TEST] This will demonstrate nested sub-agent orchestration logging")
    
    try:
        start_time = datetime.now()
        
        results = await coordinator.analyze_article(
            article_url=test_context['article_url'],
            article_text=test_context['article_text'],
            analysis_types=[AnalysisType.X_PULSE],
            user_context=test_context
        )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n[X_PULSE_TEST] X-Pulse analysis completed in {total_time:.2f}s")
        
        if AnalysisType.X_PULSE in results:
            result = results[AnalysisType.X_PULSE]
            print(f"[X_PULSE_RESULT] Success: {result.success}")
            if result.success:
                print(f"[X_PULSE_RESULT] Total execution time: {result.execution_time_ms}ms")
                print(f"[X_PULSE_RESULT] API calls: {result.api_calls_count or 'unknown'}")
                print(f"[X_PULSE_RESULT] Refinement calls: {result.refinement_calls_count or 0}")
                print(f"[X_PULSE_RESULT] Total tokens: {result.tokens_used or 0}")
            else:
                print(f"[X_PULSE_RESULT] Error: {result.error}")
    
    except Exception as e:
        print(f"\n[X_PULSE_TEST] Exception during X-Pulse analysis: {e}")
        import traceback
        traceback.print_exc()


def test_empty_response_validation():
    """Test empty response validation logging"""
    print("\n" + "="*80)
    print("TESTING EMPTY RESPONSE VALIDATION")
    print("="*80)
    
    # Import the base agent for testing validation
    from agents.base_agent import AnalysisAgent, AgentConfig, ModelType, ComplexityLevel
    
    # Create a mock agent for testing
    config = AgentConfig(
        name="TestAgent",
        description="Test agent for validation",
        default_model=ModelType.GROK_3_MINI,
        complexity=ComplexityLevel.SIMPLE
    )
    
    class MockAgent(AnalysisAgent):
        def __init__(self):
            super().__init__(config, None, None, None)
    
    mock_agent = MockAgent()
    
    # Test different response scenarios
    test_cases = [
        {"name": "Valid response", "data": {"terms": [{"term": "test", "explanation": "explanation"}]}},
        {"name": "Empty data", "data": None},
        {"name": "Empty dict", "data": {}},
        {"name": "Empty array fields", "data": {"terms": [], "summary": ""}},
        {"name": "Partial empty", "data": {"terms": [{"term": "test"}], "empty_field": []}},
        {"name": "Invalid type", "data": "not_a_dict"}
    ]
    
    for case in test_cases:
        print(f"\n[VALIDATION_TEST] Testing: {case['name']}")
        try:
            status = mock_agent._validate_response_content(case['data'], "test_session_123")
            print(f"[VALIDATION_RESULT] Status: {status}")
        except Exception as e:
            print(f"[VALIDATION_ERROR] Exception: {e}")


async def main():
    """Run all logging tests"""
    print("Enhanced Agent Logging Test Suite")
    print("This script demonstrates the granular logging for debugging performance and empty responses")
    
    # Test 1: Basic performance logging
    await test_performance_logging()
    
    # Test 2: Nested agent communication logging (X-Pulse)
    await test_x_pulse_nested_logging()
    
    # Test 3: Empty response validation
    test_empty_response_validation()
    
    print("\n" + "="*80)
    print("LOGGING TEST SUITE COMPLETED")
    print("="*80)
    print("\nKey logging patterns to look for:")
    print("• [COORDINATOR] - High-level orchestration")
    print("• [AGENT] - Individual agent execution")
    print("• [MODEL_SELECTION] - Dynamic model selection")
    print("• [PERFORMANCE_BREAKDOWN] - Detailed timing analysis")
    print("• [API_CALL] / [API_RESPONSE] - Grok API interaction")
    print("• [EMPTY_RESPONSE] / [CONTENT_VALID] - Response validation")
    print("• [X_PULSE_*] - Nested agent orchestration")
    print("\nThese logs will help identify:")
    print("1. Which phase takes the longest (prep vs API vs validation)")
    print("2. Why responses might be empty (validation logs)")
    print("3. Agent communication patterns (nested orchestration)")
    print("4. Model selection decisions and upgrades")


if __name__ == "__main__":
    asyncio.run(main())