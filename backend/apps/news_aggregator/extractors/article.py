"""
Enhanced article extraction module for Django
Uses trafilatura with Selenium fallback for JavaScript-heavy sites
"""
import trafilatura
from typing import Dict, Optional, Any
import logging
from datetime import datetime
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
import asyncio
import time
import re
import platform

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class ArticleExtractor:
    """Extract article content from URLs"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article content from URL
        
        Args:
            url: The article URL
            
        Returns:
            Dictionary with article data or None if extraction fails
        """
        try:
            # Fetch the HTML
            html = await self._fetch_html(url)
            if not html:
                logger.error(f"Failed to fetch HTML from {url}")
                return None
            
            # Try trafilatura first
            result = self._extract_with_trafilatura(html, url)
            
            # Fallback to BeautifulSoup if needed
            if not result or not result.get('content'):
                logger.info(f"Trafilatura failed for {url}, trying BeautifulSoup")
                result = self._extract_with_beautifulsoup(html, url)
            
            # Add metadata
            if result:
                result['url'] = url
                result['extracted_at'] = timezone.now()
                result['domain'] = urlparse(url).netloc
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {str(e)}")
            return None
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None
    
    def _extract_with_trafilatura(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract using trafilatura"""
        try:
            # Extract metadata
            metadata = trafilatura.extract_metadata(html, default_url=url)
            
            # Extract content
            content = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_images=False,
                favor_precision=True,
                target_language='el'
            )
            
            if not content:
                return None
            
            # Build result
            result = {
                'content': content,
                'title': metadata.title if metadata else '',
                'author': metadata.author if metadata else '',
                'published_at': None
            }
            
            # Parse date if available
            if metadata and metadata.date:
                try:
                    result['published_at'] = datetime.fromisoformat(metadata.date)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Trafilatura extraction error: {str(e)}")
            return None
    
    def _extract_with_beautifulsoup(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Fallback extraction using BeautifulSoup"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Try to find title
            title = ''
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            # Try to find author
            author = ''
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                author = author_meta.get('content', '')
            
            # Extract main content
            content = ''
            
            # Common article containers
            article_selectors = [
                'article',
                '[role="main"]',
                '.article-content',
                '.post-content',
                '.entry-content',
                '#content',
                'main'
            ]
            
            for selector in article_selectors:
                container = soup.select_one(selector)
                if container:
                    # Get all paragraphs
                    paragraphs = container.find_all('p')
                    if paragraphs:
                        content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        break
            
            # Fallback to all paragraphs
            if not content:
                all_paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in all_paragraphs if len(p.get_text(strip=True)) > 50])
            
            if not content:
                return None
            
            return {
                'title': title,
                'content': content,
                'author': author,
                'published_at': None
            }
            
        except Exception as e:
            logger.error(f"BeautifulSoup extraction error: {str(e)}")
            return None


def setup_undetected_chrome():
    """Setup undetected Chrome WebDriver that bypasses security issues"""
    try:
        import undetected_chromedriver as uc
        
        options = uc.ChromeOptions()
        
        # Headless mode
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Additional options for stability
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        
        # Try different approaches for version compatibility
        try:
            # First try with auto-detection
            driver = uc.Chrome(options=options, version_main=None)
        except Exception as e1:
            logger.debug(f"Auto-detection failed: {e1}")
            try:
                # Try with specific version (common current version)
                driver = uc.Chrome(options=options, version_main=136)
            except Exception as e2:
                logger.debug(f"Version 136 failed: {e2}")
                # Final fallback - let it detect automatically without version
                driver = uc.Chrome(options=options)
            
        logger.info("Undetected Chrome WebDriver setup successful")
        return driver
        
    except Exception as e:
        logger.error(f"Undetected Chrome setup error: {e}")
        raise


def setup_regular_chrome():
    """Setup regular Chrome WebDriver with standard options"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        logger.info("Regular Chrome WebDriver setup successful")
        return driver
        
    except Exception as e:
        logger.error(f"Regular Chrome setup error: {e}")
        raise


class EnhancedArticleExtractor(ArticleExtractor):
    """
    Enhanced extractor with Selenium support for JavaScript-heavy sites
    Migrated from legacy news-aggregator with full AMNA.gr support
    """
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.selenium_available = self._check_selenium_available()
        if self.selenium_available:
            self._setup_driver()
    
    def _check_selenium_available(self) -> bool:
        """Check if Selenium is available and configured"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            return True
        except ImportError:
            logger.warning("Selenium not available, falling back to basic extraction")
            return False
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            # Try undetected-chromedriver first (better for macOS security)
            try:
                self.driver = setup_undetected_chrome()
                logger.info("Undetected WebDriver initialized successfully")
            except:
                # Fallback to regular setup
                self.driver = setup_regular_chrome()
                logger.info("Regular WebDriver initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize WebDriver: {e}")
            self.driver = None
    
    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article with enhanced Selenium fallback for JS sites
        """
        # First try regular extraction
        result = await super().extract(url)
        
        # Check if we got meaningful content
        if result and result.get('content') and len(result['content']) > 100:
            logger.info(f"Basic extraction successful for {url}")
            return result
        
        # If failed or insufficient content and URL requires JS, try Selenium
        if self.selenium_available and self.driver and self._requires_javascript(url):
            logger.info(f"Trying enhanced Selenium extraction for {url}")
            result = await self._extract_with_selenium(url)
        
        return result
    
    def _requires_javascript(self, url: str) -> bool:
        """Check if URL likely requires JavaScript"""
        js_sites = [
            'amna.gr',      # Angular-based
            'cnn.gr',       # React/JavaScript
            'skai.gr',      # JavaScript-heavy
            'ant1news.gr',  # Dynamic loading
            'star.gr',      # JavaScript content
            'real.gr'       # Dynamic content
        ]
        domain = urlparse(url).netloc
        return any(site in domain for site in js_sites)
    
    async def _extract_with_selenium(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract using Selenium in a thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._selenium_extract_sync, url)
    
    def _selenium_extract_sync(self, url: str, wait_time: int = 5) -> Optional[Dict[str, Any]]:
        """
        Synchronous Selenium extraction with enhanced Greek news site support
        Migrated from legacy EnhancedExtractor with full functionality
        """
        if not self.driver:
            logger.error("WebDriver not available")
            return None
        
        try:
            logger.info(f"Loading URL with JavaScript: {url}")
            self.driver.get(url)
            
            # Enhanced waiting logic for Angular/JavaScript sites
            if 'amna.gr' in url:
                logger.info("Detected AMNA site, waiting for Angular...")
                time.sleep(wait_time + 3)  # Extra time for Angular
                
                # Try to wait for specific Angular elements
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.by import By
                    
                    # Wait for any ng-binding or article element
                    wait = WebDriverWait(self.driver, 10)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[ng-bind-html], .article-body, .content")))
                except Exception as e:
                    logger.debug(f"Angular wait failed, continuing: {e}")
                    pass
            else:
                time.sleep(wait_time)
            
            # Get page source after JS execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Enhanced content selectors for Greek news sites
            content_selectors = [
                '[ng-bind-html]',     # Angular binding (AMNA specific)
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
                '.text-content',
                '.story-body',        # CNN.gr
                '.article-wrapper',   # Various sites
                '.news-article',      # News sites
                '.post-body'          # Blog-style sites
            ]
            
            content = ""
            title_found = ""
            
            # Enhanced title extraction
            title_selectors = [
                'h1',
                '.article-title',
                '.title',
                '[class*="title"]',
                '.headline',
                '.story-headline',
                'h1.entry-title'
            ]
            
            for selector in title_selectors:
                elements = soup.select(selector)
                if elements:
                    potential_title = elements[0].get_text(strip=True)
                    if len(potential_title) > 10 and len(potential_title) < 300:
                        title_found = potential_title
                        logger.info(f"Found title: {title_found[:50]}...")
                        break
            
            # Enhanced content extraction
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    potential_content = elements[0].get_text(strip=True)
                    if len(potential_content) > 100:  # Ensure meaningful content
                        content = potential_content
                        logger.info(f"Found content with selector: {selector}")
                        break
            
            # If no specific content found, try enhanced body extraction
            if not content or len(content) < 100:
                logger.info("Trying enhanced body extraction")
                body = soup.find('body')
                if body:
                    # Remove unwanted elements
                    for script in body(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
                        script.decompose()
                    
                    # Get all paragraphs with better filtering
                    paragraphs = body.find_all('p')
                    if paragraphs:
                        # Filter paragraphs by length and content quality
                        good_paragraphs = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if (len(text) > 20 and 
                                not text.lower().startswith(('cookie', 'javascript', 'advertisement')) and
                                'cookie' not in text.lower()):
                                good_paragraphs.append(text)
                        
                        if good_paragraphs:
                            content = ' '.join(good_paragraphs)
                    
                    # Final fallback to all text
                    if not content:
                        content = body.get_text(strip=True)
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Remove common Greek site clutter
            content = re.sub(r'(Διαβάστε επίσης|Περισσότερα|Αναλυτικά|Δείτε όλα|Περισσότερες πληροφορίες).*?$', '', content, flags=re.MULTILINE)
            
            # Use found title if better than page title
            page_title = self.driver.title
            if title_found and (not page_title or "Αθηναϊκό - Μακεδονικό πρακτορείο ειδήσεων" in page_title):
                title = title_found
            else:
                title = page_title
            
            if not content or len(content) < 50:
                logger.warning(f"Insufficient content extracted from {url}")
                return None
            
            # Build result compatible with Django extractor format
            result = {
                'title': title,
                'content': content,
                'author': '',
                'published_at': None,
                'url': url,
                'extracted_at': timezone.now(),
                'domain': urlparse(url).netloc,
                'extraction_method': 'selenium'
            }
            
            logger.info(f"Selenium extraction successful: {len(content)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting with Selenium: {e}")
            return None
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except:
                pass
            self.driver = None
    
    def __del__(self):
        """Cleanup WebDriver on object destruction"""
        self.close()