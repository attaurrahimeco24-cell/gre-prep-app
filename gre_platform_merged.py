import os
import sqlite3
import json
import uuid
import time
import logging
import hashlib
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Sequence

# 🔒 PHASE 5: Argon2id Cryptographic Engine Initialization
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    ph = PasswordHasher()
except ImportError:
    ph = None
    logging.warning("argon2-cffi not found. Falling back to PBKDF2. Please update requirements.txt.")

# ==============================================================================
# ============================  CONFIG SECTION  ===============================
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "gre_questions.db")

os.makedirs(DATA_DIR, exist_ok=True)

SECTION_STRUCTURE = {
    "AW": {"label": "Analytical Writing", "question_count": 1, "time_seconds": 30 * 60, "order": 1, "adaptive": False},
    "VERBAL_1": {"label": "Verbal Reasoning - Section 1", "measure": "Verbal", "question_count": 12, "time_seconds": 18 * 60, "order": 2, "adaptive": False, "determines_next": "VERBAL_2"},
    "VERBAL_2": {"label": "Verbal Reasoning - Section 2", "measure": "Verbal", "question_count": 15, "time_seconds": 23 * 60, "order": 3, "adaptive": True, "determined_by": "VERBAL_1"},
    "QUANT_1": {"label": "Quantitative Reasoning - Section 1", "measure": "Quant", "question_count": 12, "time_seconds": 21 * 60, "order": 4, "adaptive": False, "determines_next": "QUANT_2"},
    "QUANT_2": {"label": "Quantitative Reasoning - Section 2", "measure": "Quant", "question_count": 15, "time_seconds": 26 * 60, "order": 5, "adaptive": True, "determined_by": "QUANT_1"},
}

ADAPTIVE_THRESHOLDS = {"hard": 0.75, "medium": 0.40}
VALID_MODES = ["exam_simulation", "practice"]
QUESTION_SOURCE_TAG = "AI-Generated Practice (GRE Engine v2.0)"

