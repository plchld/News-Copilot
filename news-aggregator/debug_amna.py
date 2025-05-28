#!/usr/bin/env python3
"""
Debug script to understand AMNA website structure
"""
import trafilatura
import requests
from bs4 import BeautifulSoup

url = "https://www.amna.gr/home/article/907028/Sunedriazei-tin-Tetarti-to-upourgiko-sumboulio-upo-ton-Kur-Mitsotaki---Poia-themata-tha-suzitithoun"

print("Testing AMNA website extraction...")
print(f"URL: {url}")
print()

# Test direct requests
print("1. Testing direct requests...")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)}")
    print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for common article selectors
    title_selectors = ['h1', '.title', '.article-title', '[class*="title"]']
    content_selectors = ['.content', '.article-content', '.article-body', '[class*="content"]', 'article', '.main-content']
    
    print("\n2. Searching for title...")
    title = None
    for selector in title_selectors:
        elements = soup.select(selector)
        if elements:
            title = elements[0].get_text().strip()
            print(f"Found title with selector '{selector}': {title[:100]}...")
            break
    
    print("\n3. Searching for content...")
    content = None
    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            content = elements[0].get_text().strip()
            print(f"Found content with selector '{selector}': {len(content)} chars")
            print(f"Preview: {content[:200]}...")
            break
    
    # Try to find all text content
    if not content:
        print("\n4. Extracting all text content...")
        all_text = soup.get_text()
        print(f"Total text length: {len(all_text)}")
        print(f"Preview: {all_text[:300]}...")
        
except Exception as e:
    print(f"Error with requests: {e}")

print("\n" + "="*50)

# Test trafilatura
print("5. Testing trafilatura...")
try:
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        print(f"Trafilatura downloaded {len(downloaded)} bytes")
        text = trafilatura.extract(downloaded)
        if text:
            print(f"Extracted text: {len(text)} chars")
            print(f"Preview: {text[:200]}...")
        else:
            print("Trafilatura extracted no text")
            print("Raw HTML preview:")
            print(downloaded[:500] + "..." if len(downloaded) > 500 else downloaded)
    else:
        print("Trafilatura download failed")
except Exception as e:
    print(f"Error with trafilatura: {e}")