#!/usr/bin/env python3
"""
General Search Script
Uses Claude or Grok with websearch for general information search
Reads prompts from markdown files
"""

import os
import sys
import django
import asyncio
import argparse
import requests
from datetime import datetime
import json
import re
from pathlib import Path

# Add the backend directory to Python path and set up Django
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from backend.apps.news_aggregator.claude_client import get_claude_client
from backend.apps.core.claude_pricing import calculate_conversation_cost, ClaudeTokenCounter, ClaudeModel


# Country code mapping for better user experience
COUNTRY_MAPPING = {
    'greece': 'GR',
    'usa': 'US',
    'uk': 'GB',
    'germany': 'DE',
    'france': 'FR',
    'italy': 'IT',
    'spain': 'ES',
    'canada': 'CA',
    'australia': 'AU',
    'japan': 'JP',
    'china': 'CN',
    'india': 'IN',
    'brazil': 'BR',
    'russia': 'RU'
}

# City mapping for Claude location settings
CITY_MAPPING = {
    'GR': {'city': 'Athens', 'region': 'Greece', 'timezone': 'Europe/Athens'},
    'US': {'city': 'New York', 'region': 'United States', 'timezone': 'America/New_York'},
    'GB': {'city': 'London', 'region': 'United Kingdom', 'timezone': 'Europe/London'},
    'DE': {'city': 'Berlin', 'region': 'Germany', 'timezone': 'Europe/Berlin'},
    'FR': {'city': 'Paris', 'region': 'France', 'timezone': 'Europe/Paris'},
    'IT': {'city': 'Rome', 'region': 'Italy', 'timezone': 'Europe/Rome'},
    'ES': {'city': 'Madrid', 'region': 'Spain', 'timezone': 'Europe/Madrid'},
    'CA': {'city': 'Toronto', 'region': 'Canada', 'timezone': 'America/Toronto'},
    'AU': {'city': 'Sydney', 'region': 'Australia', 'timezone': 'Australia/Sydney'},
    'JP': {'city': 'Tokyo', 'region': 'Japan', 'timezone': 'Asia/Tokyo'},
    'CN': {'city': 'Beijing', 'region': 'China', 'timezone': 'Asia/Shanghai'},
    'IN': {'city': 'Mumbai', 'region': 'India', 'timezone': 'Asia/Kolkata'},
    'BR': {'city': 'São Paulo', 'region': 'Brazil', 'timezone': 'America/Sao_Paulo'},
    'RU': {'city': 'Moscow', 'region': 'Russia', 'timezone': 'Europe/Moscow'}
}


