"""
Tests for Grok API client module
"""
import pytest
from unittest.mock import Mock, patch
from openai import APIStatusError

from api.grok_client import GrokClient


class TestGrokClient:
    """Test cases for Grok API client functionality"""
    
    def test_init_without_api_key(self, monkeypatch):
        """Test initialization without API key raises error"""
        monkeypatch.delenv("XAI_API_KEY", raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            GrokClient()
        
        assert "XAI_API_KEY not set" in str(exc_info.value)
    
    @patch('api.grok_client.OpenAI')
    def test_init_with_api_key(self, mock_openai, mock_env_vars):
        """Test successful initialization with API key"""
        client = GrokClient()
        
        mock_openai.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://api.x.ai/v1"
        )
        assert client.model == "grok-3"
    
    @patch('api.grok_client.OpenAI')
    def test_create_completion_success(self, mock_openai, mock_env_vars, mock_grok_response):
        """Test successful completion creation"""
        # Setup mock
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.return_value = mock_grok_response
        
        # Create client and call method
        client = GrokClient()
        result = client.create_completion(
            prompt="Test prompt",
            search_params={"mode": "on"},
            response_format={"type": "json_object"},
            stream=False
        )
        
        # Assertions
        assert result == mock_grok_response
        mock_client_instance.chat.completions.create.assert_called_once()
        
        # Check call arguments
        call_args = mock_client_instance.chat.completions.create.call_args
        assert call_args.kwargs['model'] == "grok-3"
        assert call_args.kwargs['messages'][0]['content'] == "Test prompt"
        assert call_args.kwargs['extra_body']['search_parameters']['mode'] == "on"
        assert call_args.kwargs['response_format']['type'] == "json_object"
        assert call_args.kwargs['stream'] is False
    
    @patch('api.grok_client.OpenAI')
    def test_create_completion_api_error(self, mock_openai, mock_env_vars):
        """Test handling of API errors"""
        # Setup mock
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        
        # Create mock error response
        mock_response = Mock()
        mock_response.text = "Rate limit exceeded"
        error = APIStatusError(
            message="API Error",
            response=mock_response,
            body=None
        )
        error.status_code = 429
        mock_client_instance.chat.completions.create.side_effect = error
        
        # Create client and expect error
        client = GrokClient()
        with pytest.raises(APIStatusError):
            client.create_completion(prompt="Test prompt")
    
    @patch('api.grok_client.OpenAI')
    def test_create_completion_generic_error(self, mock_openai, mock_env_vars):
        """Test handling of generic errors"""
        # Setup mock
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("Network error")
        
        # Create client and expect error
        client = GrokClient()
        with pytest.raises(RuntimeError) as exc_info:
            client.create_completion(prompt="Test prompt")
        
        assert "Error calling Grok API" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)
    
    def test_extract_citations_from_completion(self, mock_grok_response):
        """Test citation extraction from completion level"""
        citations = GrokClient.extract_citations(mock_grok_response)
        assert citations == ["https://ecb.europa.eu"]
    
    def test_extract_citations_from_choice(self):
        """Test citation extraction from choice level"""
        # Create mock response with citations at choice level
        mock_response = Mock()
        mock_response.citations = None
        mock_response.choices = [Mock()]
        mock_response.choices[0].citations = ["https://example.com", "https://test.com"]
        
        citations = GrokClient.extract_citations(mock_response)
        assert citations == ["https://example.com", "https://test.com"]
    
    def test_extract_citations_no_citations(self):
        """Test citation extraction when no citations present"""
        # Create mock response without citations
        mock_response = Mock()
        mock_response.citations = None
        mock_response.choices = [Mock()]
        mock_response.choices[0].citations = None
        
        citations = GrokClient.extract_citations(mock_response)
        assert citations == []
    
    def test_get_default_search_params(self):
        """Test default search parameters"""
        params = GrokClient.get_default_search_params()
        
        assert params["mode"] == "on"
        assert params["return_citations"] is True
        assert len(params["sources"]) == 2
        assert {"type": "web"} in params["sources"]
        assert {"type": "news"} in params["sources"]