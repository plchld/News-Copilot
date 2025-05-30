"""Cache optimization utilities and strategies"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CacheStrategy(Enum):
    """Different caching strategies"""
    AGGRESSIVE = "aggressive"  # Maximize cache reuse, longer conversations
    BALANCED = "balanced"     # Balance cache benefits with conversation length
    CONSERVATIVE = "conservative"  # Shorter conversations, prioritize accuracy


@dataclass
class CacheOptimizationConfig:
    """Configuration for cache optimization"""
    
    # Strategy settings
    strategy: CacheStrategy = CacheStrategy.BALANCED
    target_cache_hit_ratio: float = 0.7
    
    # Provider-specific settings
    anthropic_5m_discount: float = 0.9  # 90% discount on cache hits
    anthropic_1h_discount: float = 0.9  # Same discount, but costs more to write
    openai_cache_discount: float = 0.75  # 75% discount
    gemini_cache_discount: float = 0.75  # 75% discount
    
    # Cost thresholds
    max_acceptable_cost_per_story: float = 0.05  # $0.05 per story
    cost_increase_threshold: float = 0.2  # 20% cost increase is acceptable for quality
    
    # Timing settings
    conversation_timeout_minutes: int = 10
    cache_refresh_threshold: float = 0.8  # Refresh when 80% of TTL elapsed


class CacheOptimizer:
    """Optimizer for prompt caching strategies"""
    
    def __init__(self, config: CacheOptimizationConfig):
        """Initialize cache optimizer
        
        Args:
            config: Cache optimization configuration
        """
        self.config = config
        self.performance_history: List[Dict[str, Any]] = []
        
    def optimize_batch_strategy(
        self,
        stories: List[Dict[str, Any]],
        analysis_types: List[str],
        provider: str = "anthropic"
    ) -> Dict[str, Any]:
        """Optimize batching strategy for given stories and analysis types
        
        Args:
            stories: Stories to analyze
            analysis_types: Types of analysis requested
            provider: AI provider being used
            
        Returns:
            Optimized batch configuration
        """
        # Calculate optimal batch sizes based on cache efficiency
        batch_config = self._calculate_optimal_batches(
            len(stories),
            analysis_types,
            provider
        )
        
        # Determine cache TTL strategy
        cache_strategy = self._select_cache_ttl_strategy(
            len(stories),
            analysis_types,
            provider
        )
        
        # Calculate expected costs and savings
        cost_analysis = self._estimate_costs_and_savings(
            len(stories),
            analysis_types,
            batch_config,
            provider
        )
        
        return {
            "batch_configuration": batch_config,
            "cache_strategy": cache_strategy,
            "cost_analysis": cost_analysis,
            "optimization_metadata": {
                "strategy": self.config.strategy.value,
                "target_cache_ratio": self.config.target_cache_hit_ratio,
                "provider": provider
            }
        }
    
    def _calculate_optimal_batches(
        self,
        story_count: int,
        analysis_types: List[str],
        provider: str
    ) -> Dict[str, Any]:
        """Calculate optimal batch sizes for cache efficiency"""
        
        # Base batch sizes by analysis complexity
        base_batch_sizes = {
            "greek_perspective": 12,
            "international_perspective": 10,
            "opposing_view": 8,
            "fact_verification": 6,  # More complex, smaller batches
            "synthesis": 5,         # Most complex
            "jargon_context": 15,   # Simple, larger batches
            "timeline": 8,
            "social_pulse": 10
        }
        
        # Adjust based on provider cache characteristics
        provider_multipliers = {
            "anthropic": 1.2,  # Better caching, can handle larger batches
            "grok": 1.0,       # Standard
            "gemini": 1.1,     # Good for large contexts
            "openai": 0.9      # More conservative
        }
        
        multiplier = provider_multipliers.get(provider, 1.0)
        
        # Adjust based on strategy
        strategy_multipliers = {
            CacheStrategy.AGGRESSIVE: 1.5,
            CacheStrategy.BALANCED: 1.0,
            CacheStrategy.CONSERVATIVE: 0.7
        }
        
        strategy_mult = strategy_multipliers[self.config.strategy]
        
        # Calculate final batch sizes
        optimized_batches = {}
        for analysis_type in analysis_types:
            base_size = base_batch_sizes.get(analysis_type, 8)
            optimized_size = int(base_size * multiplier * strategy_mult)
            
            # Ensure reasonable bounds
            optimized_size = max(3, min(optimized_size, 20))
            
            # Adjust for story count
            if story_count < optimized_size:
                optimized_size = story_count
            elif story_count < optimized_size * 2:
                # If close to 2x batch size, split evenly
                optimized_size = story_count // 2 + 1
            
            optimized_batches[analysis_type] = optimized_size
        
        return {
            "batch_sizes": optimized_batches,
            "expected_batches_per_type": {
                analysis_type: (story_count + size - 1) // size
                for analysis_type, size in optimized_batches.items()
            },
            "total_conversations": sum(
                (story_count + size - 1) // size
                for size in optimized_batches.values()
            )
        }
    
    def _select_cache_ttl_strategy(
        self,
        story_count: int,
        analysis_types: List[str],
        provider: str
    ) -> Dict[str, Any]:
        """Select optimal cache TTL strategy"""
        
        # Estimate processing time
        estimated_processing_minutes = self._estimate_processing_time(
            story_count,
            analysis_types
        )
        
        # Default to 5-minute cache
        recommended_ttl = "5m"
        ttl_reasoning = "Standard 5-minute cache for regular processing"
        
        # Consider 1-hour cache for longer processing
        if provider == "anthropic" and estimated_processing_minutes > 8:
            # 1-hour cache costs more to write but better for longer sessions
            one_hour_cost = self._calculate_1h_cache_cost(story_count, analysis_types)
            five_min_cost = self._calculate_5m_cache_cost(story_count, analysis_types)
            
            if one_hour_cost < five_min_cost * 1.1:  # If within 10% cost
                recommended_ttl = "1h"
                ttl_reasoning = f"1-hour cache recommended for {estimated_processing_minutes:.1f}min processing time"
        
        return {
            "recommended_ttl": recommended_ttl,
            "reasoning": ttl_reasoning,
            "estimated_processing_minutes": estimated_processing_minutes,
            "alternative_options": {
                "5m": "Lower write cost, good for <5min processing",
                "1h": "Higher write cost, better for >8min processing"
            } if provider == "anthropic" else {}
        }
    
    def _estimate_processing_time(
        self,
        story_count: int,
        analysis_types: List[str]
    ) -> float:
        """Estimate total processing time in minutes"""
        
        # Base time estimates per story per analysis type (in seconds)
        base_times = {
            "greek_perspective": 8,
            "international_perspective": 10,
            "opposing_view": 12,
            "fact_verification": 15,
            "synthesis": 20,
            "jargon_context": 6,
            "timeline": 10,
            "social_pulse": 8
        }
        
        total_seconds = 0
        for analysis_type in analysis_types:
            time_per_story = base_times.get(analysis_type, 10)
            total_seconds += story_count * time_per_story
        
        # Account for parallel processing and caching speedup
        cache_speedup = 0.6  # 40% faster with good caching
        parallelism_factor = 0.8  # Some parallelism benefits
        
        total_seconds *= cache_speedup * parallelism_factor
        
        return total_seconds / 60  # Convert to minutes
    
    def _estimate_costs_and_savings(
        self,
        story_count: int,
        analysis_types: List[str],
        batch_config: Dict[str, Any],
        provider: str
    ) -> Dict[str, Any]:
        """Estimate costs and savings from caching"""
        
        # Estimate token usage
        tokens_per_analysis = {
            "greek_perspective": {"input": 1200, "output": 800},
            "international_perspective": {"input": 1400, "output": 900},
            "opposing_view": {"input": 1100, "output": 700},
            "fact_verification": {"input": 1300, "output": 600},
            "synthesis": {"input": 2000, "output": 1200},
            "jargon_context": {"input": 800, "output": 400},
            "timeline": {"input": 1000, "output": 600},
            "social_pulse": {"input": 900, "output": 500}
        }
        
        # Provider pricing per 1K tokens
        provider_pricing = {
            "anthropic": {"input": 0.003, "output": 0.015, "cache_write": 0.00375, "cache_read": 0.0003},
            "grok": {"input": 0.002, "output": 0.01, "cache_discount": 0.75},
            "gemini": {"input": 0.001, "output": 0.008, "cache_discount": 0.75},
            "openai": {"input": 0.0025, "output": 0.012, "cache_discount": 0.75}
        }
        
        pricing = provider_pricing.get(provider, provider_pricing["anthropic"])
        
        # Calculate costs without caching
        total_cost_without_cache = 0
        total_input_tokens = 0
        total_output_tokens = 0
        
        for analysis_type in analysis_types:
            type_tokens = tokens_per_analysis.get(analysis_type, {"input": 1000, "output": 600})
            input_tokens = story_count * type_tokens["input"]
            output_tokens = story_count * type_tokens["output"]
            
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            total_cost_without_cache += (
                input_tokens * pricing["input"] / 1000 +
                output_tokens * pricing["output"] / 1000
            )
        
        # Calculate costs with caching
        estimated_cache_hit_ratio = self._estimate_cache_hit_ratio(batch_config, analysis_types)
        
        if provider == "anthropic":
            # Anthropic-specific caching calculation
            cache_write_tokens = total_input_tokens * (1 - estimated_cache_hit_ratio)
            cache_read_tokens = total_input_tokens * estimated_cache_hit_ratio
            regular_input_tokens = total_input_tokens * 0.1  # Small portion not cached
            
            total_cost_with_cache = (
                cache_write_tokens * pricing["cache_write"] / 1000 +
                cache_read_tokens * pricing["cache_read"] / 1000 +
                regular_input_tokens * pricing["input"] / 1000 +
                total_output_tokens * pricing["output"] / 1000
            )
        else:
            # Other providers with simple discount model
            cache_discount = pricing.get("cache_discount", 0.75)
            cached_input_cost = total_input_tokens * estimated_cache_hit_ratio * pricing["input"] * (1 - cache_discount) / 1000
            regular_input_cost = total_input_tokens * (1 - estimated_cache_hit_ratio) * pricing["input"] / 1000
            output_cost = total_output_tokens * pricing["output"] / 1000
            
            total_cost_with_cache = cached_input_cost + regular_input_cost + output_cost
        
        # Calculate savings
        absolute_savings = total_cost_without_cache - total_cost_with_cache
        percentage_savings = (absolute_savings / total_cost_without_cache) * 100 if total_cost_without_cache > 0 else 0
        
        return {
            "without_caching": {
                "total_cost": total_cost_without_cache,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cost_per_story": total_cost_without_cache / story_count if story_count > 0 else 0
            },
            "with_caching": {
                "total_cost": total_cost_with_cache,
                "estimated_cache_hit_ratio": estimated_cache_hit_ratio,
                "cost_per_story": total_cost_with_cache / story_count if story_count > 0 else 0
            },
            "savings": {
                "absolute_dollars": absolute_savings,
                "percentage": percentage_savings,
                "cost_efficiency": "excellent" if percentage_savings > 70 else "good" if percentage_savings > 50 else "moderate"
            },
            "recommendations": self._generate_cost_recommendations(
                total_cost_with_cache / story_count if story_count > 0 else 0,
                percentage_savings,
                estimated_cache_hit_ratio
            )
        }
    
    def _estimate_cache_hit_ratio(
        self,
        batch_config: Dict[str, Any],
        analysis_types: List[str]
    ) -> float:
        """Estimate cache hit ratio based on batch configuration"""
        
        # Base cache hit ratios by analysis type (how much can be cached)
        base_cache_ratios = {
            "greek_perspective": 0.85,  # High cacheable system prompt
            "international_perspective": 0.82,
            "opposing_view": 0.78,
            "fact_verification": 0.75,  # More variable content
            "synthesis": 0.70,         # Depends on input variations
            "jargon_context": 0.88,    # Very cacheable
            "timeline": 0.80,
            "social_pulse": 0.75
        }
        
        # Calculate weighted average
        total_weight = 0
        weighted_ratio = 0
        
        for analysis_type in analysis_types:
            base_ratio = base_cache_ratios.get(analysis_type, 0.75)
            batch_size = batch_config["batch_sizes"].get(analysis_type, 1)
            
            # Larger batches have better cache hit ratios
            batch_bonus = min(0.1, (batch_size - 5) * 0.01)
            adjusted_ratio = min(0.95, base_ratio + batch_bonus)
            
            weight = 1  # Equal weight for now
            weighted_ratio += adjusted_ratio * weight
            total_weight += weight
        
        return weighted_ratio / total_weight if total_weight > 0 else 0.75
    
    def _calculate_5m_cache_cost(self, story_count: int, analysis_types: List[str]) -> float:
        """Calculate cost for 5-minute cache strategy"""
        # Simplified calculation - would need actual token estimates
        base_cost_per_story = 0.02
        cache_savings = 0.7  # 70% savings
        return story_count * base_cost_per_story * (1 - cache_savings)
    
    def _calculate_1h_cache_cost(self, story_count: int, analysis_types: List[str]) -> float:
        """Calculate cost for 1-hour cache strategy"""
        # 1-hour cache costs 2x to write but same discount on reads
        base_cost_per_story = 0.02
        cache_write_premium = 1.6  # 60% more expensive to write
        cache_savings = 0.7  # Same 70% savings on reads
        
        # Assume 80% of tokens are cached
        cache_ratio = 0.8
        return story_count * base_cost_per_story * (
            cache_ratio * cache_write_premium * (1 - cache_savings) +
            (1 - cache_ratio)
        )
    
    def _generate_cost_recommendations(
        self,
        cost_per_story: float,
        percentage_savings: float,
        cache_hit_ratio: float
    ) -> List[str]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        if cost_per_story > self.config.max_acceptable_cost_per_story:
            recommendations.append(
                f"Cost per story (${cost_per_story:.3f}) exceeds target (${self.config.max_acceptable_cost_per_story:.3f}). "
                "Consider smaller batch sizes or simpler analysis types."
            )
        
        if percentage_savings < 50:
            recommendations.append(
                f"Cache savings ({percentage_savings:.1f}%) below optimal. "
                "Increase batch sizes or improve prompt caching structure."
            )
        
        if cache_hit_ratio < self.config.target_cache_hit_ratio:
            recommendations.append(
                f"Cache hit ratio ({cache_hit_ratio:.1f}) below target ({self.config.target_cache_hit_ratio:.1f}). "
                "Review prompt structure and conversation design."
            )
        
        if not recommendations:
            recommendations.append("Cost optimization looks good! Current configuration is efficient.")
        
        return recommendations
    
    def record_performance(self, performance_data: Dict[str, Any]):
        """Record performance data for learning"""
        performance_data["timestamp"] = time.time()
        self.performance_history.append(performance_data)
        
        # Keep only recent history
        max_history = 100
        if len(self.performance_history) > max_history:
            self.performance_history = self.performance_history[-max_history:]
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get insights from performance history"""
        if not self.performance_history:
            return {"message": "No performance data available"}
        
        recent_performance = self.performance_history[-10:]  # Last 10 runs
        
        avg_cache_hit_ratio = sum(
            p.get("cache_hit_ratio", 0) for p in recent_performance
        ) / len(recent_performance)
        
        avg_cost_per_story = sum(
            p.get("cost_per_story", 0) for p in recent_performance
        ) / len(recent_performance)
        
        avg_savings = sum(
            p.get("percentage_savings", 0) for p in recent_performance
        ) / len(recent_performance)
        
        return {
            "recent_performance": {
                "avg_cache_hit_ratio": avg_cache_hit_ratio,
                "avg_cost_per_story": avg_cost_per_story,
                "avg_percentage_savings": avg_savings
            },
            "trends": {
                "cache_efficiency": "improving" if avg_cache_hit_ratio > 0.7 else "needs_work",
                "cost_efficiency": "good" if avg_cost_per_story < self.config.max_acceptable_cost_per_story else "high"
            },
            "total_runs": len(self.performance_history)
        }