# ==============================================================================
# ============================  SCHEMA SECTION  ===============================
# ==============================================================================
SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    salt BLOB NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('STUDENT', 'ADMIN', 'SUPER_ADMIN')),
    is_active INTEGER NOT NULL DEFAULT 1,
    is_verified INTEGER NOT NULL DEFAULT 0,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    token_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS questions (
    question_id TEXT PRIMARY KEY,
    section TEXT NOT NULL,
    domain TEXT NOT NULL,
    topic TEXT NOT NULL,
    subtopic TEXT,
    question_type TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    options_json TEXT,
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    estimated_time_seconds INTEGER NOT NULL DEFAULT 90,
    source TEXT NOT NULL DEFAULT 'AI-Generated Practice',
    status TEXT NOT NULL DEFAULT 'APPROVED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tests (
    test_id TEXT PRIMARY KEY,
    test_type TEXT NOT NULL,
    start_timestamp TIMESTAMP,
    end_timestamp TIMESTAMP,
    total_score INTEGER,
    quant_score INTEGER,
    verbal_score INTEGER,
    status TEXT NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_sections (
    section_instance_id TEXT PRIMARY KEY,
    test_id TEXT NOT NULL,
    section_key TEXT NOT NULL,
    difficulty_tier TEXT,
    time_allotted_seconds INTEGER NOT NULL,
    section_start_timestamp REAL,
    section_end_timestamp REAL,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_responses (
    response_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    section_instance_id TEXT,
    user_answer TEXT,
    correct_answer TEXT NOT NULL,
    result TEXT NOT NULL,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    log_id TEXT PRIMARY KEY,
    admin_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_object TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS system_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

# ==============================================================================
# ==========================  DB MANAGER SECTION  =============================
# ==============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_manager")

class DatabaseError(Exception): pass

_global_conn = None

def get_connection() -> sqlite3.Connection:
    global _global_conn
    if _global_conn is None:
        _global_conn = sqlite3.connect(DATABASE_PATH, timeout=20, check_same_thread=False)
        _global_conn.row_factory = sqlite3.Row
        _global_conn.execute("PRAGMA foreign_keys = ON;")
        _global_conn.execute("PRAGMA journal_mode = WAL;") 
        _global_conn.execute("PRAGMA synchronous = NORMAL;") 
        _global_conn.execute("PRAGMA temp_store = MEMORY;") 
    return _global_conn

@contextmanager
def db_cursor(commit: bool = False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        if commit: conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Database operation failed: {e}") from e
    finally:
        cur.close() 

@contextmanager
def db_transaction():
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Transaction failed: {e}") from e
    finally:
        cur.close()

def safe_migrations():
    with db_transaction() as cur:
        cur.execute("PRAGMA table_info(users);")
        u_cols = [row["name"] for row in cur.fetchall()]
        if "is_verified" not in u_cols:
            cur.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0;")
        if "failed_login_attempts" not in u_cols:
            cur.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;")
        if "locked_until" not in u_cols:
            cur.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;")

def seed_default_settings():
    defaults = {
        "quant_time_mins": "47", "verbal_time_mins": "41", "aw_time_mins": "30",
        "adaptive_threshold_hard": "0.75", "adaptive_threshold_medium": "0.40",
        "smtp_host": "", "smtp_port": "587",
        "smtp_user": "", "smtp_password": "",
        "smtp_sender_name": "GRE Platform", "require_email_verification": "true"
    }
    try:
        with db_transaction() as cur:
            cur.execute("SELECT COUNT(*) as c FROM system_settings")
            if cur.fetchone()["c"] == 0:
                for k, v in defaults.items():
                    cur.execute("INSERT INTO system_settings (setting_key, setting_value, updated_by) VALUES (?, ?, 'SYSTEM')", (k, v))
    except DatabaseError:
        pass 

def sync_settings_to_globals():
    try:
        with db_cursor() as cur:
            cur.execute("SELECT setting_key, setting_value FROM system_settings")
            rows = cur.fetchall()
        settings = {r["setting_key"]: r["setting_value"] for r in rows}
        if "adaptive_threshold_hard" in settings: ADAPTIVE_THRESHOLDS["hard"] = float(settings["adaptive_threshold_hard"])
        if "adaptive_threshold_medium" in settings: ADAPTIVE_THRESHOLDS["medium"] = float(settings["adaptive_threshold_medium"])
    except DatabaseError:
        pass

def get_all_settings() -> Dict[str, str]:
    with db_cursor() as cur:
        cur.execute("SELECT setting_key, setting_value FROM system_settings")
        return {r["setting_key"]: r["setting_value"] for r in cur.fetchall()}

def update_settings(updates: Dict[str, str], admin_id: str, reason: str):
    with db_transaction() as cur:
        for k, v in updates.items():
            cur.execute("""
                INSERT INTO system_settings (setting_key, setting_value, updated_by, updated_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value, updated_by = excluded.updated_by
            """, (k, v, admin_id))
    sync_settings_to_globals()

def initialize_database() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        safe_migrations()
        seed_default_settings()
        sync_settings_to_globals()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to initialize schema: {e}")

def _new_id(prefix: str) -> str: return f"{prefix}-{uuid.uuid4().hex[:12]}"

# ==============================================================================
# ====================  AUTH & VERIFICATION MODULE  ============================
# ==============================================================================
def hash_legacy_pbkdf2(password: str, salt: bytes) -> tuple[bytes, bytes]:
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash, salt

def hash_password_current(password: str) -> tuple[bytes, bytes]:
    if ph:
        return ph.hash(password).encode('utf-8'), b'argon2'
    return hash_legacy_pbkdf2(password, secrets.token_bytes(16))

def create_user(username: str, email: str, password: str, role: str = "STUDENT", is_verified: int = 0) -> str:
    if role == "SUPER_ADMIN": is_verified = 1
    user_id = _new_id("USR")
    pwd_hash, salt = hash_password_current(password)
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO users (user_id, username, email, password_hash, salt, role, is_verified) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                (user_id, username, email, pwd_hash, salt, role, is_verified)
            )
        return user_id
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e): raise ValueError("Username or email already exists.")
        raise e

def verify_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Strict login verifier with Brute-Force Rate Limiting & Seamless Argon2 Upgrades."""
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT user_id, username, role, password_hash, salt, is_active, is_verified, failed_login_attempts, locked_until FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        
        if not user or not user["is_active"]: return None
        
        # 1. Check Brute-Force Lockout Status
        if user["locked_until"]:
            if datetime.now().isoformat() < user["locked_until"]:
                raise ValueError("🔒 Account locked due to multiple failed login attempts. Please try again in 15 minutes.")
            else:
                cur.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE user_id = ?", (user["user_id"],))

        stored_hash = user["password_hash"]
        is_valid = False
        needs_upgrade = False
        
        # 2. Cryptographic Validation
        if ph and stored_hash.startswith(b'$argon2'):
            try:
                ph.verify(stored_hash.decode('utf-8'), password)
                is_valid = True
                if ph.check_needs_rehash(stored_hash.decode('utf-8')): needs_upgrade = True
            except VerifyMismatchError:
                is_valid = False
        else:
            # PBKDF2 Legacy Verification
            test_hash, _ = hash_legacy_pbkdf2(password, user["salt"])
            if test_hash == stored_hash:
                is_valid = True
                needs_upgrade = True # Old PBKDF2 users will be silently upgraded to Argon2

        # 3. Handle Result & Execute Rolling Upgrade
        if is_valid:
            cur.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE user_id = ?", (user["user_id"],))
            if needs_upgrade and ph:
                new_hash = ph.hash(password).encode('utf-8')
                cur.execute("UPDATE users SET password_hash = ?, salt = ? WHERE user_id = ?", (new_hash, b'argon2', user["user_id"]))
                logger.info(f"User {user['user_id']} seamlessly upgraded to Argon2id security.")
            
            return {"user_id": user["user_id"], "username": user["username"], "role": user["role"], "is_verified": bool(user["is_verified"])}
        else:
            # Increment Failure Counter
            attempts = user["failed_login_attempts"] + 1
            lock_time = None
            if attempts >= 5:
                lock_time = (datetime.now() + timedelta(minutes=15)).isoformat()
            cur.execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE user_id = ?", (attempts, lock_time, user["user_id"]))
            return None

def get_all_users() -> List[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute("SELECT user_id, username, email, role, is_active, is_verified, created_at FROM users ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]

def update_user_access(target_user_id: str, new_role: str, is_active: int, admin_id: str, reason: str):
    with db_transaction() as cur:
        cur.execute("UPDATE users SET role = ?, is_active = ? WHERE user_id = ?", (new_role, is_active, target_user_id))
        
def manually_verify_user(target_user_id: str, admin_id: str, reason: str):
    with db_transaction() as cur:
        cur.execute("UPDATE users SET is_verified = 1 WHERE user_id = ?", (target_user_id,))
        log_id = _new_id("LOG")
        cur.execute("INSERT INTO admin_audit_logs (log_id, admin_id, action, target_object, old_value, new_value, reason) VALUES (?, ?, ?, ?, ?, ?, ?)", (log_id, admin_id, "MANUAL_VERIFY", target_user_id, "0", "1", reason))

def create_verification_token(user_id: str, token_hash: str, expires_in_minutes: int = 60) -> None:
    expires_at = (datetime.now() + timedelta(minutes=expires_in_minutes)).isoformat()
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE email_verification_tokens SET used_at = CURRENT_TIMESTAMP WHERE user_id = ? AND used_at IS NULL", (user_id,))
        token_id = _new_id("TOK")
        cur.execute("INSERT INTO email_verification_tokens (token_id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)", (token_id, user_id, token_hash, expires_at))

def verify_and_use_token(token_hash: str) -> Dict[str, Any]:
    with db_transaction() as cur:
        cur.execute("SELECT token_id, user_id, expires_at, used_at FROM email_verification_tokens WHERE token_hash = ?", (token_hash,))
        row = cur.fetchone()
        
        if not row: return {"status": "invalid"}
        if row["used_at"] is not None: return {"status": "used"}
        if datetime.now().isoformat() > row["expires_at"]: return {"status": "expired"}
        
        cur.execute("UPDATE email_verification_tokens SET used_at = CURRENT_TIMESTAMP WHERE token_id = ?", (row["token_id"],))
        cur.execute("UPDATE users SET is_verified = 1 WHERE user_id = ?", (row["user_id"],))
        return {"status": "valid", "user_id": row["user_id"]}

def check_verification_cooldown(user_id: str, cooldown_seconds: int = 45) -> bool:
    with db_cursor() as cur:
        cur.execute("SELECT created_at FROM email_verification_tokens WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        if not row: return True
        last_created_str = row["created_at"]
        
        if "." in last_created_str: last_created = datetime.strptime(last_created_str, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            try: last_created = datetime.strptime(last_created_str, "%Y-%m-%d %H:%M:%S")
            except ValueError: return True 
                
        if (datetime.now() - last_created).total_seconds() < cooldown_seconds: return False
        return True

# --- ADMIN AUDIT MODULE ---
def log_admin_action(admin_id: str, action: str, target_object: str, old_val: str = None, new_val: str = None, reason: str = None):
    log_id = _new_id("LOG")
    with db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO admin_audit_logs (log_id, admin_id, action, target_object, old_value, new_value, reason) VALUES (?, ?, ?, ?, ?, ?, ?)", (log_id, admin_id, action, target_object, old_val, new_val, reason))

def get_audit_logs(limit: int = 200) -> List[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute("SELECT l.timestamp, u.username as admin_username, l.action, l.target_object, l.reason FROM admin_audit_logs l LEFT JOIN users u ON l.admin_id = u.user_id ORDER BY l.timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

# --- QUESTION MODULE ---
def insert_question(q: Dict[str, Any]) -> str:
    options_json = json.dumps(q.get("options")) if q.get("options") is not None else None
    try:
        with db_cursor(commit=True) as cur:
            cur.execute("""INSERT INTO questions (question_id, section, domain, topic, question_type, difficulty_level, question_text, options_json, correct_answer, explanation, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (q["question_id"], q["section"], q["domain"], q["topic"], q["question_type"], int(q["difficulty_level"]), q["question_text"], options_json, q["correct_answer"], q["explanation"], q.get("status", "APPROVED")))
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e): raise DatabaseError(f"Question ID '{q['question_id']}' already exists.")
        raise e
    return q["question_id"]

def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
        row = cur.fetchone()
    if row is None: return None
    result = dict(row)
    result["options"] = json.loads(result["options_json"]) if result["options_json"] else None
    return result

def get_questions_filtered(section: Optional[str] = None, difficulty_levels: Optional[Sequence[int]] = None, exclude_ids: Optional[Sequence[str]] = None, limit: Optional[int] = None, status: str = 'APPROVED') -> List[Dict[str, Any]]:
    if limit == 0: return []
    clauses, params = ["status = ?"], [status]
    if section:
        clauses.append("section = ?")
        params.append(section)
    if difficulty_levels:
        clauses.append(f"difficulty_level IN ({','.join('?'*len(difficulty_levels))})")
        params.extend(difficulty_levels)
    if exclude_ids:
        clauses.append(f"question_id NOT IN ({','.join('?'*len(exclude_ids))})")
        params.extend(exclude_ids)

    query = f"SELECT * FROM questions WHERE {' AND '.join(clauses)} ORDER BY RANDOM()"
    if limit is not None:
        query += " LIMIT ?"
        params.append(int(limit))

    with db_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    results = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options_json"]) if d["options_json"] else None
        results.append(d)
    return results

def get_all_questions_admin(section_filter: str = "All", status_filter: str = "All") -> List[Dict[str, Any]]:
    query, params = "SELECT * FROM questions WHERE 1=1", []
    if section_filter != "All":
        query += " AND section = ?"
        params.append(section_filter)
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY created_at DESC"
    
    with db_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        
    results = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options_json"]) if d["options_json"] else None
        results.append(d)
    return results

def count_questions() -> int:
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM questions WHERE status = 'APPROVED'")
        return cur.fetchone()["c"]

# ==============================================================================
# ====================  CBT TEST ENGINE MODULE  ================================
# ==============================================================================
def create_test(test_type: str) -> str:
    test_id = _new_id("TEST")
    with db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO tests (test_id, test_type, start_timestamp, status) VALUES (?, ?, ?, 'in_progress')", (test_id, test_type, datetime.now().isoformat()))
    return test_id

def create_session_section(test_id: str, section_key: str, difficulty_tier: Optional[str] = None) -> str:
    section_instance_id = _new_id("SEC")
    time_allotted = SECTION_STRUCTURE[section_key]["time_seconds"]
    with db_cursor(commit=True) as cur:
        cur.execute("""INSERT INTO session_sections (section_instance_id, test_id, section_key, difficulty_tier, time_allotted_seconds, status) VALUES (?, ?, ?, ?, ?, 'pending')""", (section_instance_id, test_id, section_key, difficulty_tier, time_allotted))
    return section_instance_id

def start_session_section(section_instance_id: str) -> float:
    start_ts = time.time()
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE session_sections SET status = 'in_progress', section_start_timestamp = ? WHERE section_instance_id = ?", (start_ts, section_instance_id))
    return start_ts

def complete_session_section(section_instance_id: str) -> None:
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE session_sections SET status = 'completed', section_end_timestamp = ? WHERE section_instance_id = ?", (time.time(), section_instance_id))

def complete_test(test_id: str) -> None:
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE tests SET status = 'completed', end_timestamp = ? WHERE test_id = ?", (datetime.now().isoformat(), test_id))
