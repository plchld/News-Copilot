"""
Article extraction module for News Copilot
Handles fetching and extracting text content from news articles
"""
import re
import trafilatura
import urllib.error
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDocument
from api.config import COMMON_USER_AGENT


def fetch_text(url: str) -> str:
    """
    Fetch and extract text content from a URL using trafilatura.
    
    Args:
        url: The URL of the article to fetch
        
    Returns:
        The extracted text content
        
    Raises:
        RuntimeError: If fetching or extraction fails
    """
    print(f"[fetch_text] Attempting to fetch URL: {url}", flush=True)
    
    try:
        downloaded = trafilatura.fetch_url(url)
    except urllib.error.HTTPError as e:
        error_message = f"HTTPError when fetching URL {url}: {e.code} {e.reason}"
        print(f"[fetch_text] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)
    except Exception as e:
        error_message = f"Generic error when fetching URL {url} with trafilatura: {type(e).__name__} - {e}"
        print(f"[fetch_text] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)

    if not downloaded:
        error_message = f"Could not download content from {url} (trafilatura.fetch_url returned None)"
        print(f"[fetch_text] ERROR: {error_message}", flush=True)
        raise RuntimeError(error_message)
    
    print(f"[fetch_text] Successfully downloaded content from {url}", flush=True)
    
    # Extract the main text content
    text = trafilatura.extract(downloaded) or ""
    
    if not text:
        print(f"[fetch_text] Trafilatura failed to extract main text from {url}", flush=True)
        raise RuntimeError(f"Trafilatura failed to extract main text from {url}")
    
    print(f"[fetch_text] Successfully extracted text from {url}", flush=True)
    
    # Clean up whitespace
    cleaned_text = re.sub(r"\s+\n", "\n", text).strip()
    
    return cleaned_text