import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import hashlib
import logging
from datetime import datetime
import gre_platform_merged as db_manager

logger = logging.getLogger("email_service")

def generate_secure_token() -> tuple[str, str]:
    """Generates a raw token for the URL and a hashed version for the DB."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    return raw_token, token_hash

def send_verification_email(user_id: str, to_email: str, username: str) -> bool:
    settings = db_manager.get_all_settings()
    
    # 1. Generate Cryptographic Token
    raw_token, token_hash = generate_secure_token()
    
    # 2. Store Hash in DB (expires in 60 mins)
    db_manager.create_verification_token(user_id, token_hash, expires_in_minutes=60)
    
    # 3. Construct Verification URL (Resolves automatically via query parameter)
    # Using relative parameter formatting for Streamlit Cloud compatibility
    verify_url = f"/?verify={raw_token}"
    
    # 4. Construct Premium HTML Email Template
    sender_name = settings.get("smtp_sender_name", "GRE Platform")
    sender_email = settings.get("smtp_user", "noreply@example.com")
    
    html_content = f"""
    <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="background-color: #4F46E5; padding: 32px 24px; text-align: center;">
            <h1 style="color: #FFFFFF; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.02em;">Welcome to {sender_name}</h1>
        </div>
        <div style="padding: 40px 32px; background-color: #FFFFFF; color: #0F172A;">
            <p style="font-size: 16px; margin-top: 0;">Hello <strong>{username}</strong>,</p>
            <p style="font-size: 16px; color: #475569; line-height: 1.6;">
                Thank you for creating your account. Your GRE preparation journey starts here.
                Please verify your email address to activate your account and access the platform.
            </p>
            <div style="text-align: center; margin: 40px 0;">
                <a href="{verify_url}" style="background-color: #4F46E5; color: #FFFFFF; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block;">VERIFY EMAIL ADDRESS</a>
            </div>
            <p style="font-size: 14px; color: #64748B; margin-bottom: 8px;">⏱️ This secure link expires in 60 minutes.</p>
            <p style="font-size: 14px; color: #64748B; margin-top: 0;">If you did not create this account, you can safely ignore this email.</p>
        </div>
        <div style="background-color: #F8FAFC; padding: 20px; text-align: center; border-top: 1px solid #E2E8F0;">
            <p style="font-size: 12px; color: #94A3B8; margin: 0;">&copy; {datetime.now().year} {sender_name}. All rights reserved.</p>
        </div>
    </div>
    """
    
    # 5. Connect to SMTP
    host = settings.get("smtp_host", "")
    port_str = settings.get("smtp_port", "587")
    port = int(port_str) if port_str.isdigit() else 587
    password = settings.get("smtp_password", "")
    
    # FAILSAFE: If SMTP is not yet configured, simulate the email in the backend logs
    if not host or not password:
        logger.warning(f"SMTP NOT CONFIGURED. Simulated email to {to_email}.")
        print(f"\n{'='*70}\n[SIMULATED EMAIL DISPATCH]\nTO: {to_email}\nVERIFICATION URL (Copy this into your browser):\n{verify_url}\n{'='*70}\n")
        return True
        
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Verify your {sender_name} account"
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"SMTP Delivery Failed: {e}")
        return False
