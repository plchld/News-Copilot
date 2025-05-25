"""
Grok API client module for News Copilot
Handles all interactions with the Grok AI API
"""
from typing import Dict, Any, List, Optional
from openai import OpenAI, APIStatusError
from .config import API_KEY, API_URL, MODEL
from .search_params_builder import build_search_params
import json


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
            print(f"[GrokClient] Sending prompt to Grok (model: {self.model}):\n--- PROMPT START ---\n{prompt[:1000]}...\n--- PROMPT END ---", flush=True)
            if search_params:
                print(f"[GrokClient] With search_params: {json.dumps(search_params, indent=2, ensure_ascii=False)}", flush=True)
            if response_format:
                print(f"[GrokClient] With response_format: {json.dumps(response_format, indent=2, ensure_ascii=False)}", flush=True)
                
            completion = self.client.chat.completions.create(**params)
            
            if not stream:
                # For non-streamed responses, log the content directly
                if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
                    print(f"[GrokClient] Received Grok response content:\n--- RESPONSE CONTENT START ---\n{completion.choices[0].message.content[:1000]}...\n--- RESPONSE CONTENT END ---", flush=True)
                else:
                    print("[GrokClient] Received Grok response, but no message content found.", flush=True)
            else:
                # For streamed responses, we can't log the full content here easily.
                # The calling function (e.g., get_augmentations_stream) will handle streamed data.
                print("[GrokClient] Grok call set to stream. Full response content will not be logged here.", flush=True)

            return completion
            
        except APIStatusError as e:
            error_message = f"Grok API error: Status {e.status_code}, Response: {e.response.text if e.response else 'N/A'}"
            print(f"[GrokClient] API ERROR: {error_message}", flush=True)
            raise
        except Exception as e:
            error_message = f"Error calling Grok API: {type(e).__name__} - {e}"
            print(f"[GrokClient] ERROR: {error_message}", flush=True)
            raise RuntimeError(error_message)
    
    def create_thinking_completion(
        self,
        prompt: str,
        reasoning_effort: str = "low",
        temperature: float = 0.3,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create a completion using Grok's thinking models (grok-3-mini).
        
        Args:
            prompt: The prompt to send to Grok
            reasoning_effort: "low" or "high" - controls thinking depth
            temperature: Temperature for response generation
            response_format: Optional response format specification
            
        Returns:
            The completion response with reasoning_content available
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            params = {
                "model": "grok-3-mini-fast",  # Thinking model
                "messages": messages,
                "temperature": temperature,
                "extra_body": {"reasoning_effort": reasoning_effort}
            }
            
            if response_format:
                params["response_format"] = response_format
                
            completion = self.client.chat.completions.create(**params)
            
            # Log reasoning content if available
            if hasattr(completion.choices[0].message, 'reasoning_content'):
                print(f"[GrokClient] Reasoning: {completion.choices[0].message.reasoning_content[:200]}...")
                
            return completion
            
        except APIStatusError as e:
            error_message = f"Grok thinking API error: Status {e.status_code}"
            print(f"[GrokClient] THINKING API ERROR: {error_message}", flush=True)
            raise
        except Exception as e:
            error_message = f"Error calling Grok thinking API: {type(e).__name__} - {e}"
            print(f"[GrokClient] THINKING ERROR: {error_message}", flush=True)
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
        return build_search_params(
            mode="on",
            country="GR",
            language="el",
            max_results=20
        )