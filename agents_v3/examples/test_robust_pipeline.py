#!/usr/bin/env python3
"""Test the robust pipeline with structured outputs and error handling"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents_v3.utils.discovery_parser import DiscoveryParser, ParsedStory
from agents_v3.utils.logging_config import PipelineLogger, setup_module_logging
from agents_v3.communication.simple_message_bus import simple_message_bus, MessageType


def test_discovery_parser():
    """Test the discovery parser with various inputs"""
    
    print("🧪 Testing Discovery Parser")
    print("=" * 60)
    
    parser = DiscoveryParser()
    
    # Test cases
    test_cases = [
        # Valid JSON
        {
            "name": "Valid JSON",
            "input": '''```json
{
  "category": "Greek Political News",
  "date": "2024-01-30",
  "story_count": 10,
  "stories": [
    {
      "id": 1,
      "headline": "Πρωθυπουργός ανακοινώνει νέα μέτρα",
      "headline_greek": "Πρωθυπουργός ανακοινώνει νέα μέτρα",
      "summary": "The Prime Minister announced new economic measures today.",
      "source_name": "Kathimerini",
      "source_url": "https://kathimerini.gr/story/123",
      "published_date": "2024-01-30 10:00",
      "stakeholders": ["Government", "Citizens"],
      "international_relevance_score": 3,
      "relevance_reasoning": "Domestic policy with limited international impact"
    }
  ]
}
```'''
        },
        # Missing stories
        {
            "name": "Less than 10 stories",
            "input": '''{"stories": [{"id": 1, "headline": "Test", "summary": "Test story"}]}'''
        },
        # Invalid JSON
        {
            "name": "Invalid JSON",
            "input": "This is not JSON at all"
        },
        # Malformed fields
        {
            "name": "Missing required fields",
            "input": '''{"stories": [{"id": 1}]}'''
        }
    ]
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 40)
        
        stories, errors = parser.parse_discovery_output(test["input"], "Test Category")
        
        print(f"Stories parsed: {len(stories)}")
        print(f"Errors: {len(errors)}")
        
        if errors:
            for error in errors[:3]:  # Show first 3 errors
                print(f"  ⚠️ {error}")
        
        if stories:
            story = stories[0]
            print(f"  ✓ First story: {story.headline[:50]}...")
            print(f"    - Needs int'l context: {story.needs_international_context}")


def test_logging_system():
    """Test the enhanced logging system"""
    
    print("\n\n🧪 Testing Logging System")
    print("=" * 60)
    
    # Create logger
    pipeline_logger = PipelineLogger("test_session_123")
    
    # Test different log types
    pipeline_logger.log_discovery_start("greek_political", ["Ελλάδα", "πολιτική"])
    pipeline_logger.log_discovery_result("greek_political", 10, [])
    
    pipeline_logger.log_discovery_start("international_economic", ["global", "economy"])
    pipeline_logger.log_discovery_result("international_economic", 8, ["Parse error on story 9"])
    
    # Log story processing
    pipeline_logger.log_story_processing("story_001", "context", "greek_context_agent", True)
    pipeline_logger.log_story_processing("story_001", "context", "intl_context_agent", False, "API timeout")
    
    # Log communication
    pipeline_logger.log_agent_communication("fact_checker", "greek_context", "fact_check_request", True)
    
    # Log summary
    summary = {
        "total_stories": 18,
        "successful": 16,
        "failed": 2,
        "duration_minutes": 5.3
    }
    pipeline_logger.log_summary(summary)
    
    # Get error summary
    error_summary = pipeline_logger.get_error_summary()
    print(f"\nError Summary:")
    print(f"  Total errors: {error_summary['total_errors']}")
    print(f"  Error types: {error_summary['error_types']}")
    
    print(f"\n✅ Logs saved to: {pipeline_logger.session_dir}")


async def test_message_bus():
    """Test the simplified message bus"""
    
    print("\n\n🧪 Testing Simplified Message Bus")
    print("=" * 60)
    
    # Mock agent handlers
    async def greek_agent_handler(message):
        """Mock Greek context agent handler"""
        if message.message_type == MessageType.ANALYSIS_REQUEST:
            return {
                "analysis": "Greek perspective: This story affects local politics...",
                "sources": ["Kathimerini", "Ta Nea"]
            }
        elif message.message_type == MessageType.FACT_CHECK_REQUEST:
            claim = message.payload["claim"]
            return {
                "verification": "VERIFIED",
                "evidence": f"Found evidence for: {claim[:50]}...",
                "source": "Official statistics"
            }
    
    async def fact_checker_handler(message):
        """Mock fact checker handler"""
        return {"status": "claims identified", "claims_count": 3}
    
    # Register agents
    simple_message_bus.register_agent("greek_context", None, greek_agent_handler)
    simple_message_bus.register_agent("fact_checker", None, fact_checker_handler)
    
    # Test analysis request
    print("\n1. Testing analysis request:")
    result = await simple_message_bus.request_analysis(
        requester="synthesis",
        provider="greek_context",
        story_data={"headline": "Test story", "id": "123"},
        analysis_type="perspective"
    )
    print(f"   Result: {result[:50]}..." if result else "   No result")
    
    # Test fact check request
    print("\n2. Testing fact-check request:")
    result = await simple_message_bus.request_fact_check(
        requester="fact_checker",
        provider="greek_context",
        claim="Unemployment is at 10%",
        context="Government announcement",
        search_query="Greece unemployment rate 2024"
    )
    print(f"   Result: {json.dumps(result, indent=2)}" if result else "   No result")
    
    # Show audit trail
    print("\n3. Message audit trail:")
    simple_message_bus.print_audit_summary()
    
    # Get specific logs
    print("\n4. Recent fact-check messages:")
    fact_checks = simple_message_bus.get_message_log(
        message_type=MessageType.FACT_CHECK_REQUEST,
        last_n=5
    )
    for msg in fact_checks:
        print(f"   [{msg['timestamp']:.0f}] {msg['sender_agent']} -> {msg['target_agent']}")


async def main():
    """Run all tests"""
    
    print("🚀 Testing Robust Pipeline Components")
    print("=" * 80)
    
    # Test discovery parser
    test_discovery_parser()
    
    # Test logging
    test_logging_system()
    
    # Test message bus
    await test_message_bus()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("\n💡 Key improvements demonstrated:")
    print("  • Structured JSON parsing with fault tolerance")
    print("  • Comprehensive error tracking and recovery")
    print("  • Enhanced logging for full auditability")
    print("  • Simplified message bus with clear audit trails")


if __name__ == "__main__":
    asyncio.run(main())