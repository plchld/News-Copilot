"""
Tests for article extraction module
"""
import pytest
from unittest.mock import Mock, patch
import urllib.error

from api.article_extractor import fetch_text


class TestArticleExtractor:
    """Test cases for article extraction functionality"""
    
    @patch('api.article_extractor.trafilatura.fetch_url')
    @patch('api.article_extractor.trafilatura.extract')
    def test_fetch_text_success(self, mock_extract, mock_fetch_url, sample_article_text):
        """Test successful article extraction"""
        # Mock trafilatura responses
        mock_fetch_url.return_value = "<html>Mock HTML content</html>"
        mock_extract.return_value = sample_article_text
        
        # Call function
        result = fetch_text("https://example.com/article")
        
        # Assertions
        assert result == sample_article_text.strip()
        mock_fetch_url.assert_called_once_with("https://example.com/article")
        mock_extract.assert_called_once_with("<html>Mock HTML content</html>")
    
    @patch('api.article_extractor.trafilatura.fetch_url')
    def test_fetch_text_http_error(self, mock_fetch_url):
        """Test handling of HTTP errors"""
        # Mock HTTP error
        mock_fetch_url.side_effect = urllib.error.HTTPError(
            "https://example.com/article", 404, "Not Found", {}, None
        )
        
        # Call function and expect error
        with pytest.raises(RuntimeError) as exc_info:
            fetch_text("https://example.com/article")
        
        assert "HTTPError" in str(exc_info.value)
        assert "404" in str(exc_info.value)
    
    @patch('api.article_extractor.trafilatura.fetch_url')
    def test_fetch_text_generic_error(self, mock_fetch_url):
        """Test handling of generic errors"""
        # Mock generic error
        mock_fetch_url.side_effect = Exception("Network error")
        
        # Call function and expect error
        with pytest.raises(RuntimeError) as exc_info:
            fetch_text("https://example.com/article")
        
        assert "Generic error" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)
    
    @patch('api.article_extractor.trafilatura.fetch_url')
    def test_fetch_text_no_content(self, mock_fetch_url):
        """Test handling when no content is downloaded"""
        # Mock no content
        mock_fetch_url.return_value = None
        
        # Call function and expect error
        with pytest.raises(RuntimeError) as exc_info:
            fetch_text("https://example.com/article")
        
        assert "Could not download content" in str(exc_info.value)
    
    @patch('api.article_extractor.trafilatura.fetch_url')
    @patch('api.article_extractor.trafilatura.extract')
    def test_fetch_text_extraction_failed(self, mock_extract, mock_fetch_url):
        """Test handling when text extraction fails"""
        # Mock successful download but failed extraction
        mock_fetch_url.return_value = "<html>Mock HTML content</html>"
        mock_extract.return_value = None
        
        # Call function and expect error
        with pytest.raises(RuntimeError) as exc_info:
            fetch_text("https://example.com/article")
        
        assert "failed to extract main text" in str(exc_info.value)
    
    @patch('api.article_extractor.trafilatura.fetch_url')
    @patch('api.article_extractor.trafilatura.extract')
    def test_fetch_text_whitespace_cleanup(self, mock_extract, mock_fetch_url):
        """Test that whitespace is properly cleaned up"""
        # Mock content with excessive whitespace
        mock_fetch_url.return_value = "<html>Mock HTML content</html>"
        mock_extract.return_value = "Line 1  \n  \nLine 2   \n\n\nLine 3"
        
        # Call function
        result = fetch_text("https://example.com/article")
        
        # Check that excessive whitespace is cleaned
        assert result == "Line 1\n\nLine 2\n\n\nLine 3"