#!/usr/bin/env python3
"""
Grok Live Search Script
Uses xAI's Grok API with live search to analyze news and provide alternative perspectives.
"""

import os
import sys
import argparse
import requests
import json
from pathlib import Path


def read_prompt_from_file(file_path="greece_politics_prompt.md"):
    """Read the prompt template from the markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: Prompt file '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        sys.exit(1)


def call_grok_with_live_search(prompt, country_code=None, news_query=None):
    """
    Call xAI Grok API with live search enabled.
    
    Args:
        prompt (str): The system prompt/instructions
        country_code (str): ISO alpha-2 country code (e.g., 'GR' for Greece)
        news_query (str): Specific news query to search for
    
    Returns:
        dict: API response
    """
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        print("Error: XAI_API_KEY environment variable not set.")
        print("Please set your xAI API key: export XAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Construct the user message
    user_message = prompt
    if news_query:
        user_message += f"\n\nΑναζήτηση για: {news_query}"
    
    # Build search parameters
    search_params = {
        "mode": "on",  # Force live search
        "return_citations": True,
        "max_search_results": 30
    }
    
    # Configure sources based on country code - only web source
    sources = []
    
    if country_code:
        # Add only web source with country specification
        sources.append({"type": "web", "country": country_code.upper()})
    else:
        # Default web source without country restriction
        sources.append({"type": "web"})
    
    search_params["sources"] = sources
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "search_parameters": search_params,
        "model": "grok-3-latest",
        "temperature": 0.7,
        "max_tokens": 8000
    }
    
    try:
        print(f"🔍 Searching for news with Grok (Country: {country_code or 'Global'})...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def format_response(response):
    """Format and display the API response."""
    try:
        # Extract the main content
        content = response['choices'][0]['message']['content']
        
        print("\n" + "="*80)
        print("🤖 GROK ANALYSIS WITH LIVE SEARCH")
        print("="*80)
        print(content)
        
        # Display citations if available
        if 'citations' in response:
            citations = response['citations']
            if citations:
                print("\n" + "-"*60)
                print("📚 ΠΗΓΕΣ (SOURCES):")
                print("-"*60)
                for i, citation in enumerate(citations, 1):
                    print(f"{i}. {citation}")
        
        # Display usage information
        if 'usage' in response:
            usage = response['usage']
            print(f"\n📊 Token Usage: {usage.get('total_tokens', 'N/A')} total")
            print(f"   Input: {usage.get('prompt_tokens', 'N/A')}, Output: {usage.get('completion_tokens', 'N/A')}")
            
    except KeyError as e:
        print(f"Error parsing response: Missing key {e}")
        print("Raw response:", json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error formatting response: {e}")
        print("Raw response:", json.dumps(response, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="Use Grok with live search to analyze Greek political news",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python grok_live_search.py --country GR
  python grok_live_search.py --country GR --query "Μονή Σινά Αίγυπτος"
  python grok_live_search.py --country US --query "Greece monastery Egypt"
  
Country codes (ISO alpha-2):
  GR - Greece
  US - United States  
  DE - Germany
  FR - France
  UK - United Kingdom
  etc.
        """
    )
    
    parser.add_argument(
        '--country', '-c',
        type=str,
        help='ISO alpha-2 country code for localized search (e.g., GR for Greece)'
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Specific news topic to search for (optional)'
    )
    
    parser.add_argument(
        '--prompt-file', '-p',
        type=str,
        default='greece_politics_prompt.md',
        help='Path to the prompt file (default: greece_politics_prompt.md)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output including raw API response'
    )
    
    args = parser.parse_args()
    
    # Validate country code if provided
    if args.country and len(args.country) != 2:
        print("Error: Country code must be exactly 2 characters (ISO alpha-2 format)")
        print("Examples: GR (Greece), US (United States), DE (Germany)")
        sys.exit(1)
    
    # Read the prompt
    print(f"📖 Reading prompt from: {args.prompt_file}")
    prompt = read_prompt_from_file(args.prompt_file)
    
    # Make the API call
    response = call_grok_with_live_search(
        prompt=prompt,
        country_code=args.country,
        news_query=args.query
    )
    
    # Display results
    if args.verbose:
        print("\n🔧 RAW API RESPONSE:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("\n")
    
    format_response(response)


if __name__ == "__main__":
    main() 