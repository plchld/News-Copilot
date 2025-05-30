#!/usr/bin/env python3
"""
Claude Search Script
Uses Claude with websearch for information search
Reads prompts from markdown files
"""

import os
import sys
import django
import asyncio
import argparse
import re
from datetime import datetime

# Add the backend directory to Python path and set up Django
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from backend.apps.news_aggregator.claude_client import get_claude_client


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


class ClaudeSearchClient:
    """Claude search client with websearch capabilities"""
    
    def __init__(self):
        self.anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        
        # Load from .env file if not in environment
        if not self.anthropic_key:
            self._load_env_file()
        
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or .env file")
    
    def _load_env_file(self):
        """Load API keys from .env file"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'ANTHROPIC_API_KEY' and not self.anthropic_key:
                            self.anthropic_key = value.strip('"\'')
        except FileNotFoundError:
            pass
    
    async def search(self, system_prompt: str, user_prompt: str, region: str = None, city: str = None, timezone: str = None, model: str = "claude-sonnet-4-20250514") -> dict:
        """Search using Claude with websearch and return content with citations"""
        
        claude_client = get_claude_client()
        
        # Build user_location for the tool
        user_location = {"type": "approximate"}
        if region:
            user_location["region"] = region
        if city:
            user_location["city"] = city
        if timezone:
            user_location["timezone"] = timezone
        
        print(f"🔍 Searching with Claude ({model})...")
        if region or city or timezone:
            location_parts = [city, region] if city and region else [region or city]
            print(f"📍 Location: {', '.join(filter(None, location_parts))}")
        
        try:
            raw_response = await claude_client.client.messages.create(
                model=model,
                max_tokens=8000,
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.3,
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 10,
                    "user_location": user_location
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
            
            # Process citations - ensure they're in a clean list format
            clean_citations = []
            for citation in citations:
                clean_citation = {
                    "url": citation.get("url", ""),
                    "title": citation.get("title", ""),
                    "cited_text": citation.get("cited_text", ""),
                    "encrypted_index": citation.get("encrypted_index", "")
                }
                if clean_citation["url"]:
                    clean_citations.append(clean_citation)
            
            return {
                "content": full_content,
                "citations": clean_citations,
                "search_count": search_count,
                "model": raw_response.model,
                "usage": getattr(raw_response, 'usage', None),
                "stop_reason": getattr(raw_response, 'stop_reason', None)
            }
            
        except Exception as e:
            print(f"⚠️  Error with structured response, falling back to simple response: {e}")
            # Fallback to simple response
            response = await claude_client.create_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                use_websearch=True,
                temperature=0.3,
                max_tokens=8000
            )
            
            return {
                "content": response,
                "citations": [],
                "search_count": 0,
                "model": model,
                "usage": None,
                "stop_reason": "fallback"
            }


async def perform_claude_search(prompt_file: str = "search_prompt.md", region: str = None, city: str = None, timezone: str = None, model: str = "claude-sonnet-4-20250514", query: str = None):
    """Perform search using Claude with specified parameters"""
    
    today = datetime.now().strftime("%Y-%m-%d")
    current_day = datetime.now().strftime("%A, %B %d, %Y")
    
    print(f"🤖 Claude Search Tool - {current_day}")
    if region:
        print(f"🌍 Region: {region}")
    if city:
        print(f"🏙️  City: {city}")
    if timezone:
        print(f"🕐 Timezone: {timezone}")
    print(f"📄 Prompt file: {prompt_file}")
    print(f"🧠 Model: {model}")
    if query:
        print(f"🔍 Query: {query}")
    print("=" * 60)
    print()
    
    try:
        # Read prompts from file
        system_prompt, user_prompt = read_prompt_file(prompt_file)
        
        # Add specific query if provided
        if query:
            user_prompt = f"{user_prompt}\n\nSpecific query: {query}"
        
        # Add date context to user prompt
        enhanced_user_prompt = f"{user_prompt}\n\nDate: {current_day} ({today})"
        
        # Add explicit web search instruction
        enhanced_user_prompt += "\n\nUSE the web search tool NOW to find the most recent information. Do not respond without searching first."
        
        # Add Greek language instruction if region is Greece
        if region and region.lower() == 'greece':
            enhanced_user_prompt += "\n\nTranslate the response to Greek language."
        
        # Perform search
        search_client = ClaudeSearchClient()
        
        result = await search_client.search(
            system_prompt=system_prompt,
            user_prompt=enhanced_user_prompt,
            region=region,
            city=city,
            timezone=timezone,
            model=model
        )
        
        # Check if content already has inline citations
        content = result["content"]
        has_inline_citations = bool(re.search(r'\[\d+\]', content))
        
        print("📝 **Search Results:**")
        print()
        
        # If no inline citations but we have citation data, append sources section
        if not has_inline_citations and result["citations"]:
            content += "\n\n## Πηγές\n"
            for i, citation in enumerate(result["citations"], 1):
                content += f"\n[{i}] {citation['title']} - {citation['url']}"
                if citation['cited_text']:
                    content += f"\n    \"{citation['cited_text'][:150]}...\""
        
        print(content)
        print()
        
        # Display detailed citations if available
        if result["citations"]:
            print("📚 **Detailed Sources & References:**")
            print()
            for i, citation in enumerate(result["citations"], 1):
                print(f"{i}. **{citation['title']}**")
                print(f"   🔗 {citation['url']}")
                if citation['cited_text']:
                    print(f"   💬 \"{citation['cited_text']}\"")
                if citation['encrypted_index']:
                    print(f"   🔑 Encrypted Index: {citation['encrypted_index']}")
                print()
        
        # Display metadata
        print("ℹ️  **Search Metadata:**")
        if result["search_count"]:
            print(f"   🔍 Performed {result['search_count']} web searches")
        print(f"   🧠 Model: {result['model']}")
        print(f"   🛑 Stop reason: {result['stop_reason']}")
        if result["usage"]:
            usage = result["usage"]
            if hasattr(usage, 'input_tokens') and hasattr(usage, 'output_tokens'):
                print(f"   📊 Tokens: {usage.input_tokens} input, {usage.output_tokens} output")
        
        print()
        print("✅ Search completed successfully!")
        
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return False
    
    return True


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Claude search tool with websearch and custom prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_search.py --region "Greece" --prompt-file greece_politics_prompt.md
  python claude_search.py --region "Greece" --city "Athens" --timezone "Europe/Athens"
  python claude_search.py --query "latest AI developments"
        """
    )
    
    parser.add_argument('--prompt-file', '-f', type=str, default='search_prompt.md', help='Markdown file containing the prompts')
    parser.add_argument('--region', '-r', type=str, help='Region for search location (e.g., "Greece")')
    parser.add_argument('--city', type=str, help='City for search location')
    parser.add_argument('--timezone', '-t', type=str, help='Timezone for search location (e.g., "Europe/Athens")')
    parser.add_argument('--model', '-m', type=str, default='claude-sonnet-4-20250514', 
                       choices=['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'],
                       help='Claude model to use')
    parser.add_argument('--query', '-q', type=str, help='Specific search query to append to the prompt')
    
    args = parser.parse_args()
    
    # Run the search
    asyncio.run(perform_claude_search(args.prompt_file, args.region, args.city, args.timezone, args.model, args.query))


if __name__ == "__main__":
    main() 