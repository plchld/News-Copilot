# api/admin.py
# Admin endpoints for user management and analytics

from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Simple admin authentication
ADMIN_KEY = os.getenv('ADMIN_KEY', 'your-admin-secret-key')

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != ADMIN_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/api/admin/users', methods=['GET'])
@require_admin
def list_users():
    """Get all users with stats"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            u.email,
            u.tier,
            u.created_at,
            COUNT(DISTINCT DATE(l.created_at)) as active_days,
            COUNT(l.id) as total_requests,
            SUM(l.cost_usd) as total_cost
        FROM users u
        LEFT JOIN usage_logs l ON u.email = l.user_email
        GROUP BY u.email
        ORDER BY u.created_at DESC
    ''')
    
    users = []
    for row in cursor.fetchall():
        users.append({
            'email': row[0],
            'tier': row[1],
            'created_at': row[2],
            'active_days': row[3] or 0,
            'total_requests': row[4] or 0,
            'total_cost': round(row[5] or 0, 2),
            'avg_daily_requests': round((row[4] or 0) / max(row[3] or 1, 1), 1)
        })
    
    conn.close()
    
    # Calculate summary stats
    total_users = len(users)
    tier_breakdown = {}
    for user in users:
        tier = user['tier']
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
    
    return jsonify({
        'total_users': total_users,
        'tier_breakdown': tier_breakdown,
        'users': users
    })

@admin_bp.route('/api/admin/usage-stats', methods=['GET'])
@require_admin
def usage_stats():
    """Get usage statistics"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Daily usage for last 30 days
    cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(DISTINCT user_email) as unique_users,
            COUNT(id) as requests,
            SUM(cost_usd) as cost
        FROM usage_logs
        WHERE created_at >= date('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''')
    
    daily_stats = []
    for row in cursor.fetchall():
        daily_stats.append({
            'date': row[0],
            'unique_users': row[1],
            'requests': row[2],
            'cost': round(row[3] or 0, 2)
        })
    
    # Get email list for marketing
    cursor.execute('''
        SELECT email, tier, created_at 
        FROM users 
        WHERE tier = 'free'
        ORDER BY created_at DESC
    ''')
    
    free_users = []
    for row in cursor.fetchall():
        free_users.append({
            'email': row[0],
            'tier': row[1],
            'created_at': row[2]
        })
    
    conn.close()
    
    return jsonify({
        'daily_stats': daily_stats,
        'free_users_for_marketing': free_users
    })

@admin_bp.route('/api/admin/export-emails', methods=['GET'])
@require_admin
def export_emails():
    """Export email list for marketing campaigns"""
    tier_filter = request.args.get('tier', 'all')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    if tier_filter == 'all':
        cursor.execute('SELECT email, tier FROM users')
    else:
        cursor.execute('SELECT email, tier FROM users WHERE tier = ?', (tier_filter,))
    
    emails = []
    for row in cursor.fetchall():
        emails.append({
            'email': row[0],
            'tier': row[1]
        })
    
    conn.close()
    
    # Format for CSV export
    csv_data = "email,tier\n"
    for user in emails:
        csv_data += f"{user['email']},{user['tier']}\n"
    
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=users_{tier_filter}.csv'
    }