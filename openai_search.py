#!/usr/bin/env python3
"""
Simple OpenAI Search Script for Testing
Uses OpenAI's o4-mini model with web search
Reads prompts from markdown files
"""

import os
import re
import argparse
from datetime import datetime
from openai import OpenAI


def read_prompt_file(file_path: str) -> str:
    """Read user prompt from markdown file"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract user prompt section
    if '## User Prompt' in content:
        parts = content.split('## User Prompt')
        if len(parts) > 1:
            return parts[1].strip()
    
    return content.strip()


def perform_search(prompt_file: str = "search_prompt.md", country: str = "US", context_size: str = "medium"):
    """Perform search using OpenAI o4-mini with web search"""
    
    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Try loading from .env file
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == "OPENAI_API_KEY":
                            api_key = value.strip('"\'')
                            break
        except FileNotFoundError:
            pass
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment or .env file")
        return False
    
    client = OpenAI(api_key=api_key)
    
    # Read prompt
    try:
        user_prompt = read_prompt_file(prompt_file)
    except Exception as e:
        print(f"❌ Error reading prompt file: {e}")
        return False
    
    # Add date and instructions
    current_day = datetime.now().strftime("%A, %B %d, %Y")
    
    enhanced_prompt = f"{user_prompt}\n\nDate: {current_day}\n\n"
    enhanced_prompt += f"Country/Region focus: {country}\n\n"
    enhanced_prompt += "IMPORTANT: Use web search to find current information. "
    enhanced_prompt += "Include inline citations [1], [2] etc. and add a '## Πηγές' section at the end with all sources."
    
    # Add Greek language instruction if country is Greece
    if country.lower() in ['greece', 'gr']:
        enhanced_prompt += "\n\nTranslate the response to Greek language."
    
    print(f"🔍 OpenAI Search Tool - {current_day}")
    print(f"📄 Prompt file: {prompt_file}")
    print(f"🤖 Model: gpt-4.1 with web search preview")
    print(f"🌍 Country: {country}")
    print(f"📊 Search context size: {context_size}")
    print("=" * 60)
    print()
    
    try:
        # Simple system message
        messages = [
            {"role": "system", "content": "You are a helpful assistant that searches for information and provides citations."},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        # Combine messages into single input
        input_text = f"{messages[0]['content']}\n\n{messages[1]['content']}"
        
        # Build tools configuration with user location
        tools = [{
            "type": "web_search_preview",
            "user_location": {
                "type": "approximate",
                "country": country.upper() if len(country) == 2 else "US"
            }
        }]
        
        # Convert common country names to ISO codes
        country_codes = {
            "greece": "GR",
            "usa": "US", 
            "uk": "GB",
            "germany": "DE",
            "france": "FR",
            "italy": "IT",
            "spain": "ES"
        }
        
        if country.lower() in country_codes:
            tools[0]["user_location"]["country"] = country_codes[country.lower()]
        
        # Add context size if not default
        if context_size != "medium":
            tools[0]["search_context_size"] = context_size
        
        # Call OpenAI with web search
        print("🔍 Searching...")
        response = client.responses.create(
            model="gpt-4.1",
            input=input_text,
            tools=tools
        )
        
        # Extract content from response
        content = ""
        citations = []
        search_performed = False
        
        # Process the response output items
        if hasattr(response, 'output'):
            for item in response.output:
                # Check for web search call
                if hasattr(item, 'type') and item.type == "web_search_call":
                    search_performed = True
                    
                # Extract message content
                elif hasattr(item, 'type') and item.type == "message":
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content = content_item.text
                            
                            # Extract citations from annotations
                            if hasattr(content_item, 'annotations'):
                                for annotation in content_item.annotations:
                                    if hasattr(annotation, 'type') and annotation.type == "url_citation":
                                        citations.append({
                                            "title": getattr(annotation, 'title', 'No title'),
                                            "url": getattr(annotation, 'url', ''),
                                            "start": getattr(annotation, 'start_index', 0),
                                            "end": getattr(annotation, 'end_index', 0)
                                        })
        
        # Fallback to simpler structure if available
        if not content and hasattr(response, 'output_text'):
            content = response.output_text
        
        print("\n📝 **Results:**")
        print()
        
        # Check if content has inline citations
        has_inline_citations = bool(re.search(r'\[\d+\]', content))
        
        # If no inline citations but we have citation data, append sources
        if not has_inline_citations and citations:
            content += "\n\n## Πηγές\n"
            for i, citation in enumerate(citations, 1):
                content += f"\n[{i}] {citation['title']} - {citation['url']}"
        
        print(content)
        print()
        
        # Display citations
        if citations:
            print("\n📚 **Sources Found:**")
            for i, citation in enumerate(citations, 1):
                print(f"\n{i}. {citation['title']}")
                print(f"   🔗 {citation['url']}")
                if 'start' in citation and 'end' in citation:
                    # Show the cited text from the content
                    cited_text = content[citation['start']:citation['end']] if len(content) > citation['end'] else ""
                    if cited_text:
                        print(f"   📝 \"{cited_text[:150]}...\"")
        
        # Show search status
        if search_performed:
            print(f"\n🔍 Web search performed successfully")
        
        print("\n✅ Search completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Simple main function for testing"""
    parser = argparse.ArgumentParser(
        description="Simple OpenAI search tool for testing with prompt files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python openai_search.py                                    # Use defaults
  python openai_search.py greece_politics_prompt.md          # Use specific prompt
  python openai_search.py -c Greece                          # Search focused on Greece
  python openai_search.py -c Greece -s high                 # Greece with high context
  python openai_search.py science_prompt.md -c US -s low    # Science prompt, US focus, low context
        """
    )
    
    parser.add_argument(
        'prompt_file',
        nargs='?',
        default='search_prompt.md',
        help='Prompt file to use (default: search_prompt.md)'
    )
    
    parser.add_argument(
        '-c', '--country',
        type=str,
        default='US',
        help='Country/region to focus search on (default: US)'
    )
    
    parser.add_argument(
        '-s', '--context-size',
        type=str,
        choices=['low', 'medium', 'high'],
        default='medium',
        help='Search context size: low (fast/cheap), medium (balanced), high (comprehensive) (default: medium)'
    )
    
    args = parser.parse_args()
    
    # Run search
    perform_search(args.prompt_file, args.country, args.context_size)


if __name__ == "__main__":
    main()