# api/models.py
# User and subscription models

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
import sqlite3
import os

# Simple SQLite database for MVP
DB_PATH = os.getenv('DATABASE_PATH', 'users.db')

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'free',
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            api_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Usage logs for analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            article_url TEXT,
            tokens_used INTEGER,
            cost_usd REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, tier, api_key)
            VALUES (?, ?, ?)
        ''', (user.email, user.tier, user.api_key))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(email: str) -> Optional[User]:
    """Get user by email"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(
            email=row[1],
            tier=row[2],
            stripe_customer_id=row[3],
            stripe_subscription_id=row[4],
            api_key=row[5],
            created_at=row[6]
        )
    return None

def update_user_tier(email: str, tier: str, stripe_info: dict = None) -> bool:
    """Update user's subscription tier"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if stripe_info:
        cursor.execute('''
            UPDATE users 
            SET tier = ?, stripe_customer_id = ?, stripe_subscription_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        ''', (tier, stripe_info.get('customer_id'), stripe_info.get('subscription_id'), email))
    else:
        cursor.execute('''
            UPDATE users 
            SET tier = ?, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
        ''', (tier, email))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def log_usage(log: UsageLog) -> None:
    """Log API usage for billing"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO usage_logs (user_email, analysis_type, article_url, tokens_used, cost_usd)
        VALUES (?, ?, ?, ?, ?)
    ''', (log.user_email, log.analysis_type, log.article_url, log.tokens_used, log.cost_usd))
    conn.commit()
    conn.close()

def get_monthly_cost(email: str) -> float:
    """Get total cost for current month"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(cost_usd) 
        FROM usage_logs 
        WHERE user_email = ? 
        AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
    ''', (email,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result[0] else 0.0

# Initialize database on import
init_db()