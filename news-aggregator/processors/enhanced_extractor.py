"""
Enhanced article extractor with JavaScript rendering support
Handles dynamic content loading for modern news websites
"""
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import trafilatura
from processors.chrome_setup import setup_chrome_driver
from processors.undetected_chrome_setup import setup_undetected_chrome


class EnhancedExtractor:
    """Enhanced extractor with JavaScript rendering capability"""
    
    def __init__(self):
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            # Try undetected-chromedriver first (better for macOS security)
            try:
                self.driver = setup_undetected_chrome()
                print("[EnhancedExtractor] Undetected WebDriver initialized successfully")
            except:
                # Fallback to regular setup
                self.driver = setup_chrome_driver()
                print("[EnhancedExtractor] Regular WebDriver initialized successfully")
        except Exception as e:
            print(f"[EnhancedExtractor] Warning: Could not initialize WebDriver: {e}")
            self.driver = None
    
    def extract_with_js(self, url: str, wait_time: int = 5) -> tuple:
        """
        Extract content using Selenium for JavaScript rendering
        
        Args:
            url: URL to extract
            wait_time: Time to wait for content to load
            
        Returns:
            Tuple of (title, content, metadata)
        """
        if not self.driver:
            raise RuntimeError("WebDriver not available")
        
        try:
            print(f"[EnhancedExtractor] Loading URL with JavaScript: {url}")
            self.driver.get(url)
            
            # Wait for Angular content to load
            if 'amna.gr' in url:
                print("[EnhancedExtractor] Detected AMNA site, waiting for Angular...")
                time.sleep(wait_time + 3)  # Extra time for Angular
                
                # Try to wait for specific Angular elements
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.by import By
                    
                    # Wait for any ng-binding or article element
                    wait = WebDriverWait(self.driver, 10)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[ng-bind-html], .article-body, .content")))
                except:
                    pass
            else:
                time.sleep(wait_time)
            
            # Get page title
            title = self.driver.title
            
            # Get page source after JS execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try common content selectors for Greek news sites
            content_selectors = [
                '[ng-bind-html]',  # Angular binding (AMNA specific)
                '.article-text',
                '.article-content',
                '.content',
                '.article-body',
                '.main-content',
                '[class*="content"]',
                '[class*="article"]',
                '.entry-content',
                '.post-content',
                'article',
                '[data-article]',
                '.news-content',
                '.text-content'
            ]
            
            content = ""
            title_found = ""
            
            # Try to find title first
            title_selectors = ['h1', '.article-title', '.title', '[class*="title"]']
            for selector in title_selectors:
                elements = soup.select(selector)
                if elements:
                    potential_title = elements[0].get_text(strip=True)
                    if len(potential_title) > 10 and len(potential_title) < 300:
                        title_found = potential_title
                        print(f"[EnhancedExtractor] Found title: {title_found[:50]}...")
                        break
            
            # Extract content
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    potential_content = elements[0].get_text(strip=True)
                    if len(potential_content) > 100:  # Ensure meaningful content
                        content = potential_content
                        print(f"[EnhancedExtractor] Found content with selector: {selector}")
                        break
            
            # If no specific content found, try to extract from body
            if not content or len(content) < 100:
                print("[EnhancedExtractor] Trying to extract from body")
                body = soup.find('body')
                if body:
                    # Remove script and style elements
                    for script in body(["script", "style", "nav", "header", "footer", "aside"]):
                        script.decompose()
                    
                    # Get all paragraphs
                    paragraphs = body.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                    
                    if not content:
                        content = body.get_text(strip=True)
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Use found title if better than page title
            if title_found and (not title or title == "Αθηναϊκό - Μακεδονικό πρακτορείο ειδήσεων"):
                title = title_found
            
            metadata = {
                'method': 'selenium',
                'page_title': title,
                'url': url
            }
            
            print(f"[EnhancedExtractor] Extracted {len(content)} characters")
            return title, content, metadata
            
        except Exception as e:
            print(f"[EnhancedExtractor] Error extracting with JS: {e}")
            raise
    
    def extract_fallback(self, url: str) -> tuple:
        """
        Fallback extraction using trafilatura + enhanced selenium
        
        Args:
            url: URL to extract
            
        Returns:
            Tuple of (title, content, metadata)
        """
        print(f"[EnhancedExtractor] Attempting fallback extraction for: {url}")
        
        # First try trafilatura
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                metadata_traf = trafilatura.extract_metadata(downloaded)
                
                if text and len(text) > 100:
                    print("[EnhancedExtractor] Trafilatura extraction successful")
                    return (
                        metadata_traf.get('title', 'Untitled'),
                        text,
                        {'method': 'trafilatura', 'metadata': metadata_traf}
                    )
        except Exception as e:
            print(f"[EnhancedExtractor] Trafilatura failed: {e}")
        
        # If trafilatura fails, try Selenium
        if self.driver:
            try:
                return self.extract_with_js(url)
            except Exception as e:
                print(f"[EnhancedExtractor] Selenium extraction failed: {e}")
        
        raise RuntimeError(f"All extraction methods failed for URL: {url}")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print("[EnhancedExtractor] WebDriver closed")
    
    def __del__(self):
        """Cleanup WebDriver on object destruction"""
        self.close()