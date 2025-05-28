# api/models.py
# Pydantic models for article analysis and user management

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

# ── Pydantic models for article analysis ──────────────────────────────
class TermExplanation(BaseModel):
    term: str
    explanation: str

class JargonResponse(BaseModel):
    terms: List[TermExplanation]

# ── Request models ──────────────────────────────────
class AnalysisRequest(BaseModel):
    """Request for article analysis"""
    url: str
    analysis_type: str
    article_text: Optional[str] = None
    user_id: Optional[str] = None
    user_tier: str = 'free'

# ── User models (for Supabase) ──────────────────────────────
class User(BaseModel):
    email: EmailStr
    tier: str = 'free'
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    api_key: Optional[str] = None
    created_at: Optional[datetime] = None
    
class UsageLog(BaseModel):
    user_email: EmailStr
    analysis_type: str
    article_url: str
    tokens_used: int
    cost_usd: float