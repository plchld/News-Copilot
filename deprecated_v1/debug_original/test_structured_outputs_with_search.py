#!/usr/bin/env python3
"""Test structured outputs with live search"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SearchResult(BaseModel):
    title: str = Field(description="Title of the found article")
    source: str = Field(description="News source name")
    summary: str = Field(description="Brief summary in Greek")

class NewsAnalysis(BaseModel):
    main_topic: str = Field(description="Main topic of the search in Greek")
    search_terms_used: List[str] = Field(description="Search terms that were effective")
    findings: List[SearchResult] = Field(description="Articles found through live search")
    analysis_summary: str = Field(description="Summary analysis in Greek")

def test_structured_outputs_with_search():
    """Test if structured outputs work with live search"""
    
    # Initialize OpenAI client for Grok
    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    
    # Test query about current Greek news
    search_query = "Τουρκία ΗΠΑ συνεργασία S-400 F-35"
    
    print(f"Testing structured outputs with live search...")
    print(f"Search query: {search_query}")
    
    try:
        completion = client.beta.chat.completions.parse(
            model="grok-3-mini",  # Use mini for faster testing
            messages=[
                {
                    "role": "system", 
                    "content": """You are a Greek news analyst. Use live search to find current articles about the given topic. 
                    Analyze the search results and provide structured output in Greek language.
                    Search primarily for Greek news sources and current information."""
                },
                {
                    "role": "user", 
                    "content": f"""Search for recent news about: {search_query}
                    
                    Find 3-5 current articles and provide analysis in Greek."""
                }
            ],
            response_format=NewsAnalysis,
            # Enable live search
            search_parameters={
                "enabled": True,
                "search_mode": "fast",
                "sources": [
                    {"type": "news"},
                    {"type": "web"}
                ],
                "max_results": 10
            }
        )
        
        # Extract structured result
        analysis = completion.choices[0].message.parsed
        
        print(f"\n✅ SUCCESS! Structured outputs work with live search")
        print(f"\nMain Topic: {analysis.main_topic}")
        print(f"\nSearch Terms Used: {', '.join(analysis.search_terms_used)}")
        print(f"\nFindings ({len(analysis.findings)} articles):")
        
        for i, finding in enumerate(analysis.findings, 1):
            print(f"\n{i}. {finding.title}")
            print(f"   Source: {finding.source}")
            print(f"   Summary: {finding.summary}")
        
        print(f"\nAnalysis Summary:")
        print(f"{analysis.analysis_summary}")
        
        # Check if we got meaningful results
        if len(analysis.findings) > 0:
            print(f"\n✅ Live search returned {len(analysis.findings)} results")
        else:
            print(f"\n⚠️  No articles found in search results")
            
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        
        # Check if it's a structured outputs not supported error
        if "structured outputs" in str(e).lower() or "response_format" in str(e).lower():
            print(f"📝 Structured outputs may not be supported with live search")
        elif "parse" in str(e).lower():
            print(f"📝 Beta parse endpoint may not support live search")
        else:
            print(f"📝 Unexpected error occurred")
            
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_structured_outputs_with_search()