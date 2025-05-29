#!/usr/bin/env python
"""
Test script for Jargon Agent with Claude migration
"""
import os
import sys
import django
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.news_aggregator.agents.jargon_agent import JargonAgent


async def test_jargon_agent():
    """Test the migrated jargon agent with Claude"""
    print("Testing Jargon Agent with Claude...")
    
    # Sample Greek article with technical terms
    test_article = """
    Η Κυβέρνηση ανακοίνωσε νέα μέτρα για την ψηφιακή διακυβέρνηση με στόχο την υιοθέτηση τεχνολογιών 
    τεχνητής νοημοσύνης (ΤΝ) και μηχανικής μάθησης (ML) στις δημόσιες υπηρεσίες. Το έργο θα 
    χρησιμοποιήσει APIs και microservices αρχιτεκτονική για να διασφαλίσει την interoperability 
    μεταξύ των συστημάτων. Παράλληλα, θα εφαρμοστούν strict protocols για την GDPR συμμόρφωση 
    και την προστασία των προσωπικών δεδομένων των πολιτών.
    """
    
    try:
        # Create agent instance
        agent = JargonAgent()
        print(f"Created agent: {agent.config.name}")
        print(f"Using model: {agent.config.default_model.value}")
        
        # Process the article
        result = await agent.process(test_article, article_id="test_jargon_claude")
        
        if result.success:
            print("✅ Agent completed successfully!")
            print(f"Model used: {result.model_used.value if result.model_used else 'Unknown'}")
            
            # Display the identified terms
            if result.data and 'terms' in result.data:
                print(f"\n📚 Found {len(result.data['terms'])} technical terms:")
                for i, term in enumerate(result.data['terms'], 1):
                    print(f"\n{i}. **{term.get('term', 'N/A')}**")
                    print(f"   Εξήγηση: {term.get('explanation', 'N/A')}")
                    if term.get('context'):
                        print(f"   Πλαίσιο: {term.get('context')}")
            else:
                print("No terms found in response")
                
        else:
            print(f"❌ Agent failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_jargon_agent())