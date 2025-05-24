"""
Tests for Flask routes
"""
import pytest
import json
from unittest.mock import patch, Mock


class TestRoutes:
    """Test cases for Flask route endpoints"""
    
    def test_home_api_request(self, client):
        """Test home endpoint returns API info for non-HTML requests"""
        response = client.get('/', headers={'Accept': 'application/json'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['service'] == 'News Copilot API'
        assert data['status'] == 'running'
        assert 'endpoints' in data
        assert 'usage' in data
    
    def test_home_browser_request(self, client):
        """Test home endpoint serves HTML for browser requests"""
        with patch('flask.current_app.send_static_file') as mock_send:
            mock_send.return_value = '<html>Mock HTML</html>'
            response = client.get('/', headers={'Accept': 'text/html'})
            
            assert response.status_code == 200
            mock_send.assert_called_once_with('index.html')
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}
    
    def test_verification_pages(self, client):
        """Test static verification page endpoints"""
        with patch('flask.current_app.send_static_file') as mock_send:
            mock_send.return_value = '<html>Mock HTML</html>'
            
            # Test success page
            response = client.get('/verification-success.html')
            assert response.status_code == 200
            mock_send.assert_called_with('verification-success.html')
            
            # Test failed page
            response = client.get('/verification-failed.html')
            assert response.status_code == 200
            mock_send.assert_called_with('verification-failed.html')
            
            # Test expired page
            response = client.get('/verification-expired.html')
            assert response.status_code == 200
            # Should use failed page for now
            mock_send.assert_called_with('verification-failed.html')
    
    @patch('api.routes.analysis_handler.get_augmentations_stream')
    def test_augment_stream_success(self, mock_stream, client):
        """Test augment-stream endpoint with valid URL"""
        # Mock the stream generator
        def mock_generator(url):
            yield 'event: progress\ndata: {"status": "Testing"}\n\n'
            yield 'event: final_result\ndata: {"jargon": {"terms": []}}\n\n'
        
        mock_stream.return_value = mock_generator("test-url")
        
        # Make request
        response = client.get('/augment-stream?url=https://example.com/article')
        
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream'
        
        # Check response data
        data = response.get_data(as_text=True)
        assert 'event: progress' in data
        assert 'event: final_result' in data
    
    def test_augment_stream_missing_url(self, client):
        """Test augment-stream endpoint without URL parameter"""
        response = client.get('/augment-stream')
        
        assert response.status_code == 200
        assert response.content_type == 'text/event-stream'
        
        # Check error event
        data = response.get_data(as_text=True)
        assert 'event: error' in data
        assert 'Missing URL parameter' in data
    
    @patch('api.routes.analysis_handler.get_deep_analysis')
    def test_deep_analysis_success(self, mock_analysis, client):
        """Test deep-analysis endpoint with valid request"""
        # Mock analysis result
        mock_analysis.return_value = {
            'analysis': {'claims': []},
            'citations': ['https://example.com'],
            'analysis_type': 'fact-check'
        }
        
        # Make request
        response = client.post('/deep-analysis', 
            json={
                'url': 'https://example.com/article',
                'analysis_type': 'fact-check',
                'search_params': {'mode': 'on'}
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['analysis_type'] == 'fact-check'
    
    def test_deep_analysis_missing_params(self, client):
        """Test deep-analysis endpoint with missing parameters"""
        # Missing URL
        response = client.post('/deep-analysis', 
            json={'analysis_type': 'fact-check'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Missing URL or analysis_type' in data['error']
        
        # Missing analysis_type
        response = client.post('/deep-analysis', 
            json={'url': 'https://example.com'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Missing URL or analysis_type' in data['error']
    
    @patch('api.routes.analysis_handler.get_deep_analysis')
    def test_deep_analysis_error(self, mock_analysis, client):
        """Test deep-analysis endpoint error handling"""
        # Mock analysis error
        mock_analysis.side_effect = Exception("Analysis failed")
        
        # Make request
        response = client.post('/deep-analysis', 
            json={
                'url': 'https://example.com/article',
                'analysis_type': 'fact-check'
            }
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert 'Analysis failed' in data['error']