def read_prompt_file(file_path: str) -> tuple:
    """
    Read system and user prompts from markdown file
    Returns: (system_prompt, user_prompt)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by ---
    if '---' in content:
        parts = content.split('---', 1)
        system_part = parts[0].strip()
        user_part = parts[1].strip()
        
        # Remove markdown headers from system prompt
        system_lines = [line for line in system_part.split('\n') 
                       if not line.strip().startswith('#')]
        system_prompt = '\n'.join(system_lines).strip()
        
        # Extract user prompt (after ## User Prompt header)
        user_lines = user_part.split('\n')
        user_start = 0
        for i, line in enumerate(user_lines):
            if line.strip().startswith('## User Prompt'):
                user_start = i + 1
                break
        
        user_prompt = '\n'.join(user_lines[user_start:]).strip()
        
        return system_prompt, user_prompt
    else:
        # If no separator, treat first paragraph as system, rest as user
        paragraphs = content.split('\n\n')
        system_prompt = paragraphs[0].strip()
        user_prompt = '\n\n'.join(paragraphs[1:]).strip() if len(paragraphs) > 1 else ""
        
        return system_prompt, user_prompt


def log_api_cost(cost_info: dict, prompt_file: str):
    """Log API costs to a JSON file for tracking"""
    if not cost_info:
        return
    
    log_file = Path("api_costs_log.json")
    
    # Load existing log or create new
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_data = json.load(f)
    else:
        log_data = {
            "total_cost_usd": 0,
            "total_tokens": 0,
            "total_calls": 0,
            "calls": []
        }
    
    # Add new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt_file": prompt_file,
        "model": cost_info["model"],
        "input_tokens": cost_info["input_tokens"],
        "output_tokens": cost_info["output_tokens"],
        "total_tokens": cost_info["total_tokens"],
        "web_searches": cost_info.get("web_searches", 0),
        "web_search_cost_usd": cost_info.get("web_search_cost_usd", 0),
        "cost_usd": cost_info["total_cost_usd"]
    }
    
    log_data["calls"].append(entry)
    log_data["total_cost_usd"] += cost_info["total_cost_usd"]
    log_data["total_tokens"] += cost_info["total_tokens"]
    log_data["total_calls"] += 1
    
    # Save updated log
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return log_data["total_cost_usd"]


class SearchClient:
    """Unified client for both Claude and Grok search"""
    
    def __init__(self):
        # Load API keys from environment
        self.anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        self.xai_key = os.environ.get('XAI_API_KEY')
        
        # Load from .env file if not in environment
        if not self.anthropic_key or not self.xai_key:
            self._load_env_file()
    
    def _load_env_file(self):
        """Load API keys from .env file"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'ANTHROPIC_API_KEY' and not self.anthropic_key:
                            self.anthropic_key = value
                        elif key == 'XAI_API_KEY' and not self.xai_key:
                            self.xai_key = value
        except FileNotFoundError:
            pass
    
    def _normalize_country_code(self, country: str) -> str:
        """Normalize country input to ISO alpha-2 code"""
        if not country:
            return 'GR'  # Default to Greece
        
        country = country.lower().strip()
        
        # If it's already a 2-letter code, return uppercase
        if len(country) == 2 and country.isalpha():
            return country.upper()
        
        # Check if it's in our mapping
        if country in COUNTRY_MAPPING:
            return COUNTRY_MAPPING[country]
        
        # If not found, default to Greece
        print(f"⚠️  Unknown country '{country}', defaulting to Greece (GR)")
        return 'GR'
    
    async def search_with_claude(self, system_prompt: str, user_prompt: str, country: str = 'GR') -> dict:
        """Search using Claude with websearch and return content with citations"""
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        
        country_code = self._normalize_country_code(country)
        location_info = CITY_MAPPING.get(country_code, CITY_MAPPING['GR'])
        
        claude_client = get_claude_client()
        
        # Use the client directly to get the structured response with citations
        try:
            raw_response = await claude_client.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4000,
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.3,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5,
                    "user_location": {
                        "type": "approximate",
                        "city": location_info["city"],
                        "region": location_info["region"],
                        "country": country_code,
                        "timezone": location_info["timezone"]
                    }
                }]
            )
            
            # Extract content and citations from response
            full_content = ""
            citations = []
            search_count = 0
            
            # Process content blocks
            for content_block in raw_response.content:
                if hasattr(content_block, 'text') and content_block.text:
                    full_content += content_block.text
                
                # Count web search tool uses
                if hasattr(content_block, 'name') and content_block.name == 'web_search':
                    search_count += 1
            
            # Extract citations from usage metadata if available
            if hasattr(raw_response, 'usage') and hasattr(raw_response.usage, 'web_search_result_locations'):
                for location in raw_response.usage.web_search_result_locations:
                    citation_info = {
                        "url": getattr(location, 'url', ''),
                        "title": getattr(location, 'title', ''),
                        "cited_text": getattr(location, 'cited_text', ''),
                        "encrypted_index": getattr(location, 'encrypted_index', '')
                    }
                    if citation_info["url"] and citation_info not in citations:
                        citations.append(citation_info)
            
            # If no usage metadata, try extracting from content
            if not citations and hasattr(raw_response, 'content'):
                # Look for citation patterns in the response content
                citation_pattern = r'\[(\d+)\]'
                citation_matches = re.findall(citation_pattern, full_content)
                if citation_matches:
                    # Basic citation extraction - would need more sophisticated parsing
                    # for now, we'll use a simple approach
                    pass
            
            # Calculate cost if usage data is available
            cost_info = None
            if hasattr(raw_response, 'usage'):
                try:
                    # Prepare messages for cost calculation
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    
                    # Get actual model name
                    model_name = getattr(raw_response, 'model', 'claude-3-7-sonnet-20250219')
                    
                    # Calculate cost
                    cost_info = calculate_conversation_cost(
                        messages=messages,
                        response=full_content,
                        model_name=model_name,
                        web_searches=search_count
                    )
                except Exception as e:
                    print(f"⚠️  Could not calculate cost: {e}")
            
            return {
                "content": full_content,
                "citations": citations,
                "search_count": search_count,
                "cost_info": cost_info,
                "response_metadata": {
                    "model": raw_response.model,
                    "stop_reason": getattr(raw_response, 'stop_reason', None),
                    "usage": getattr(raw_response, 'usage', None)
                }
            }
            
        except Exception as e:
            print(f"⚠️  Error accessing structured response, falling back: {e}")
            # Fallback to simple response
            response = await claude_client.create_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model="claude-3-7-sonnet-20250219",
                use_websearch=True,
                temperature=0.3,
                max_tokens=4000
            )
            
            return {
                "content": response,
                "citations": [],
                "search_count": 0,
                "cost_info": None,
                "response_metadata": {}
            }
    
    def search_with_grok(self, system_prompt: str, user_prompt: str, sources: list = None, country: str = 'GR') -> str:
        """Search using Grok with live search"""
        if not self.xai_key:
            raise ValueError("XAI_API_KEY not found")
        
        country_code = self._normalize_country_code(country)
        
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.xai_key}"
        }
        
        # Default sources with country parameter
        if not sources:
            sources = [
                {"type": "web", "safe_search": True, "country": country_code},
                {"type": "news", "safe_search": True, "country": country_code}
            ]
        else:
            # Add country to existing sources if not already present
            for source in sources:
                if source.get("type") in ["web", "news"] and "country" not in source:
                    source["country"] = country_code
        
        # Build messages with system prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "messages": messages,
            "search_parameters": {
                "mode": "on",
                "sources": sources,
                "return_citations": True,
                "max_search_results": 25,
                "from_date": datetime.now().strftime("%Y-%m-%d"),  # Today only
                "to_date": datetime.now().strftime("%Y-%m-%d")
            },
            "model": "grok-3-latest",
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Add citations if available
            if 'citations' in result and result['citations']:
                content += "\n\n📚 **Πηγές:**\n"
                for i, citation in enumerate(result['citations'], 1):
                    content += f"{i}. {citation}\n"
            
            return content
        else:
            raise Exception(f"Grok API error: {response.status_code} - {response.text}")


