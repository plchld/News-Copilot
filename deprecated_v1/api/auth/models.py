"""User models for authentication"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """User model for authenticated requests"""
    id: str
    email: str
    tier: str = 'free'  # free, premium, admin
    api_key: Optional[str] = None
    analyses_this_month: int = 0
    created_at: datetime = None
    
    @property
    def monthly_limit(self) -> int:
        """Get monthly analysis limit based on tier"""
        limits = {
            'free': 10,
            'premium': 50,
            'admin': float('inf')
        }
        return limits.get(self.tier, 10)
    
    @property
    def has_limit_reached(self) -> bool:
        """Check if user has reached monthly limit"""
        if self.tier == 'admin':
            return False
        return self.analyses_this_month >= self.monthly_limit
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'tier': self.tier,
            'analyses_this_month': self.analyses_this_month,
            'monthly_limit': self.monthly_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }