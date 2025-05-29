"""
Claude API Token Counting and Pricing Library
Handles token counting and cost calculation for Anthropic's Claude API
"""

import json
from typing import Dict, List, Union, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

try:
    import tiktoken
except ImportError:
    raise ImportError("Please install tiktoken: pip install tiktoken")


class ClaudeModel(Enum):
    """Claude model variants with their specifications"""
    # Model name: (input_price_per_million, output_price_per_million, context_window, max_output)
    # Opus 4.0 - Latest flagship model
    CLAUDE_OPUS_4 = ("claude-opus-4-20250514", 15.00, 75.00, 200000, 20000)
    SONNET_4 = ("claude-sonnet-4-20250307", 3.00, 15.00, 200000, 20000)
    
    # Sonnet 3.7 - New balanced model
    CLAUDE_3_7_SONNET = ("claude-3-7-sonnet-20250219", 3.00, 15.00, 200000, 8192)
    
    # Claude 3.5 Models (October 2024)
    CLAUDE_3_5_SONNET = ("claude-3-5-sonnet-20241022", 3.00, 15.00, 200000, 8192)
    CLAUDE_3_5_HAIKU = ("claude-3-5-haiku-20241022", 1.00, 5.00, 200000, 8192)
    
    # Claude 3 Models (Original)
    CLAUDE_3_OPUS = ("claude-3-opus-20240229", 15.00, 75.00, 200000, 4096)
    CLAUDE_3_SONNET = ("claude-3-sonnet-20240229", 3.00, 15.00, 200000, 4096)
    CLAUDE_3_HAIKU = ("claude-3-haiku-20240307", 0.25, 1.25, 200000, 4096)

    def __init__(self, model_id: str, input_price: float, output_price: float, 
                 context_window: int, max_output: int):
        self.model_id = model_id
        self.input_price_per_million = input_price
        self.output_price_per_million = output_price
        self.context_window = context_window
        self.max_output_tokens = max_output


@dataclass
class TokenUsage:
    """Container for token usage information"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: ClaudeModel
    web_searches: int = 0  # Number of web searches performed
    
    @property
    def input_cost(self) -> float:
        """Calculate input token cost in USD"""
        return (self.input_tokens / 1_000_000) * self.model.input_price_per_million
    
    @property
    def output_cost(self) -> float:
        """Calculate output token cost in USD"""
        return (self.output_tokens / 1_000_000) * self.model.output_price_per_million
    
    @property
    def web_search_cost(self) -> float:
        """Calculate web search cost in USD
        Web search pricing: $10 per 1000 searches ($0.01 per search)
        Based on Anthropic's actual pricing
        """
        return (self.web_searches / 1000) * 10.00
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost in USD including web searches"""
        return self.input_cost + self.output_cost + self.web_search_cost


@dataclass
class CostEstimate:
    """Detailed cost breakdown"""
    token_usage: TokenUsage
    estimated_cost_usd: float
    cost_breakdown: Dict[str, float]
    warnings: List[str]
    timestamp: datetime
    web_searches: int = 0


class ClaudeTokenCounter:
    """Main class for counting tokens and calculating costs for Claude API"""
    
    def __init__(self):
        # Claude uses a similar tokenizer to cl100k_base
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string
        
        Args:
            text: Input text to tokenize
            
        Returns:
            Number of tokens
        """
        tokens = len(self.encoding.encode(text))
        return tokens
    
    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count tokens in a message list (for chat format)
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Total number of tokens including formatting overhead
        """
        total_tokens = 0
        
        for message in messages:
            # Each message has overhead tokens for role and formatting
            total_tokens += 4  # Approximate overhead per message
            
            if 'role' in message:
                total_tokens += self.count_tokens(message['role'])
            
            if 'content' in message:
                if isinstance(message['content'], str):
                    total_tokens += self.count_tokens(message['content'])
                elif isinstance(message['content'], list):
                    # Handle multi-modal content
                    for content_item in message['content']:
                        if isinstance(content_item, dict):
                            if content_item.get('type') == 'text':
                                total_tokens += self.count_tokens(content_item.get('text', ''))
                            elif content_item.get('type') == 'image':
                                # Image tokens vary by size, using conservative estimate
                                total_tokens += 1600  # Approximate for standard image
        
        # Add base overhead for conversation
        total_tokens += 3
        
        return total_tokens
    
    def estimate_cost(self, 
                     input_text: Union[str, List[Dict[str, str]]], 
                     output_text: Optional[str] = None,
                     model: ClaudeModel = ClaudeModel.CLAUDE_3_7_SONNET,
                     expected_output_tokens: Optional[int] = None,
                     web_searches: int = 0) -> CostEstimate:
        """
        Estimate the cost of an API call
        
        Args:
            input_text: Input text or messages
            output_text: Actual output text (if available)
            model: Claude model to use
            expected_output_tokens: Expected output tokens if output_text not available
            web_searches: Number of web searches performed (default: 0)
            
        Returns:
            CostEstimate object with detailed breakdown including web search costs
        """
        warnings = []
        
        # Count input tokens
        if isinstance(input_text, str):
            input_tokens = self.count_tokens(input_text)
        else:
            input_tokens = self.count_message_tokens(input_text)
        
        # Count or estimate output tokens
        if output_text:
            output_tokens = self.count_tokens(output_text)
        elif expected_output_tokens:
            output_tokens = expected_output_tokens
        else:
            # Conservative estimate: 20% of input tokens
            output_tokens = int(input_tokens * 0.2)
            warnings.append(f"Output tokens estimated at 20% of input ({output_tokens} tokens)")
        
        # Check limits
        if input_tokens > model.context_window:
            warnings.append(f"Input tokens ({input_tokens}) exceed model context window ({model.context_window})")
        
        if output_tokens > model.max_output_tokens:
            warnings.append(f"Output tokens ({output_tokens}) exceed model max output ({model.max_output_tokens})")
        
        # Create token usage
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model=model,
            web_searches=web_searches
        )
        
        # Calculate costs
        cost_breakdown = {
            "input_cost_usd": usage.input_cost,
            "output_cost_usd": usage.output_cost,
            "web_search_cost_usd": usage.web_search_cost,
            "total_cost_usd": usage.total_cost,
            "cost_per_1k_tokens": (usage.total_cost / usage.total_tokens) * 1000 if usage.total_tokens > 0 else 0,
            "cost_per_search": 10.00 / 1000 if web_searches > 0 else 0
        }
        
        return CostEstimate(
            token_usage=usage,
            estimated_cost_usd=usage.total_cost,
            cost_breakdown=cost_breakdown,
            warnings=warnings,
            timestamp=datetime.now(),
            web_searches=web_searches
        )
    
    def batch_estimate(self, 
                      conversations: List[List[Dict[str, str]]], 
                      model: ClaudeModel = ClaudeModel.CLAUDE_3_5_SONNET) -> Dict:
        """
        Estimate costs for multiple conversations
        
        Args:
            conversations: List of conversation message lists
            model: Claude model to use
            
        Returns:
            Dictionary with batch statistics and individual estimates
        """
        estimates = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0
        
        for conv in conversations:
            estimate = self.estimate_cost(conv, model=model)
            estimates.append(estimate)
            total_input_tokens += estimate.token_usage.input_tokens
            total_output_tokens += estimate.token_usage.output_tokens
            total_cost += estimate.estimated_cost_usd
        
        return {
            "total_conversations": len(conversations),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_estimated_tokens": total_input_tokens + total_output_tokens,
            "total_estimated_cost_usd": total_cost,
            "average_cost_per_conversation": total_cost / len(conversations) if conversations else 0,
            "model": model.model_id,
            "individual_estimates": estimates
        }
    
    def compare_models(self, 
                      input_text: Union[str, List[Dict[str, str]]], 
                      expected_output_tokens: Optional[int] = None) -> Dict[str, CostEstimate]:
        """
        Compare costs across all Claude models
        
        Args:
            input_text: Input text or messages
            expected_output_tokens: Expected output tokens
            
        Returns:
            Dictionary mapping model names to cost estimates
        """
        comparisons = {}
        
        for model in ClaudeModel:
            estimate = self.estimate_cost(
                input_text=input_text,
                expected_output_tokens=expected_output_tokens,
                model=model
            )
            comparisons[model.model_id] = estimate
        
        return comparisons
    
    def format_cost_report(self, estimate: CostEstimate) -> str:
        """
        Format a cost estimate into a readable report
        
        Args:
            estimate: CostEstimate object
            
        Returns:
            Formatted string report
        """
        report = f"""
Claude API Cost Estimate Report
===============================
Model: {estimate.token_usage.model.model_id}
Timestamp: {estimate.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Token Usage:
-----------
Input Tokens:  {estimate.token_usage.input_tokens:,}
Output Tokens: {estimate.token_usage.output_tokens:,}
Total Tokens:  {estimate.token_usage.total_tokens:,}

Cost Breakdown:
--------------
Input Cost:  ${estimate.cost_breakdown['input_cost_usd']:.6f}
Output Cost: ${estimate.cost_breakdown['output_cost_usd']:.6f}"""
        
        # Add web search costs if applicable
        if estimate.web_searches > 0:
            report += f"""
Web Search Cost: ${estimate.cost_breakdown['web_search_cost_usd']:.6f}
Web Searches: {estimate.web_searches}"""
        
        report += f"""
Total Cost:  ${estimate.cost_breakdown['total_cost_usd']:.6f}

Cost per 1K tokens: ${estimate.cost_breakdown['cost_per_1k_tokens']:.4f}

Pricing Rates:
-------------
Input:  ${estimate.token_usage.model.input_price_per_million:.2f} per million tokens
Output: ${estimate.token_usage.model.output_price_per_million:.2f} per million tokens"""
        
        if estimate.web_searches > 0:
            report += f"""
Web Search: $10.00 per 1000 searches ($0.01 per search)"""
        
        report += "\n"
        
        if estimate.warnings:
            report += "\nWarnings:\n---------\n"
            for warning in estimate.warnings:
                report += f"⚠️  {warning}\n"
        
        return report
    
    def calculate_monthly_budget(self, 
                               daily_requests: int,
                               avg_input_tokens: int,
                               avg_output_tokens: int,
                               model: ClaudeModel = ClaudeModel.CLAUDE_3_7_SONNET,
                               days_per_month: int = 30) -> Dict:
        """
        Calculate estimated monthly budget for API usage
        
        Args:
            daily_requests: Number of API requests per day
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request
            model: Claude model to use
            days_per_month: Number of days to calculate for
            
        Returns:
            Dictionary with budget breakdown
        """
        # Calculate token usage
        daily_input_tokens = daily_requests * avg_input_tokens
        daily_output_tokens = daily_requests * avg_output_tokens
        
        monthly_input_tokens = daily_input_tokens * days_per_month
        monthly_output_tokens = daily_output_tokens * days_per_month
        
        # Calculate costs
        monthly_input_cost = (monthly_input_tokens / 1_000_000) * model.input_price_per_million
        monthly_output_cost = (monthly_output_tokens / 1_000_000) * model.output_price_per_million
        monthly_total_cost = monthly_input_cost + monthly_output_cost
        
        return {
            "model": model.model_id,
            "daily_requests": daily_requests,
            "days_per_month": days_per_month,
            "total_monthly_requests": daily_requests * days_per_month,
            "tokens": {
                "avg_input_per_request": avg_input_tokens,
                "avg_output_per_request": avg_output_tokens,
                "total_monthly_input": monthly_input_tokens,
                "total_monthly_output": monthly_output_tokens,
                "total_monthly": monthly_input_tokens + monthly_output_tokens
            },
            "costs": {
                "monthly_input_cost_usd": monthly_input_cost,
                "monthly_output_cost_usd": monthly_output_cost,
                "monthly_total_cost_usd": monthly_total_cost,
                "daily_average_cost_usd": monthly_total_cost / days_per_month,
                "cost_per_request_usd": monthly_total_cost / (daily_requests * days_per_month)
            },
            "pricing_info": {
                "input_price_per_million": model.input_price_per_million,
                "output_price_per_million": model.output_price_per_million
            }
        }


# Convenience functions
def quick_estimate(text: str, model_name: str = "claude-3-7-sonnet-20250219") -> Dict:
    """
    Quick cost estimate for a simple text input
    
    Args:
        text: Input text
        model_name: Model identifier
        
    Returns:
        Dictionary with basic cost information
    """
    counter = ClaudeTokenCounter()
    
    # Find model by ID
    model = None
    for m in ClaudeModel:
        if m.model_id == model_name:
            model = m
            break
    
    if not model:
        raise ValueError(f"Unknown model: {model_name}")
    
    estimate = counter.estimate_cost(text, model=model)
    
    return {
        "tokens": estimate.token_usage.total_tokens,
        "estimated_cost_usd": estimate.estimated_cost_usd,
        "model": model_name
    }


def calculate_conversation_cost(messages: List[Dict[str, str]], 
                              response: str,
                              model_name: str = "claude-3-7-sonnet-20250219",
                              web_searches: int = 0) -> Dict:
    """
    Calculate actual cost for a completed conversation
    
    Args:
        messages: Input messages
        response: Actual response text
        model_name: Model identifier
        web_searches: Number of web searches performed (default: 0)
        
    Returns:
        Dictionary with actual cost calculation including web search costs
    """
    counter = ClaudeTokenCounter()
    
    # Find model by ID
    model = None
    for m in ClaudeModel:
        if m.model_id == model_name:
            model = m
            break
    
    if not model:
        raise ValueError(f"Unknown model: {model_name}")
    
    estimate = counter.estimate_cost(messages, output_text=response, model=model, web_searches=web_searches)
    
    return {
        "input_tokens": estimate.token_usage.input_tokens,
        "output_tokens": estimate.token_usage.output_tokens,
        "total_tokens": estimate.token_usage.total_tokens,
        "web_searches": web_searches,
        "input_cost_usd": estimate.cost_breakdown["input_cost_usd"],
        "output_cost_usd": estimate.cost_breakdown["output_cost_usd"],
        "web_search_cost_usd": estimate.cost_breakdown["web_search_cost_usd"],
        "total_cost_usd": estimate.cost_breakdown["total_cost_usd"],
        "model": model_name
    }