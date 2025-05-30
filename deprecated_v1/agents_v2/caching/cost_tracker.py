"""Cost tracking and monitoring for cached operations"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CostRecord:
    """Record of costs for a single operation"""
    
    timestamp: float
    operation_id: str
    operation_type: str  # "discovery", "analysis", "synthesis", etc.
    
    # Token usage
    input_tokens: int
    output_tokens: int
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    
    # Cost breakdown
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_write_cost: float = 0.0
    cache_read_cost: float = 0.0
    total_cost: float = 0.0
    
    # Metadata
    provider: str = ""
    model: str = ""
    cache_hit_ratio: float = 0.0
    stories_processed: int = 0
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.total_cost = (
            self.input_cost + 
            self.output_cost + 
            self.cache_write_cost + 
            self.cache_read_cost
        )
        
        total_input = self.input_tokens + self.cache_write_tokens + self.cache_read_tokens
        self.cache_hit_ratio = self.cache_read_tokens / max(total_input, 1)


class CostTracker:
    """Tracks and analyzes costs with caching optimizations"""
    
    def __init__(self, save_to_file: bool = True, file_path: str = "cost_tracking.json"):
        """Initialize cost tracker
        
        Args:
            save_to_file: Whether to save records to file
            file_path: Path to save cost records
        """
        self.save_to_file = save_to_file
        self.file_path = file_path
        self.cost_records: List[CostRecord] = []
        
        # Provider pricing (per 1K tokens)
        self.provider_pricing = {
            "anthropic": {
                "claude-opus-4": {
                    "input": 0.015,
                    "output": 0.075,
                    "cache_write_5m": 0.01875,  # 1.25x base
                    "cache_write_1h": 0.03,     # 2x base
                    "cache_read": 0.0015        # 0.1x base
                },
                "claude-sonnet-4": {
                    "input": 0.003,
                    "output": 0.015,
                    "cache_write_5m": 0.00375,
                    "cache_write_1h": 0.006,
                    "cache_read": 0.0003
                },
                "claude-haiku-3.5": {
                    "input": 0.0008,
                    "output": 0.004,
                    "cache_write_5m": 0.001,
                    "cache_write_1h": 0.0016,
                    "cache_read": 0.00008
                }
            },
            "grok": {
                "grok-3": {
                    "input": 0.002,
                    "output": 0.01,
                    "cache_discount": 0.75  # 75% discount on cached tokens
                },
                "grok-3-mini": {
                    "input": 0.0005,
                    "output": 0.002,
                    "cache_discount": 0.75
                }
            },
            "gemini": {
                "gemini-2.0-flash": {
                    "input": 0.001,
                    "output": 0.008,
                    "cache_discount": 0.75
                },
                "gemini-2.5-flash": {
                    "input": 0.0015,
                    "output": 0.01,
                    "cache_discount": 0.75
                }
            },
            "openai": {
                "gpt-4o": {
                    "input": 0.0025,
                    "output": 0.012,
                    "cache_discount": 0.75
                }
            }
        }
        
        # Load existing records
        self._load_records()
    
    def record_operation(
        self,
        operation_id: str,
        operation_type: str,
        usage_data: Dict[str, Any],
        provider: str,
        model: str,
        stories_processed: int = 1,
        cache_ttl: str = "5m"
    ) -> CostRecord:
        """Record costs for an operation
        
        Args:
            operation_id: Unique identifier for operation
            operation_type: Type of operation
            usage_data: Token usage data from API response
            provider: AI provider used
            model: Model used
            stories_processed: Number of stories processed
            cache_ttl: Cache TTL used ("5m" or "1h")
            
        Returns:
            Cost record
        """
        # Extract token counts
        input_tokens = usage_data.get("prompt_tokens", usage_data.get("input_tokens", 0))
        output_tokens = usage_data.get("completion_tokens", usage_data.get("output_tokens", 0))
        cache_write_tokens = usage_data.get("cache_creation_input_tokens", 0)
        cache_read_tokens = usage_data.get("cache_read_input_tokens", 0)
        
        # Calculate costs
        costs = self._calculate_costs(
            provider,
            model,
            input_tokens,
            output_tokens,
            cache_write_tokens,
            cache_read_tokens,
            cache_ttl
        )
        
        # Create cost record
        record = CostRecord(
            timestamp=time.time(),
            operation_id=operation_id,
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_write_tokens=cache_write_tokens,
            cache_read_tokens=cache_read_tokens,
            input_cost=costs["input_cost"],
            output_cost=costs["output_cost"],
            cache_write_cost=costs["cache_write_cost"],
            cache_read_cost=costs["cache_read_cost"],
            provider=provider,
            model=model,
            stories_processed=stories_processed
        )
        
        # Store record
        self.cost_records.append(record)
        
        # Save to file if enabled
        if self.save_to_file:
            self._save_records()
        
        return record
    
    def _calculate_costs(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int,
        cache_read_tokens: int,
        cache_ttl: str = "5m"
    ) -> Dict[str, float]:
        """Calculate costs based on token usage and provider pricing"""
        
        # Get pricing for provider/model
        pricing = self._get_pricing(provider, model)
        if not pricing:
            # Fallback to default pricing
            pricing = {
                "input": 0.003,
                "output": 0.015,
                "cache_write_5m": 0.00375,
                "cache_read": 0.0003
            }
        
        # Calculate costs (convert tokens to thousands)
        input_cost = (input_tokens / 1000) * pricing.get("input", 0)
        output_cost = (output_tokens / 1000) * pricing.get("output", 0)
        
        # Cache costs depend on provider
        if provider == "anthropic":
            # Anthropic has separate pricing for cache writes and reads
            cache_write_key = f"cache_write_{cache_ttl}" if cache_ttl in ["5m", "1h"] else "cache_write_5m"
            cache_write_cost = (cache_write_tokens / 1000) * pricing.get(cache_write_key, pricing.get("input", 0) * 1.25)
            cache_read_cost = (cache_read_tokens / 1000) * pricing.get("cache_read", pricing.get("input", 0) * 0.1)
        else:
            # Other providers use discount model
            cache_discount = pricing.get("cache_discount", 0.75)
            cache_write_cost = 0  # No separate write cost
            cache_read_cost = (cache_read_tokens / 1000) * pricing.get("input", 0) * (1 - cache_discount)
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "cache_write_cost": cache_write_cost,
            "cache_read_cost": cache_read_cost
        }
    
    def _get_pricing(self, provider: str, model: str) -> Optional[Dict[str, float]]:
        """Get pricing for provider and model"""
        
        provider_data = self.provider_pricing.get(provider)
        if not provider_data:
            return None
        
        # Try exact match first
        if model in provider_data:
            return provider_data[model]
        
        # Try partial matches
        for pricing_model, pricing in provider_data.items():
            if pricing_model in model or model in pricing_model:
                return pricing
        
        # Return first available pricing as fallback
        return next(iter(provider_data.values())) if provider_data else None
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get cost summary for a specific day
        
        Args:
            date: Date to summarize (defaults to today)
            
        Returns:
            Daily cost summary
        """
        if date is None:
            date = datetime.now()
        
        # Get records for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        daily_records = [
            record for record in self.cost_records
            if start_of_day.timestamp() <= record.timestamp < end_of_day.timestamp()
        ]
        
        if not daily_records:
            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_cost": 0.0,
                "operations": 0,
                "stories_processed": 0
            }
        
        # Calculate totals
        total_cost = sum(record.total_cost for record in daily_records)
        total_stories = sum(record.stories_processed for record in daily_records)
        
        # Calculate cache efficiency
        total_input_tokens = sum(
            record.input_tokens + record.cache_write_tokens + record.cache_read_tokens
            for record in daily_records
        )
        total_cache_read = sum(record.cache_read_tokens for record in daily_records)
        cache_hit_ratio = total_cache_read / max(total_input_tokens, 1)
        
        # Group by operation type
        by_operation = {}
        for record in daily_records:
            op_type = record.operation_type
            if op_type not in by_operation:
                by_operation[op_type] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "stories": 0
                }
            
            by_operation[op_type]["count"] += 1
            by_operation[op_type]["total_cost"] += record.total_cost
            by_operation[op_type]["stories"] += record.stories_processed
        
        # Calculate savings estimate
        estimated_cost_without_cache = total_cost / (1 - cache_hit_ratio * 0.9) if cache_hit_ratio > 0 else total_cost
        estimated_savings = estimated_cost_without_cache - total_cost
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_cost": total_cost,
            "operations": len(daily_records),
            "stories_processed": total_stories,
            "cost_per_story": total_cost / max(total_stories, 1),
            "cache_performance": {
                "cache_hit_ratio": cache_hit_ratio,
                "total_cache_read_tokens": total_cache_read,
                "estimated_savings": estimated_savings,
                "savings_percentage": (estimated_savings / estimated_cost_without_cache * 100) if estimated_cost_without_cache > 0 else 0
            },
            "by_operation_type": by_operation,
            "cost_breakdown": {
                "input_cost": sum(r.input_cost for r in daily_records),
                "output_cost": sum(r.output_cost for r in daily_records),
                "cache_write_cost": sum(r.cache_write_cost for r in daily_records),
                "cache_read_cost": sum(r.cache_read_cost for r in daily_records)
            }
        }
    
    def get_weekly_trends(self) -> Dict[str, Any]:
        """Get cost trends for the past week"""
        
        daily_summaries = []
        end_date = datetime.now()
        
        for i in range(7):
            date = end_date - timedelta(days=i)
            summary = self.get_daily_summary(date)
            daily_summaries.append(summary)
        
        daily_summaries.reverse()  # Chronological order
        
        # Calculate trends
        costs = [s["total_cost"] for s in daily_summaries if s["total_cost"] > 0]
        stories = [s["stories_processed"] for s in daily_summaries if s["stories_processed"] > 0]
        
        avg_daily_cost = sum(costs) / len(costs) if costs else 0
        avg_cost_per_story = sum(s["cost_per_story"] for s in daily_summaries if s["cost_per_story"] > 0) / max(len(daily_summaries), 1)
        
        # Cache efficiency trend
        cache_ratios = [
            s["cache_performance"]["cache_hit_ratio"]
            for s in daily_summaries
            if s.get("cache_performance", {}).get("cache_hit_ratio", 0) > 0
        ]
        avg_cache_hit_ratio = sum(cache_ratios) / len(cache_ratios) if cache_ratios else 0
        
        return {
            "period": f"{daily_summaries[0]['date']} to {daily_summaries[-1]['date']}",
            "daily_summaries": daily_summaries,
            "trends": {
                "avg_daily_cost": avg_daily_cost,
                "avg_cost_per_story": avg_cost_per_story,
                "avg_cache_hit_ratio": avg_cache_hit_ratio,
                "total_week_cost": sum(costs),
                "total_week_stories": sum(stories)
            },
            "recommendations": self._generate_cost_recommendations(daily_summaries)
        }
    
    def _generate_cost_recommendations(self, daily_summaries: List[Dict[str, Any]]) -> List[str]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        # Check for high costs
        high_cost_days = [s for s in daily_summaries if s["cost_per_story"] > 0.05]
        if high_cost_days:
            recommendations.append(
                f"High cost per story detected on {len(high_cost_days)} days. "
                "Consider optimizing batch sizes or reducing analysis complexity."
            )
        
        # Check cache efficiency
        low_cache_days = [
            s for s in daily_summaries
            if s.get("cache_performance", {}).get("cache_hit_ratio", 1) < 0.5
        ]
        if low_cache_days:
            recommendations.append(
                f"Low cache hit ratio on {len(low_cache_days)} days. "
                "Review prompt structure and conversation design for better caching."
            )
        
        # Check for cost growth
        recent_costs = [s["total_cost"] for s in daily_summaries[-3:] if s["total_cost"] > 0]
        earlier_costs = [s["total_cost"] for s in daily_summaries[:3] if s["total_cost"] > 0]
        
        if len(recent_costs) >= 2 and len(earlier_costs) >= 2:
            recent_avg = sum(recent_costs) / len(recent_costs)
            earlier_avg = sum(earlier_costs) / len(earlier_costs)
            
            if recent_avg > earlier_avg * 1.3:  # 30% increase
                recommendations.append(
                    "Cost trend increasing. Monitor usage patterns and consider optimization strategies."
                )
        
        if not recommendations:
            recommendations.append("Cost management looks good! Current usage patterns are efficient.")
        
        return recommendations
    
    def export_records(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Export cost records for analysis
        
        Args:
            start_date: Start date for export
            end_date: End date for export
            
        Returns:
            List of cost records as dictionaries
        """
        records_to_export = self.cost_records
        
        if start_date:
            records_to_export = [
                r for r in records_to_export
                if r.timestamp >= start_date.timestamp()
            ]
        
        if end_date:
            records_to_export = [
                r for r in records_to_export
                if r.timestamp <= end_date.timestamp()
            ]
        
        return [asdict(record) for record in records_to_export]
    
    def _save_records(self):
        """Save cost records to file"""
        try:
            records_data = [asdict(record) for record in self.cost_records]
            with open(self.file_path, 'w') as f:
                json.dump(records_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cost records to {self.file_path}: {e}")
    
    def _load_records(self):
        """Load cost records from file"""
        try:
            with open(self.file_path, 'r') as f:
                records_data = json.load(f)
            
            self.cost_records = [
                CostRecord(**record_dict) for record_dict in records_data
            ]
        except FileNotFoundError:
            # File doesn't exist yet, start with empty records
            self.cost_records = []
        except Exception as e:
            print(f"Warning: Could not load cost records from {self.file_path}: {e}")
            self.cost_records = []