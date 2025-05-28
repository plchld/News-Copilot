#!/usr/bin/env python3
"""Test regular API with live search and manual JSON schema validation"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_regular_api_with_search():
    """Test if regular API works with live search and structured JSON"""
    
    # Initialize OpenAI client for Grok
    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    
    # Define JSON schema for manual validation
    json_schema = {
        "type": "object",
        "properties": {
            "main_topic": {"type": "string", "description": "Main topic in Greek"},
            "search_terms_used": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Effective search terms"
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "source": {"type": "string"},
                        "summary": {"type": "string"}
                    },
                    "required": ["title", "source", "summary"]
                }
            },
            "analysis_summary": {"type": "string", "description": "Summary in Greek"}
        },
        "required": ["main_topic", "search_terms_used", "findings", "analysis_summary"]
    }
    
    search_query = "Τουρκία ΗΠΑ συνεργασία S-400 F-35"
    
    print(f"Testing regular API with live search...")
    print(f"Search query: {search_query}")
    
    try:
        completion = client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {
                    "role": "system", 
                    "content": f"""You are a Greek news analyst. Use live search to find current articles about the given topic.
                    
                    Return ONLY a valid JSON object that matches this exact schema:
                    {json.dumps(json_schema, ensure_ascii=False, indent=2)}
                    
                    All text values must be in Greek. Do not include any text before or after the JSON."""
                },
                {
                    "role": "user", 
                    "content": f"""Search for recent news about: {search_query}
                    
                    Find 3-5 current articles and provide analysis in Greek. Return only valid JSON."""
                }
            ],
            # Enable live search with regular API
            search_parameters={
                "enabled": True,
                "search_mode": "fast",
                "sources": [
                    {"type": "news"},
                    {"type": "web"}
                ],
                "max_results": 10
            },
            temperature=0.3
        )
        
        # Extract response content
        response_content = completion.choices[0].message.content
        print(f"\n📥 Raw response received ({len(response_content)} chars)")
        print(f"First 200 chars: {response_content[:200]}...")
        
        # Try to parse JSON
        try:
            analysis = json.loads(response_content)
            print(f"\n✅ SUCCESS! Regular API with live search works")
            print(f"✅ JSON parsing successful")
            
            # Validate schema manually
            required_keys = ["main_topic", "search_terms_used", "findings", "analysis_summary"]
            missing_keys = [key for key in required_keys if key not in analysis]
            
            if missing_keys:
                print(f"⚠️  Missing required keys: {missing_keys}")
            else:
                print(f"✅ All required keys present")
                
                print(f"\nMain Topic: {analysis['main_topic']}")
                print(f"Search Terms: {', '.join(analysis['search_terms_used'])}")
                print(f"Findings: {len(analysis['findings'])} articles")
                
                for i, finding in enumerate(analysis['findings'][:3], 1):  # Show first 3
                    print(f"\n{i}. {finding['title']}")
                    print(f"   Source: {finding['source']}")
                    print(f"   Summary: {finding['summary'][:100]}...")
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parsing failed: {str(e)}")
            print(f"📄 Raw response:")
            print(f"{response_content}")
            return False
        
    except Exception as e:
        print(f"\n❌ API ERROR: {str(e)}")
        
        if "search_parameters" in str(e).lower():
            print(f"📝 Live search may not be supported")
        else:
            print(f"📝 Unexpected error occurred")
            
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_regular_api_with_search()