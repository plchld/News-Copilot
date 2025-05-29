#!/usr/bin/env python3
"""
Test basic setup and imports
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing basic imports...")

try:
    from config.config import XAI_API_KEY, GROK_DEFAULT_MODEL
    print(f"✓ Config loaded - API Key present: {bool(XAI_API_KEY)}")
    print(f"✓ Default model: {GROK_DEFAULT_MODEL}")
except Exception as e:
    print(f"✗ Config error: {e}")

try:
    from processors.article_processor import ArticleProcessor
    print("✓ ArticleProcessor imported")
except Exception as e:
    print(f"✗ ArticleProcessor error: {e}")

try:
    from processors.ai_enrichment import AIEnrichmentProcessor
    print("✓ AIEnrichmentProcessor imported")
except Exception as e:
    print(f"✗ AIEnrichmentProcessor error: {e}")

try:
    from agents import JargonAgent, BiasAnalysisAgent
    print("✓ Agents imported successfully")
except Exception as e:
    print(f"✗ Agents import error: {e}")
    
try:
    from core.grok_client import GrokClient
    print("✓ GrokClient imported")
except Exception as e:
    print(f"✗ GrokClient error: {e}")

print("\nAll basic imports completed!")