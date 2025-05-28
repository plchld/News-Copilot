#!/usr/bin/env python3
"""
Test script to identify which agent is causing the COMPLEX error
"""
import sys
import os
import asyncio

# Add Django project to path
sys.path.insert(0, '/mnt/c/Repositories/News-Copilot/backend')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
try:
    django.setup()
except Exception as e:
    print(f"Django setup error: {e}")
    print("Continuing with basic test...")

async def test_individual_agents():
    """Test each agent individually to find the failing one"""
    
    # Sample article content
    test_content = """
    Συνεδριάζει την Τετάρτη το υπουργικό συμβούλιο υπό τον Πρόεδρο της Δημοκρατίας
    με μοναδικά θέματα τα οικονομικά. Η συνεδρίαση θα πραγματοποιηθεί στο Προεδρικό
    Μέγαρο και αναμένεται να διαρκέσει περίπου δύο ώρες.
    """
    
    print("🔍 Testing Individual Agents")
    print("=" * 50)
    
    # Test agent imports first
    try:
        from apps.news_aggregator.agents.base import BaseAgent, AgentResult, ComplexityLevel
        print("✓ Base agent classes imported successfully")
        print(f"  ComplexityLevel values: {[c.value for c in ComplexityLevel]}")
    except Exception as e:
        print(f"✗ Base agent import error: {e}")
        return
    
    # Test coordinator import
    try:
        from apps.news_aggregator.agents.coordinator import AgentCoordinator
        print("✓ AgentCoordinator imported successfully")
    except Exception as e:
        print(f"✗ AgentCoordinator import error: {e}")
        return
    
    # Test individual agent imports
    agent_modules = [
        ('jargon', 'apps.news_aggregator.agents.jargon_agent', 'JargonAgent'),
        ('viewpoints', 'apps.news_aggregator.agents.viewpoints_agent', 'ViewpointsAgent'),
        ('fact_check', 'apps.news_aggregator.agents.fact_check_agent', 'FactCheckAgent'),
        ('bias', 'apps.news_aggregator.agents.bias_agent', 'BiasAgent'),
        ('timeline', 'apps.news_aggregator.agents.timeline_agent', 'TimelineAgent'),
        ('expert', 'apps.news_aggregator.agents.expert_agent', 'ExpertAgent'),
    ]
    
    working_agents = []
    failed_agents = []
    
    for agent_name, module_path, class_name in agent_modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            agent = agent_class()
            working_agents.append(agent_name)
            print(f"✓ {agent_name} agent imported and instantiated")
        except Exception as e:
            failed_agents.append((agent_name, str(e)))
            print(f"✗ {agent_name} agent failed: {e}")
    
    # Test coordinator instantiation
    try:
        coordinator = AgentCoordinator()
        print(f"✓ AgentCoordinator instantiated with {len(coordinator.agents)} agents")
    except Exception as e:
        print(f"✗ AgentCoordinator instantiation failed: {e}")
        return
    
    # Test each working agent individually
    print(f"\n🧪 Testing {len(working_agents)} working agents...")
    
    for agent_name in working_agents:
        try:
            # Create a coordinator with only this agent
            single_coordinator = AgentCoordinator()
            
            # Filter to just this agent
            filtered_agents = {agent_name: single_coordinator.agents[agent_name]}
            single_coordinator.agents = filtered_agents
            
            print(f"\n  Testing {agent_name} agent...")
            result = await single_coordinator.analyze_article(
                article_content=test_content,
                article_id="test-article"
            )
            
            if agent_name in result:
                agent_result = result[agent_name]
                if agent_result.success:
                    print(f"    ✓ {agent_name} completed successfully")
                else:
                    print(f"    ✗ {agent_name} failed: {agent_result.error}")
            else:
                print(f"    ⚠ {agent_name} not in results")
                
        except Exception as e:
            print(f"    ✗ {agent_name} exception: {e}")
            
            # Check if it's the COMPLEX error
            if "COMPLEX" in str(e):
                print(f"    🎯 Found COMPLEX error source: {agent_name}")
                
                # Try to debug further
                try:
                    if hasattr(e, '__cause__') and e.__cause__:
                        print(f"    Cause: {e.__cause__}")
                    if hasattr(e, '__context__') and e.__context__:
                        print(f"    Context: {e.__context__}")
                except:
                    pass
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  Working agents: {working_agents}")
    if failed_agents:
        print(f"  Failed agents: {[name for name, _ in failed_agents]}")
    
    # If all agents worked individually, test full coordinator
    if len(working_agents) == len(agent_modules):
        print(f"\n🔬 Testing full coordinator with all agents...")
        try:
            coordinator = AgentCoordinator()
            results = await coordinator.analyze_article(
                article_content=test_content,
                article_id="test-full"
            )
            print(f"✓ Full coordinator completed with {len(results)} results")
        except Exception as e:
            print(f"✗ Full coordinator failed: {e}")
            if "COMPLEX" in str(e):
                print("🎯 COMPLEX error occurs in full coordinator")

if __name__ == "__main__":
    asyncio.run(test_individual_agents())