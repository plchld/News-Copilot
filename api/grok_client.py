"""
Grok API client module for News Copilot
Handles all interactions with the Grok AI API
"""
from typing import Dict, Any, List, Optional
from openai import OpenAI, APIStatusError
from .config import API_KEY, API_URL, MODEL


class GrokClient:
    """Wrapper for Grok API interactions"""
    
    def __init__(self):
        if not API_KEY:
            raise ValueError("XAI_API_KEY not set in environment variables")
        self.client = OpenAI(api_key=API_KEY, base_url=API_URL)
        self.model = MODEL
        
    def create_completion(
        self,
        prompt: str,
        search_params: Optional[Dict[str, Any]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """
        Create a completion using the Grok API.
        
        Args:
            prompt: The prompt to send to Grok
            search_params: Optional search parameters for live search
            response_format: Optional response format specification
            stream: Whether to stream the response
            
        Returns:
            The completion response from Grok
            
        Raises:
            APIStatusError: If the API request fails
            RuntimeError: For other errors
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Build the request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "stream": stream
            }
            
            # Add optional parameters
            if search_params:
                params["extra_body"] = {"search_parameters": search_params}
            
            if response_format:
                params["response_format"] = response_format
                
            # Make the API call
            completion = self.client.chat.completions.create(**params)
            
            return completion
            
        except APIStatusError as e:
            error_message = f"Grok API error: Status {e.status_code}, Response: {e.response.text if e.response else 'N/A'}"
            print(f"[GrokClient] API ERROR: {error_message}", flush=True)
            raise
        except Exception as e:
            error_message = f"Error calling Grok API: {type(e).__name__} - {e}"
            print(f"[GrokClient] ERROR: {error_message}", flush=True)
            raise RuntimeError(error_message)
    
    @staticmethod
    def extract_citations(completion) -> List[str]:
        """
        Extract citations from a completion response.
        
        Args:
            completion: The completion response from Grok
            
        Returns:
            List of citation strings
        """
        citations = []
        
        # Check for citations at the completion level
        if hasattr(completion, 'citations') and completion.citations:
            citations = [str(c) for c in completion.citations]
        # Check for citations at the choice level
        elif hasattr(completion.choices[0], 'citations') and completion.choices[0].citations:
            citations = [str(c) for c in completion.choices[0].citations]
            
        return citations
    
    @staticmethod
    def get_default_search_params() -> Dict[str, Any]:
        """Get default search parameters for live search"""
        return {
            "mode": "on",
            "return_citations": True,
            "sources": [
                {"type": "web"},
                {"type": "news"}
            ]
        }