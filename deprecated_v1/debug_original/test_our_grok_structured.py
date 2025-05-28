#!/usr/bin/env python3
"""Test our GrokClient with live search and structured JSON"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.grok_client import GrokClient
from api.search_params_builder import build_search_params
import json

def test_our_grok_with_search():
    """Test our GrokClient with live search and manual JSON schema"""
    
    # Initialize our GrokClient
    client = GrokClient()
    
    # Build search parameters using our builder
    search_params = build_search_params(
        mode="on",
        sources=[
            {"type": "news"},
            {"type": "web"}
        ],
        max_results=10
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
    
    prompt = f"""You are a Greek news analyst. Use live search to find current articles about: {search_query}

Return ONLY a valid JSON object that matches this exact schema:
{json.dumps(json_schema, ensure_ascii=False, indent=2)}

Requirements:
- Search for 3-5 current articles about Turkey-US cooperation, S-400, F-35
- All text values must be in Greek
- Do not include any text before or after the JSON
- Use the live search results to fill the findings array"""
    
    print(f"Testing our GrokClient with live search...")
    print(f"Search query: {search_query}")
    print(f"Search params: {json.dumps(search_params, ensure_ascii=False, indent=2)}")
    
    try:
        # Test 1: Regular completion with search
        print(f"\n🧪 Test 1: Regular completion with live search")
        completion = client.create_completion(
            prompt=prompt,
            search_params=search_params
        )
        
        response_content = completion.choices[0].message.content
        print(f"\n📥 Response received ({len(response_content)} chars)")
        print(f"First 300 chars: {response_content[:300]}...")
        
        # Try to parse JSON
        try:
            analysis = json.loads(response_content)
            print(f"\n✅ SUCCESS! Our GrokClient with live search works")
            print(f"✅ JSON parsing successful")
            
            # Validate schema
            required_keys = ["main_topic", "search_terms_used", "findings", "analysis_summary"]
            missing_keys = [key for key in required_keys if key not in analysis]
            
            if missing_keys:
                print(f"⚠️  Missing required keys: {missing_keys}")
            else:
                print(f"✅ All required keys present")
                print(f"\nMain Topic: {analysis['main_topic']}")
                print(f"Search Terms: {', '.join(analysis['search_terms_used'])}")
                print(f"Findings: {len(analysis['findings'])} articles")
                
                for i, finding in enumerate(analysis['findings'][:2], 1):
                    print(f"\n{i}. {finding['title']}")
                    print(f"   Source: {finding['source']}")
            
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parsing failed: {str(e)}")
            print(f"📄 Raw response (first 1000 chars):")
            print(f"{response_content[:1000]}")
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                print(f"\n🔍 Trying to extract JSON...")
                try:
                    extracted_json = json.loads(json_match.group())
                    print(f"✅ Extracted JSON successfully!")
                    print(f"Keys: {list(extracted_json.keys())}")
                except:
                    print(f"❌ Extracted text is not valid JSON")
        
        # Test 2: Try with response_format if supported
        print(f"\n\n🧪 Test 2: Testing response_format parameter")
        try:
            completion_with_format = client.create_completion(
                prompt=prompt,
                search_params=search_params,
                response_format={"type": "json_object"}
            )
            print(f"✅ response_format parameter works!")
            
            response_content_2 = completion_with_format.choices[0].message.content
            try:
                analysis_2 = json.loads(response_content_2)
                print(f"✅ JSON with response_format works: {len(analysis_2)} keys")
            except:
                print(f"❌ JSON parsing failed even with response_format")
                
        except Exception as e:
            print(f"⚠️  response_format not supported: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_our_grok_with_search()