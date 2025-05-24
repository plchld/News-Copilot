# api/models.py
# User and subscription models

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import psycopg2
import psycopg2.extras
import os

# Neon Postgres database URL from Vercel
DATABASE_URL = os.getenv('DATABASE_URL')

# ── Pydantic models for article analysis ──────────────────────────────
class TermExplanation(BaseModel):
    term: str
    explanation: str

class JargonResponse(BaseModel):
    terms: List[TermExplanation]

def get_db_connection():
    """Get database connection"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            tier VARCHAR(50) DEFAULT 'free',
            stripe_customer_id VARCHAR(255),
            stripe_subscription_id VARCHAR(255),
            api_key TEXT,
            email_verified BOOLEAN DEFAULT false,
            is_admin BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Usage logs for analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            analysis_type VARCHAR(50) NOT NULL,
            article_url TEXT,
            tokens_used INTEGER,
            cost_usd DECIMAL(10,4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    
    # Email verifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_verifications (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            token VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT false,
            verified_at TIMESTAMP,
            UNIQUE(email)
        )
    ''')
    
    conn.commit()
    conn.close()

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

def create_user(user: User) -> bool:
    """Create new user in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, tier, api_key)
            VALUES (%s, %s, %s)
        ''', (user.email, user.tier, user.api_key))
        conn.commit()
        conn.close()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        conn.close()
        return False

def get_user(email: str) -> Optional[User]:
    """Get user by email"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(
            email=row['email'],
            tier=row['tier'],
            stripe_customer_id=row['stripe_customer_id'],
            stripe_subscription_id=row['stripe_subscription_id'],
            api_key=row['api_key'],
            created_at=row['created_at']
        )
    return None

def update_user_tier(email: str, tier: str, stripe_info: dict = None) -> bool:
    """Update user's subscription tier"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if stripe_info:
        cursor.execute('''
            UPDATE users 
            SET tier = %s, stripe_customer_id = %s, stripe_subscription_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE email = %s
        ''', (tier, stripe_info.get('customer_id'), stripe_info.get('subscription_id'), email))
    else:
        cursor.execute('''
            UPDATE users 
            SET tier = %s, updated_at = CURRENT_TIMESTAMP
            WHERE email = %s
        ''', (tier, email))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def log_usage(log: UsageLog) -> None:
    """Log API usage for billing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO usage_logs (user_email, analysis_type, article_url, tokens_used, cost_usd)
        VALUES (%s, %s, %s, %s, %s)
    ''', (log.user_email, log.analysis_type, log.article_url, log.tokens_used, log.cost_usd))
    conn.commit()
    conn.close()

def get_monthly_cost(email: str) -> float:
    """Get total cost for current month"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(cost_usd) 
        FROM usage_logs 
        WHERE user_email = %s 
        AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_TIMESTAMP)
    ''', (email,))
    result = cursor.fetchone()
    conn.close()
    return float(result[0]) if result[0] else 0.0

def get_monthly_usage(email: str, analysis_type: str) -> int:
    """Get usage count for current month from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM usage_logs 
        WHERE user_email = %s 
        AND analysis_type = %s
        AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_TIMESTAMP)
    ''', (email, analysis_type))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialize database on import
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization failed: {e}")