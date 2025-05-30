#!/usr/bin/env python3
"""
Quick test script to use Google Gemini API to summarize a URL
To run: pip install google-genai
"""

import base64
import os
from google import genai
from google.genai import types
import sys


def generate_summary(url):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-preview-05-20"
    
    # Create the prompt asking for a summary of the URL
    prompt = f"""Please analyze the content at this URL and provide a comprehensive summary in Greek (since this appears to be a Greek news article):

URL: {url}

Please include:
1. The main headline/title
2. Key points and important details
3. Any significant quotes or statements
4. Context and background information
5. Summary should be in Greek language

Provide a well-structured summary that captures the essence of the article."""

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    
    tools = [
        types.Tool(url_context=types.UrlContext()),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain",
    )

    print(f"Analyzing URL: {url}")
    print("=" * 80)
    print()

    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")
        print()  # Add a newline at the end
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Default URL or take from command line
    default_url = "https://www.amna.gr/home/article/907109/Thespisi-ethnikis-archis-epopteias-tis-agoras-aniggeile-o-Kur-Mitsotakis-sto-Ypourgiko-Sumboulio-"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = default_url
        print(f"Using default URL: {url}")
        print()
    
    generate_summary(url) 