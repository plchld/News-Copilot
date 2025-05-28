#!/usr/bin/env python3
"""Test article extraction for the problematic URL"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.article_extractor import fetch_text

def test_extraction():
    """Test article extraction"""
    url = "https://www.kathimerini.gr/politics/foreign-policy/563630194/synetairoi-me-toyrkia-ypo-oroys/"
    
    print(f"Testing extraction for: {url}")
    
    try:
        text = fetch_text(url)
        print(f"\nExtracted text length: {len(text)} characters")
        print(f"\nFirst 1000 characters:")
        print("-" * 80)
        print(text[:1000])
        print("-" * 80)
        print(f"\nLast 500 characters:")
        print("-" * 80)
        print(text[-500:])
        print("-" * 80)
        
        # Check for specific content
        if "Τουρκία" in text:
            print("\n✓ Found 'Τουρκία' in text")
        if "ΗΠΑ" in text:
            print("✓ Found 'ΗΠΑ' in text")
        if "S-400" in text:
            print("✓ Found 'S-400' in text")
        if "F-35" in text:
            print("✓ Found 'F-35' in text")
            
    except Exception as e:
        print(f"\nError extracting article: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction()