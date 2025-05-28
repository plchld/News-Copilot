#!/usr/bin/env python3
"""
Simple test to extract content from AMNA using manual parsing
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def extract_amna_manual(url: str):
    """Manually extract content from AMNA website"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Fetching: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "Untitled"
        
        # Look for meta description
        description_elem = soup.find('meta', {'name': 'description'})
        description = description_elem.get('content', '') if description_elem else ''
        
        # Extract all text content and filter
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        
        # Filter out navigation and other non-content
        content_lines = []
        for line in lines:
            # Skip very short lines, navigation elements, etc.
            if (len(line) > 30 and 
                'cookie' not in line.lower() and 
                'navigation' not in line.lower() and
                'menu' not in line.lower() and
                'facebook' not in line.lower() and
                'twitter' not in line.lower() and
                line not in ['Αθηναϊκό - Μακεδονικό πρακτορείο ειδήσεων']):
                content_lines.append(line)
        
        content = ' '.join(content_lines)
        
        result = {
            'url': url,
            'title': title,
            'description': description,
            'content': content,
            'content_length': len(content),
            'word_count': len(content.split()),
            'extracted_at': datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    amna_url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"
    
    print("=" * 80)
    print("MANUAL AMNA EXTRACTION TEST")
    print("=" * 80)
    
    result = extract_amna_manual(amna_url)
    
    if result:
        print(f"✓ Title: {result['title']}")
        print(f"✓ Description: {result['description'][:100]}...")
        print(f"✓ Content length: {result['content_length']} chars")
        print(f"✓ Word count: {result['word_count']} words")
        print()
        print("Content preview:")
        print("-" * 50)
        print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
        print("-" * 50)
        
        # Save to file
        with open('data/exports/amna_manual_test.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n✓ Saved to: data/exports/amna_manual_test.json")
        
    else:
        print("❌ Extraction failed")

if __name__ == "__main__":
    main()