"""
Article extraction module for Django
Uses trafilatura with fallback to BeautifulSoup
"""
import trafilatura
from typing import Dict, Optional, Any
import logging
from datetime import datetime
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
import asyncio

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


class SeleniumArticleExtractor(ArticleExtractor):
    """
    Enhanced extractor using Selenium for JavaScript-heavy sites
    This is optional and requires selenium to be properly configured
    """
    
    def __init__(self):
        super().__init__()
        self.selenium_available = self._check_selenium_available()
    
    def _check_selenium_available(self) -> bool:
        """Check if Selenium is available and configured"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            return True
        except ImportError:
            logger.warning("Selenium not available, falling back to basic extraction")
            return False
    
    async def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article with Selenium fallback for JS sites
        """
        # First try regular extraction
        result = await super().extract(url)
        
        # If failed and URL requires JS, try Selenium
        if not result and self.selenium_available and self._requires_javascript(url):
            logger.info(f"Trying Selenium extraction for {url}")
            result = await self._extract_with_selenium(url)
        
        return result
    
    def _requires_javascript(self, url: str) -> bool:
        """Check if URL likely requires JavaScript"""
        js_sites = ['amna.gr', 'cnn.gr', 'skai.gr']  # Add more as needed
        domain = urlparse(url).netloc
        return any(site in domain for site in js_sites)
    
    async def _extract_with_selenium(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract using Selenium in a thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._selenium_extract_sync, url)
    
    def _selenium_extract_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """Synchronous Selenium extraction"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Get the rendered HTML
            html = driver.page_source
            
            # Use regular extraction on the rendered HTML
            return self._extract_with_trafilatura(html, url)
            
        except Exception as e:
            logger.error(f"Selenium extraction error: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()