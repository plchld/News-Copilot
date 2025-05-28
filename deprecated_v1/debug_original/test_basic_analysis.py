#!/usr/bin/env python3
"""Test basic components to identify the issue"""

import os
import sys

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

# Test 1: Can we import the modules?
print("Test 1: Importing modules...")
try:
    from api.agents.viewpoints_agent import ViewpointsAgent
    print("✓ ViewpointsAgent imported")
except Exception as e:
    print(f"✗ Error importing ViewpointsAgent: {e}")

try:
    from api.grok_client import GrokClient
    print("✓ GrokClient imported")
except Exception as e:
    print(f"✗ Error importing GrokClient: {e}")

try:
    from api.article_extractor import fetch_text
    print("✓ fetch_text imported")
except Exception as e:
    print(f"✗ Error importing fetch_text: {e}")

# Test 2: Can we create a GrokClient?
print("\nTest 2: Creating GrokClient...")
try:
    client = GrokClient()
    print("✓ GrokClient created")
except Exception as e:
    print(f"✗ Error creating GrokClient: {e}")
    sys.exit(1)

# Test 3: Can we create a ViewpointsAgent?
print("\nTest 3: Creating ViewpointsAgent...")
try:
    agent = ViewpointsAgent.create(client)
    print("✓ ViewpointsAgent created")
    print(f"  - Name: {agent.config.name}")
    print(f"  - Model: {agent.config.default_model.value}")
except Exception as e:
    print(f"✗ Error creating ViewpointsAgent: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check the prompt builder
print("\nTest 4: Testing prompt builder...")
try:
    context = {
        'article_text': 'Test article text',
        'article_url': 'https://example.com/test'
    }
    prompt = agent._build_custom_prompt(context)
    print(f"✓ Prompt built: {len(prompt)} characters")
    print(f"  First 100 chars: {prompt[:100]}...")
except Exception as e:
    print(f"✗ Error building prompt: {e}")

# Test 5: Check search params builder
print("\nTest 5: Testing search params builder...")
try:
    search_params = agent._build_search_params(context)
    print(f"✓ Search params built")
    if search_params:
        print(f"  - Sources: {len(search_params.get('sources', []))}")
        print(f"  - Excluded websites: {search_params.get('excluded_websites_map', {})}")
except Exception as e:
    print(f"✗ Error building search params: {e}")
    import traceback
    traceback.print_exc()