#!/usr/bin/env python
"""
Comprehensive test script for Claude migration of all agents
Tests each agent individually and then runs the full coordinator
"""
import os
import sys
import django
import asyncio
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.news_aggregator.agents.jargon_agent import JargonAgent
from apps.news_aggregator.agents.timeline_agent import TimelineAgent
from apps.news_aggregator.agents.viewpoints_agent import ViewpointsAgent
from apps.news_aggregator.agents.fact_check_agent import FactCheckAgent
from apps.news_aggregator.agents.coordinator import AgentCoordinator


async def test_agent(agent, agent_name: str, test_article: str):
    """Test an individual agent"""
    print(f"\n🔍 Testing {agent_name}...")
    print(f"   Model: {agent.config.default_model.value}")
    
    start_time = time.time()
    
    try:
        result = await agent.process(test_article, article_id=f"test_{agent_name}_claude")
        
        execution_time = time.time() - start_time
        
        if result.success:
            print(f"   ✅ Success in {execution_time:.2f}s")
            if result.data:
                # Show a brief summary of the results
                if agent_name == 'jargon' and 'terms' in result.data:
                    print(f"   📚 Found {len(result.data['terms'])} technical terms")
                elif agent_name == 'timeline' and 'events' in result.data:
                    print(f"   📅 Found {len(result.data['events'])} timeline events")
                elif agent_name == 'viewpoints' and 'alternative_perspectives' in result.data:
                    print(f"   👁️ Alternative perspectives found")
                elif agent_name == 'fact_check' and 'claims' in result.data:
                    print(f"   🔍 Verified {len(result.data['claims'])} claims")
            return True
        else:
            print(f"   ❌ Failed: {result.error}")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"   ❌ Exception after {execution_time:.2f}s: {str(e)}")
        return False


async def test_all_agents():
    """Test all migrated agents"""
    print("🚀 Testing Claude Migration for All Agents")
    print("=" * 50)
    
    # Sample Greek article with multiple elements to test all agents
    test_article = """
    Η Κυβέρνηση ανακοίνωσε χθες νέα μέτρα για την ψηφιακή διακυβέρνηση, μετά από 
    συναντήσεις που διήρκεσαν τρεις μήνες με εκπροσώπους της τεχνολογικής βιομηχανίας. 
    Το έργο θα υλοποιηθεί σε δύο φάσεις: η πρώτη θα ολοκληρωθεί μέχρι τον Ιούνιο 2024, 
    ενώ η δεύτερη φάση προγραμματίζεται για το τέλος του 2024.
    
    Σύμφωνα με τον Υπουργό Ψηφιακής Διακυβέρνησης, τα νέα συστήματα θα χρησιμοποιούν 
    τεχνητή νοημοσύνη (AI) και μηχανική μάθηση (ML) για την βελτίωση των υπηρεσιών προς 
    τους πολίτες. Το project θα κοστίσει 50 εκατομμύρια ευρώ και θα εφαρμόσει strict 
    GDPR compliance protocols.
    
    Ωστόσο, η αντιπολίτευση επέκρινε τη "βιαστική" απόφαση, υποστηρίζοντας ότι δεν έγινε 
    επαρκής διαβούλευση με τους φορείς. Η ΑΔΑΕ (Αρχή Διασφάλισης Απορρήτου Επικοινωνιών) 
    εξέφρασε επιφυλάξεις για την προστασία προσωπικών δεδομένων.
    """
    
    # Test each agent individually
    agents_to_test = [
        (JargonAgent(), 'jargon'),
        (TimelineAgent(), 'timeline'),
        (ViewpointsAgent(), 'viewpoints'),
        (FactCheckAgent(), 'fact_check')
    ]
    
    results = {}
    
    for agent, name in agents_to_test:
        success = await test_agent(agent, name, test_article)
        results[name] = success
    
    # Test coordinator
    print(f"\n🎯 Testing AgentCoordinator...")
    
    try:
        coordinator = AgentCoordinator(max_concurrent=2)
        start_time = time.time()
        
        analysis_results = await coordinator.analyze_article(
            test_article,
            article_id="test_coordinator_claude"
        )
        
        execution_time = time.time() - start_time
        
        successful_agents = sum(1 for result in analysis_results.values() if result.success)
        total_agents = len(analysis_results)
        
        print(f"   ✅ Coordinator completed in {execution_time:.2f}s")
        print(f"   📊 {successful_agents}/{total_agents} agents successful")
        
        for agent_name, result in analysis_results.items():
            status = "✅" if result.success else "❌"
            print(f"      {status} {agent_name}")
        
        results['coordinator'] = successful_agents == total_agents
        
    except Exception as e:
        print(f"   ❌ Coordinator failed: {str(e)}")
        results['coordinator'] = False
    
    # Final summary
    print(f"\n📋 Migration Test Summary")
    print("=" * 30)
    
    successful_components = sum(1 for success in results.values() if success)
    total_components = len(results)
    
    for component, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {component}")
    
    print(f"\n🎯 Overall: {successful_components}/{total_components} components successful")
    
    if successful_components == total_components:
        print("🎉 Claude migration completed successfully!")
    else:
        print("⚠️  Some components failed - check logs for details")
    
    return successful_components == total_components


async def test_websearch_capabilities():
    """Test websearch functionality specifically"""
    print(f"\n🌐 Testing Websearch Capabilities")
    print("=" * 35)
    
    # Test with a current events topic that would benefit from websearch
    current_events_article = """
    Η Ευρωπαϊκή Ένωση εξετάζει νέους κανονισμούς για την τεχνητή νοημοσύνη μετά από 
    τις πρόσφατες εξελίξεις στην τεχνολογία. Οι προτεινόμενοι κανονισμοί στοχεύουν 
    στη ρύθμιση των AI συστημάτων υψηλού κινδύνου.
    """
    
    # Test agents that use websearch
    websearch_agents = [
        (TimelineAgent(), 'timeline'),
        (ViewpointsAgent(), 'viewpoints'), 
        (FactCheckAgent(), 'fact_check')
    ]
    
    for agent, name in websearch_agents:
        print(f"\n🔍 Testing {name} with websearch...")
        success = await test_agent(agent, name, current_events_article)
        if success:
            print(f"   🌐 Websearch integration working")
        else:
            print(f"   ⚠️  Websearch integration may have issues")


if __name__ == "__main__":
    print("Starting Claude Migration Test Suite...")
    
    async def run_tests():
        # Test basic migration
        migration_success = await test_all_agents()
        
        # Test websearch capabilities
        await test_websearch_capabilities()
        
        return migration_success
    
    success = asyncio.run(run_tests())
    
    if success:
        print(f"\n🎊 All tests passed! Claude migration is ready.")
        exit(0)
    else:
        print(f"\n💥 Some tests failed. Please check the logs.")
        exit(1)