async def perform_search(client_type: str = "claude", prompt_file: str = "search_prompt.md", 
                        country: str = 'GR'):
    """Perform search using specified client and prompt file"""
    
    today = datetime.now().strftime("%Y-%m-%d")
    current_day = datetime.now().strftime("%A, %B %d, %Y")
    
    print(f"🔍 General Search Tool - {current_day}")
    print(f"🤖 Using: {client_type.upper()}")
    print(f"🌍 Country: {country.upper()}")
    print(f"📄 Prompt file: {prompt_file}")
    print("=" * 60)
    print()
    
    try:
        # Read prompts from file
        system_prompt, user_prompt = read_prompt_file(prompt_file)
        
        # Add date and country context to user prompt
        enhanced_user_prompt = f"{user_prompt}\n\nΗμερομηνία: {current_day} ({today})\nΧώρα εστίασης: {country.upper()}"
        
        # For Claude, add explicit web search instruction
        if client_type == "claude":
            enhanced_user_prompt += "\n\nΧΡΗΣΙΜΟΠΟΙΗΣΕ το εργαλείο αναζήτησης στο διαδίκτυο ΤΩΡΑ για να βρεις τις πιο πρόσφατες πληροφορίες. Μην απαντήσεις χωρίς να κάνεις πρώτα αναζήτηση."
        
        enhanced_user_prompt += "\n\nΠαρέχεις την απάντηση στα ελληνικά με πηγές."
        
        # Perform search
        search_client = SearchClient()
        
        if client_type == "claude":
            result = await search_client.search_with_claude(
                system_prompt=system_prompt,
                user_prompt=enhanced_user_prompt,
                country=country
            )
            
            print("📝 **Αποτελέσματα Αναζήτησης:**")
            print()
            print(result["content"])
            print()
            
            # Display citations if available
            if result["citations"]:
                print("📚 **Πηγές & Αναφορές:**")
                print()
                for i, citation in enumerate(result["citations"], 1):
                    print(f"{i}. **{citation['title']}**")
                    print(f"   🔗 {citation['url']}")
                    if citation['cited_text']:
                        print(f"   💬 \"{citation['cited_text']}\"")
                    print()
            
            if result["search_count"]:
                print(f"🔍 Πραγματοποιήθηκαν {result['search_count']} αναζητήσεις στο διαδίκτυο")
            
            # Display cost information if available
            if result.get("cost_info"):
                cost = result["cost_info"]
                print()
                print("💰 **Κόστος API Κλήσης:**")
                print(f"   📥 Input tokens: {cost['input_tokens']:,}")
                print(f"   📤 Output tokens: {cost['output_tokens']:,}")
                print(f"   🔢 Total tokens: {cost['total_tokens']:,}")
                print(f"   💵 Input cost: ${cost['input_cost_usd']:.6f}")
                print(f"   💵 Output cost: ${cost['output_cost_usd']:.6f}")
                
                # Add web search costs if applicable
                if cost.get('web_searches', 0) > 0:
                    print(f"   🔍 Web searches: {cost['web_searches']}")
                    print(f"   💵 Web search cost: ${cost['web_search_cost_usd']:.6f}")
                
                print(f"   💰 Total cost: ${cost['total_cost_usd']:.6f}")
                print(f"   🤖 Model: {cost['model']}")
                
                # Log the cost
                total_cost = log_api_cost(cost, prompt_file)
                print(f"   📊 Συνολικό κόστος όλων των κλήσεων: ${total_cost:.4f}")
                
        else:  # grok
            result = search_client.search_with_grok(
                system_prompt=system_prompt,
                user_prompt=enhanced_user_prompt,
                country=country
            )
            
            print("📝 **Αποτελέσματα Αναζήτησης:**")
            print()
            print(result)
        
        print()
        print("✅ Αναζήτηση ολοκληρώθηκε επιτυχώς!")
        
    except Exception as e:
        print(f"❌ Σφάλμα κατά την αναζήτηση: {str(e)}")
        return False
    
    return True


