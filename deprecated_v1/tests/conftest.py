"""
Pytest configuration and fixtures for News Copilot tests
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("XAI_API_KEY", "test-api-key")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setenv("BASE_URL", "http://localhost:8080")
    monkeypatch.setenv("FLASK_PORT", "8080")


@pytest.fixture
def sample_article_text():
    """Sample article text for testing"""
    return """
    Η Ευρωπαϊκή Κεντρική Τράπεζα (ΕΚΤ) ανακοίνωσε σήμερα την αύξηση των επιτοκίων κατά 25 μονάδες βάσης.
    Ο πρόεδρος της ΕΚΤ, Christine Lagarde, δήλωσε ότι η απόφαση ελήφθη για την αντιμετώπιση του πληθωρισμού.
    Το ΑΕΠ της Ευρωζώνης αναμένεται να αυξηθεί κατά 2% το 2024.
    """


@pytest.fixture
def sample_article_url():
    """Sample article URL for testing"""
    return "https://www.kathimerini.gr/test-article"


@pytest.fixture
def mock_grok_response():
    """Mock response from Grok API"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = '{"terms": [{"term": "ΕΚΤ", "explanation": "Ευρωπαϊκή Κεντρική Τράπεζα"}]}'
    mock_response.citations = ["https://ecb.europa.eu"]
    return mock_response


@pytest.fixture
def mock_trafilatura_response():
    """Mock response from trafilatura"""
    return """
    Η Ευρωπαϊκή Κεντρική Τράπεζα (ΕΚΤ) ανακοίνωσε σήμερα την αύξηση των επιτοκίων κατά 25 μονάδες βάσης.
    """


@pytest.fixture
def app(mock_env_vars, monkeypatch):
    """Create Flask app for testing"""
    # Disable authentication for tests
    monkeypatch.setenv("AUTH_ENABLED", "false")
    
    from api.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask test CLI runner"""
    return app.test_cli_runner()