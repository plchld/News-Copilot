# api/email_verification.py
# Email verification system with magic links

from flask import Blueprint, request, jsonify, redirect
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from api.models import get_db_connection
import psycopg2.extras

email_bp = Blueprint('email', __name__)

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')  # Your Gmail address
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')  # Your Gmail app password
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USERNAME)
BASE_URL = os.getenv('BASE_URL', 'https://news-copilot.vercel.app')

def send_verification_email(email, verification_token):
    """Send verification email with magic link"""
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("⚠️ Email not configured, verification token:", verification_token)
        return True  # Return success for development
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Επιβεβαίωση λογαριασμού News Copilot"
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        
        # Magic link
        verification_link = f"{BASE_URL}/api/email/verify?token={verification_token}"
        
        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ font-size: 12px; color: #6b7280; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📰 News Copilot</h1>
                    <p>Καλώς ήρθατε στην πλατφόρμα ανάλυσης ειδήσεων</p>
                </div>
                <div class="content">
                    <h2>Επιβεβαίωση Email</h2>
                    <p>Γεια σας,</p>
                    <p>Χρησιμοποιήστε τον παρακάτω σύνδεσμο για να επιβεβαιώσετε το email σας και να ενεργοποιήσετε τον λογαριασμό σας:</p>
                    
                    <a href="{verification_link}" class="button">Επιβεβαίωση Email</a>
                    
                    <p><strong>Τι παίρνετε δωρεάν:</strong></p>
                    <ul>
                        <li>✅ 10 βασικές αναλύσεις ειδήσεων τον μήνα</li>
                        <li>✅ Επεξήγηση τεχνικών όρων</li>
                        <li>✅ Ανάλυση αξιοπιστίας πηγών</li>
                        <li>✅ Εναλλακτικές οπτικές</li>
                    </ul>
                    
                    <p><strong>Χρειάζεστε περισσότερα;</strong></p>
                    <p>Αναβαθμιστείτε στο Pro πλάνο (€8.99/μήνα) για 50 βασικές + 10 εξειδικευμένες αναλύσεις, ή χρησιμοποιήστε το δικό σας Grok API key για απεριόριστη χρήση.</p>
                    
                    <div class="footer">
                        <p>Αν δεν δημιουργήσατε αυτόν τον λογαριασμό, αγνοήστε αυτό το email.</p>
                        <p>Ο σύνδεσμος θα λήξει σε 24 ώρες.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Καλώς ήρθατε στο News Copilot!
        
        Επιβεβαιώστε το email σας: {verification_link}
        
        Δωρεάν πλάνο: 10 αναλύσεις/μήνα
        Pro πλάνο: €8.99/μήνα για 50 βασικές + 10 εξειδικευμένες αναλύσεις
        
        Αν δεν δημιουργήσατε αυτόν τον λογαριασμό, αγνοήστε αυτό το email.
        """
        
        # Attach parts
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False

@email_bp.route('/api/email/verify', methods=['GET'])
def verify_email():
    """Verify email using magic link token"""
    token = request.args.get('token')
    
    if not token:
        return redirect(f"{BASE_URL}/verification-failed.html")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Find pending verification
        cursor.execute('''
            SELECT email, created_at 
            FROM email_verifications 
            WHERE token = %s AND verified = false
        ''', (token,))
        
        verification = cursor.fetchone()
        
        if not verification:
            conn.close()
            return redirect(f"{BASE_URL}/verification-failed.html")
        
        # Check if token expired (24 hours)
        token_age = datetime.now() - verification['created_at']
        if token_age > timedelta(hours=24):
            conn.close()
            return redirect(f"{BASE_URL}/verification-expired.html")
        
        # Mark email as verified
        cursor.execute('''
            UPDATE email_verifications 
            SET verified = true, verified_at = CURRENT_TIMESTAMP 
            WHERE token = %s
        ''', (token,))
        
        # Mark user as verified
        cursor.execute('''
            UPDATE users 
            SET email_verified = true 
            WHERE email = %s
        ''', (verification['email'],))
        
        conn.commit()
        conn.close()
        
        return redirect(f"{BASE_URL}/verification-success.html")
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Email verification error: {e}")
        return redirect(f"{BASE_URL}/verification-failed.html")

def create_verification_token(email):
    """Create email verification token and store in database"""
    token = secrets.token_urlsafe(32)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Store verification token
        cursor.execute('''
            INSERT INTO email_verifications (email, token, created_at, verified)
            VALUES (%s, %s, CURRENT_TIMESTAMP, false)
            ON CONFLICT (email) DO UPDATE SET
                token = EXCLUDED.token,
                created_at = EXCLUDED.created_at,
                verified = false
        ''', (email, token))
        
        conn.commit()
        conn.close()
        
        return token
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Failed to create verification token: {e}")
        return None

def is_email_verified(email):
    """Check if email is verified"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT email_verified FROM users WHERE email = %s
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result and result[0]
        
    except Exception as e:
        conn.close()
        print(f"Failed to check email verification: {e}")
        return False