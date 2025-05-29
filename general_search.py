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

# Add the backend directory to Python path and set up Django
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from backend.apps.news_aggregator.claude_client import get_claude_client


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
                        "country": location_info["country"],
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
            
            return {
                "content": full_content,
                "citations": citations,
                "search_count": search_count,
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
    
    args = parser.parse_args()
    
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