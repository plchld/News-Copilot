"""
Tests for analysis handlers module
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from api.analysis_handlers import AnalysisHandler, transform_fact_check_response, transform_bias_response


class TestAnalysisHandler:
    """Test cases for analysis handler functionality"""
    
    @pytest.fixture
    def handler(self, mock_env_vars):
        """Create AnalysisHandler instance with mocked dependencies"""
        with patch('api.analysis_handlers.GrokClient'):
            return AnalysisHandler()
    
    def test_stream_event(self, handler):
        """Test server-sent event formatting"""
        event = handler.stream_event("progress", {"status": "Testing"})
        assert event == 'event: progress\ndata: {"status": "Testing"}\n\n'
    
    @patch('api.analysis_handlers.fetch_text')
    def test_get_augmentations_stream_fetch_error(self, mock_fetch, handler):
        """Test stream handling when article fetch fails"""
        # Mock fetch error
        mock_fetch.side_effect = RuntimeError("Failed to fetch")
        
        # Collect stream results
        results = list(handler.get_augmentations_stream("https://example.com"))
        
        # Check that appropriate events were sent
        assert any('"status": "Initializing augmentation..."' in r for r in results)
        assert any('"status": "Fetching article content..."' in r for r in results)
        assert any('event: error' in r for r in results)
        assert any('"message": "Error fetching article: Failed to fetch"' in r for r in results)
    
    @patch('api.analysis_handlers.fetch_text')
    def test_get_augmentations_stream_success(self, mock_fetch, handler, sample_article_text):
        """Test successful augmentation stream"""
        # Mock dependencies
        mock_fetch.return_value = sample_article_text
        
        # Mock Grok client responses
        mock_jargon_response = Mock()
        mock_jargon_response.choices = [Mock()]
        mock_jargon_response.choices[0].message.content = '{"terms": [{"term": "ΕΚΤ", "explanation": "Ευρωπαϊκή Κεντρική Τράπεζα"}]}'
        
        mock_viewpoints_response = Mock()
        mock_viewpoints_response.choices = [Mock()]
        mock_viewpoints_response.choices[0].message.content = "Alternative viewpoints text"
        
        handler.grok_client.create_completion = Mock(side_effect=[
            mock_jargon_response,
            mock_viewpoints_response
        ])
        handler.grok_client.extract_citations = Mock(return_value=["https://example.com"])
        
        # Collect stream results
        results = list(handler.get_augmentations_stream("https://example.com"))
        
        # Verify progress events
        assert any('"status": "Initializing augmentation..."' in r for r in results)
        assert any('"status": "Fetching article content..."' in r for r in results)
        assert any('"status": "Explaining terms and concepts..."' in r for r in results)
        assert any('"status": "Finding alternative viewpoints..."' in r for r in results)
        assert any('"status": "Done!"' in r for r in results)
        
        # Verify final result
        final_result = None
        for r in results:
            if 'event: final_result' in r:
                # Extract JSON data from the event
                data_line = r.split('\n')[1]
                data_json = data_line.replace('data: ', '')
                final_result = json.loads(data_json)
                break
        
        assert final_result is not None
        assert final_result['jargon']['terms'][0]['term'] == 'ΕΚΤ'
        assert final_result['viewpoints'] == "Alternative viewpoints text"
        assert final_result['jargon_citations'] == ["https://example.com"]
        assert final_result['viewpoints_citations'] == ["https://example.com"]
    
    @patch('api.analysis_handlers.fetch_text')
    def test_get_deep_analysis_fact_check(self, mock_fetch, handler, sample_article_text):
        """Test deep analysis for fact-checking"""
        # Mock dependencies
        mock_fetch.return_value = sample_article_text
        
        # Mock Grok response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "claims": [{
                "claim": "ΕΚΤ raised rates",
                "verdict": "True",
                "evidence": "Official ECB announcement",
                "confidence": "High",
                "sources": ["https://ecb.europa.eu"]
            }],
            "overall_credibility": "High",
            "red_flags": [],
            "verification_notes": "Verified with official sources"
        })
        
        handler.grok_client.create_completion = Mock(return_value=mock_response)
        handler.grok_client.extract_citations = Mock(return_value=["https://ecb.europa.eu"])
        
        # Call method
        result = handler.get_deep_analysis(
            "https://example.com",
            "fact-check",
            {"mode": "on"}
        )
        
        # Assertions
        assert result['analysis_type'] == 'fact-check'
        assert result['analysis']['claims'][0]['verdict'] == 'True'
        assert result['citations'] == ["https://ecb.europa.eu"]
    
    @patch('api.analysis_handlers.fetch_text')
    def test_get_deep_analysis_invalid_type(self, mock_fetch, handler, sample_article_text):
        """Test deep analysis with invalid analysis type"""
        mock_fetch.return_value = sample_article_text
        
        with pytest.raises(ValueError) as exc_info:
            handler.get_deep_analysis(
                "https://example.com",
                "invalid-type",
                {}
            )
        
        assert "Unknown analysis type: invalid-type" in str(exc_info.value)
    
    def test_get_analysis_schemas(self, handler):
        """Test that all required schemas are present"""
        schemas = handler._get_analysis_schemas()
        
        # Check all analysis types have schemas
        assert 'fact-check' in schemas
        assert 'bias' in schemas
        assert 'timeline' in schemas
        assert 'expert' in schemas
        
        # Check schema structure
        for schema_type, schema in schemas.items():
            assert schema['type'] == 'object'
            assert 'properties' in schema
    
    @patch('api.analysis_handlers.fetch_text')
    def test_get_augmentations_stream_jargon_error(self, mock_fetch, handler, sample_article_text):
        """Test stream handling when jargon analysis fails"""
        # Mock successful fetch
        mock_fetch.return_value = sample_article_text
        
        # Mock Grok client to raise error on jargon call
        # Ensure the coordinator is mocked if it's called directly
        if hasattr(handler, 'coordinator'):
             # Mock the coordinator's analyze_core method if it's the one making the call
            mock_coordinator = AsyncMock()
            mock_coordinator.analyze_core.return_value = {
                'success': False,
                'errors': {'jargon': 'API Error'},
                'results': {}
            }
            handler.coordinator = mock_coordinator
        else:
            # Fallback to mocking create_completion if coordinator is not used or structure is different
            handler.grok_client.create_completion = Mock(side_effect=Exception("API Error"))

        # Collect stream results
        # Since get_augmentations_stream is async, we need to handle it appropriately
        async def collect_results():
            results_list = []
            async for item in handler.get_augmentations_stream("https://example.com"):
                results_list.append(item)
            return results_list

        results = pytest. asyncio.run(collect_results())
        
        # Check that error event was sent
        assert any('event: error' in r for r in results)
        # The error message comes from the coordinator now
        assert any("Error during analysis." in r for r in results)


    def test_transform_fact_check_response(self):
        """Test the transform_fact_check_response function."""
        sample_fact_check_input = {
            "overall_credibility": "μέτρια",
            "claims": [
                {
                    "statement": "Claim 1",
                    "verified": True,
                    "explanation": "Explanation 1",
                    "sources": ["Source A"]
                }
            ],
            "red_flags": [],
            "missing_context": "None"
        }
        expected_fact_check_output = {
            "overall_credibility": "μέτρια",
            "claims": [
                {
                    "statement": "Claim 1",
                    "verified": True,
                    "explanation": "Explanation 1",
                    "sources": ["Source A"]
                }
            ],
            "red_flags": [],
            "missing_context": "None",
            "source_quality": {"score": "N/A", "description": "Source quality not assessed by agent"}
        }
        assert transform_fact_check_response(sample_fact_check_input.copy()) == expected_fact_check_output

        sample_empty_fact_check_input = {"overall_credibility": "χαμηλή", "claims": [], "red_flags": None} # Added red_flags:None
        expected_empty_fact_check_output = {
            "overall_credibility": "χαμηλή", 
            "claims": [],
            "red_flags": None,
            "source_quality": {"score": "N/A", "description": "Source quality not assessed by agent"}
        }
        assert transform_fact_check_response(sample_empty_fact_check_input.copy()) == expected_empty_fact_check_output

    def test_transform_bias_response(self):
        """Test the transform_bias_response function."""
        sample_bias_input = {
            "political_spectrum_analysis_greek": {
                "economic_axis_placement": "Κεντροαριστερά",
                "economic_axis_justification": "Justification econ",
                "social_axis_placement": "Φιλελεύθερη",
                "social_axis_justification": "Justification social",
                "overall_confidence": "Υψηλή"
            },
            "language_and_framing_analysis": {
                "emotionally_charged_terms": [
                    {"term": "term1", "explanation": "expl1"},
                    {"term": "term2", "explanation": "expl2"}
                ],
                "identified_framing_techniques": [
                    {"technique_name": "Framing1", "example_from_article": "Example1"},
                    {"technique_name": "Framing2", "example_from_article": "Example2"}
                ],
                "detected_tone": "μικτός",
                "missing_perspectives_summary": "Missing some perspectives."
            },
            "sources_diversity": "Adequate", # Added this as per schema
            "analysis_summary": "Summary of bias.", # Added this as per schema
            "supporting_evidence": ["Evidence 1"], # Added this as per schema
            "comparison": "Comparison text.", # This was an assumed field, not in schema
            "recommendations": "Recommendations text." # This was an assumed field, not in schema
        }
        expected_bias_output = {
            "political_lean": "Economic: Κεντροαριστερά, Social: Φιλελεύθερη",
            "emotional_tone": "μικτός",
            "confidence": "Υψηλή",
            "language_analysis": {
                "framing": "Framing1: \"Example1\"; Framing2: \"Example2\"", # Corrected example format
                "loaded_words": ["term1", "term2"],
                "missing_perspectives": "Missing some perspectives."
            },
            "comparison": "Comparison text.",
            "recommendations": "Recommendations text."
        }
        assert transform_bias_response(sample_bias_input.copy()) == expected_bias_output

        sample_empty_bias_input = {
            "political_spectrum_analysis_greek": {},
            "language_and_framing_analysis": {
                "emotionally_charged_terms": [],
                "identified_framing_techniques": [],
                # "detected_tone" is missing -> should default to N/A
                # "missing_perspectives_summary" is missing -> should default to N/A
            }
            # "comparison" is missing -> should default to N/A
            # "recommendations" is missing -> should default to N/A
        }
        expected_empty_bias_output = {
            "political_lean": "N/A", # Corrected based on helper
            "emotional_tone": "N/A",
            "confidence": "N/A",
            "language_analysis": {
                "framing": "N/A", # Corrected based on helper
                "loaded_words": [],
                "missing_perspectives": "N/A"
            },
            "comparison": "N/A",
            "recommendations": "N/A"
        }
        assert transform_bias_response(sample_empty_bias_input.copy()) == expected_empty_bias_output

# Need to add AsyncMock for Python < 3.8 if not already available
# For simplicity, assuming pytest-asyncio is installed and handles AsyncMock
from unittest.mock import MagicMock
if not hasattr(MagicMock, 'assert_awaited'): # Basic check for async mock capabilities
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)