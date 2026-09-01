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
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    return raw_token, token_hash

def send_verification_email(user_id: str, to_email: str, username: str) -> dict:
    settings = db_manager.get_all_settings()
    
    raw_token, token_hash = generate_secure_token()
    db_manager.create_verification_token(user_id, token_hash, expires_in_minutes=60)
    
    verify_url = f"/?verify={raw_token}"
    
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
        </div>
    </div>
    """
    
    host = settings.get("smtp_host", "")
    port_str = settings.get("smtp_port", "587")
    port = int(port_str) if port_str.isdigit() else 587
    password = settings.get("smtp_password", "")
    
    # SMART DEV MODE: If SMTP is missing, return the URL to the UI so the user isn't locked out.
    if not host or not password:
        logger.warning(f"SMTP NOT CONFIGURED. Simulated email to {to_email}.")
        return {"status": "simulated", "url": verify_url}
        
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
        return {"status": "sent"}
    except Exception as e:
        logger.error(f"SMTP Delivery Failed: {e}")
        return {"status": "error", "message": str(e)}
