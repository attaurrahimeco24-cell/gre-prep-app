import datetime
import hashlib
import secrets
import gre_platform_merged as db

def send_verification_email(user_id: str, email: str, username: str) -> dict:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=30)).isoformat()
    
    token_id = db._generate_secure_id("TOK")
    with db.db_transaction() as cur:
        cur.execute(
            "INSERT INTO email_verification_tokens (token_id, user_id, token_hash, expires_at, used) VALUES (?, ?, ?, ?, 0)",
            (token_id, user_id, token_hash, expires_at)
        )
        
    return {
        "status": "simulated",
        "recipient": email,
        "verify_link": f"/?verify={raw_token}"
    }

def verify_email_token(raw_token: str) -> dict:
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    now = datetime.datetime.now()
    
    with db.db_transaction() as cur:
        cur.execute("SELECT * FROM email_verification_tokens WHERE token_hash = ? AND used = 0", (token_hash,))
        token = cur.fetchone()
        if not token:
            return {"status": "invalid"}
            
        if now > datetime.datetime.fromisoformat(token["expires_at"]):
            return {"status": "expired"}
            
        cur.execute("UPDATE email_verification_tokens SET used = 1 WHERE token_id = ?", (token["token_id"],))
        cur.execute("UPDATE users SET is_verified = 1 WHERE user_id = ?", (token["user_id"],))
        return {"status": "valid", "user_id": token["user_id"]}