def show_cost_history():
    """Display cost history from the log file"""
    log_file = Path("api_costs_log.json")
    
    if not log_file.exists():
        print("❌ No cost history found. Run some searches first!")
        return
    
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    print("💰 **API Cost History**")
    print("=" * 60)
    print(f"📊 Total API calls: {log_data['total_calls']}")
    print(f"🔢 Total tokens used: {log_data['total_tokens']:,}")
    print(f"💵 Total cost: ${log_data['total_cost_usd']:.4f}")
    
    # Calculate total web searches
    total_web_searches = sum(call.get('web_searches', 0) for call in log_data['calls'])
    total_web_search_cost = sum(call.get('web_search_cost_usd', 0) for call in log_data['calls'])
    
    if total_web_searches > 0:
        print(f"🔍 Total web searches: {total_web_searches}")
        print(f"💵 Total web search cost: ${total_web_search_cost:.4f}")
    
    print()
    
    if log_data['total_calls'] > 0:
        print(f"📈 Average cost per call: ${log_data['total_cost_usd']/log_data['total_calls']:.6f}")
        print(f"📈 Average tokens per call: {log_data['total_tokens']/log_data['total_calls']:.0f}")
        if total_web_searches > 0:
            print(f"📈 Average web searches per call: {total_web_searches/log_data['total_calls']:.1f}")
    
    print()
    print("📋 Recent calls (last 10):")
    print("-" * 60)
    
    # Show last 10 calls
    for call in log_data['calls'][-10:]:
        timestamp = datetime.fromisoformat(call['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        web_info = f" | 🔍 {call.get('web_searches', 0)}" if call.get('web_searches', 0) > 0 else ""
        print(f"{timestamp} | {call['prompt_file']:20} | {call['total_tokens']:6,} tokens | ${call['cost_usd']:.6f}{web_info} | {call['model']}")


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="General search tool using Claude or Grok with custom prompts")
    
    parser.add_argument(
        '--client', '-c',
        choices=['claude', 'grok'],
        default='grok',
        help='AI client to use (default: grok)'
    )
    
    parser.add_argument(
        '--prompt-file', '-f',
        type=str,
        default='search_prompt.md',
        help='Markdown file containing the prompts (default: search_prompt.md)'
    )
    
    parser.add_argument(
        '--country',
        type=str,
        default='GR',
        help='Country to focus search on (ISO alpha-2 code or name, default: GR)'
    )
    
    parser.add_argument(
        '--sources',
        type=str,
        nargs='+',
        choices=['web', 'news', 'x'],
        default=['web', 'news'],
        help='Data sources for Grok (only applies to --client grok)'
    )
    
    parser.add_argument(
        '--cost-history',
        action='store_true',
        help='Show API cost history and exit'
    )
    
    args = parser.parse_args()
    
    # If cost history requested, show it and exit
    if args.cost_history:
        show_cost_history()
        return
    
    # Print usage info
    print("🔍 General Search Tool")
    print("=" * 25)
    print(f"📅 Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"🤖 Client: {args.client}")
    print(f"🌍 Country: {args.country.upper()}")
    print(f"📄 Prompt file: {args.prompt_file}")
    print()
    
    # Run the search
    asyncio.run(perform_search(args.client, args.prompt_file, args.country))


if __name__ == "__main__":
    main() 