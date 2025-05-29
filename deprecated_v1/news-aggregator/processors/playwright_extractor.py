"""
Playwright-based article extractor for JavaScript-heavy sites
"""
import asyncio
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import trafilatura


class PlaywrightExtractor:
    """Extract articles using Playwright for better JavaScript handling"""
    
    def extract_with_playwright(self, url: str) -> tuple:
        """
        Extract content using Playwright
        
        Args:
            url: URL to extract
            
        Returns:
            Tuple of (title, content, metadata)
        """
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set user agent
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            try:
                print(f"[PlaywrightExtractor] Loading: {url}")
                
                # Navigate to page
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for content
                if 'amna.gr' in url:
                    print("[PlaywrightExtractor] Waiting for AMNA content...")
                    # Wait for Angular content
                    page.wait_for_timeout(5000)
                    
                    # Try to wait for specific selectors
                    try:
                        page.wait_for_selector('[ng-bind-html], .article-content, .content', timeout=5000)
                    except:
                        pass
                
                # Get page content
                content_html = page.content()
                title = page.title()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content_html, 'html.parser')
                
                # Extract title
                title_found = ""
                title_selectors = ['h1', '.article-title', '.title', '[class*="title"]']
                for selector in title_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        potential_title = elem.get_text(strip=True)
                        if 10 < len(potential_title) < 300:
                            title_found = potential_title
                            print(f"[PlaywrightExtractor] Found title: {title_found[:50]}...")
                            break
                
                # Extract content
                content = ""
                content_selectors = [
                    '[ng-bind-html]',  # Angular binding
                    '.article-text',
                    '.article-content',
                    '.article-body',
                    '.content',
                    '.main-content',
                    '[class*="article"]',
                    '[class*="content"]',
                    'article',
                    '.news-content',
                    '.text-content'
                ]
                
                for selector in content_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        potential_content = elem.get_text(strip=True)
                        if len(potential_content) > 100:
                            content = potential_content
                            print(f"[PlaywrightExtractor] Found content with selector: {selector}")
                            break
                
                # Fallback to paragraph extraction
                if not content or len(content) < 100:
                    print("[PlaywrightExtractor] Extracting from paragraphs...")
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                
                # Clean content
                content = re.sub(r'\s+', ' ', content).strip()
                
                # Use better title if found
                if title_found and (not title or title == "Αθηναϊκό - Μακεδονικό πρακτορείο ειδήσεων"):
                    title = title_found
                
                metadata = {
                    'method': 'playwright',
                    'page_title': title,
                    'url': url
                }
                
                print(f"[PlaywrightExtractor] Extracted {len(content)} characters")
                return title, content, metadata
                
            finally:
                browser.close()
    
    def extract_fallback(self, url: str) -> tuple:
        """
        Try extraction with fallback methods
        
        Args:
            url: URL to extract
            
        Returns:
            Tuple of (title, content, metadata)
        """
        # First try trafilatura
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                metadata_traf = trafilatura.extract_metadata(downloaded)
                
                if text and len(text) > 100:
                    print("[PlaywrightExtractor] Trafilatura extraction successful")
                    return (
                        metadata_traf.get('title', 'Untitled'),
                        text,
                        {'method': 'trafilatura', 'metadata': metadata_traf}
                    )
        except Exception as e:
            print(f"[PlaywrightExtractor] Trafilatura failed: {e}")
        
        # If trafilatura fails, try Playwright
        try:
            return self.extract_with_playwright(url)
        except Exception as e:
            print(f"[PlaywrightExtractor] Playwright extraction failed: {e}")
            raise RuntimeError(f"All extraction methods failed for URL: {url}")