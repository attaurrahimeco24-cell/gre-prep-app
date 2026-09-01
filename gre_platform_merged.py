import os
import sqlite3
import secrets
import datetime
from contextlib import contextmanager
import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "gre_platform_enterprise.db")
ph = PasswordHasher()

@st.cache_resource
def _initialize_storage_directory():
    os.makedirs(DB_DIR, exist_ok=True)
    return True

def get_db_connection():
    _initialize_storage_directory()
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

@contextmanager
def db_transaction():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise DatabaseException(f"Atomic transaction failed: {e}") from e
    finally:
        conn.close()

class DatabaseException(Exception):
    pass

def _generate_secure_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"

def initialize_database():
    with db_transaction() as cur:
        # Users Table with RBAC and Brute-Force Lockout
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'STUDENT',
            is_verified INTEGER DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Email Verification Tokens
        cur.execute("""
        CREATE TABLE IF NOT EXISTS email_verification_tokens (
            token_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        # Question Bank Schema
        cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            question_id TEXT PRIMARY KEY,
            section TEXT NOT NULL,
            domain TEXT NOT NULL,
            topic TEXT NOT NULL,
            question_type TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT NOT NULL,
            svg_payload TEXT DEFAULT NULL,
            status TEXT DEFAULT 'APPROVED'
        );
        """)

        # Tests & Sessions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            test_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            test_type TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS session_sections (
            sec_instance_id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            section_name TEXT NOT NULL,
            difficulty_tier TEXT DEFAULT 'medium',
            start_epoch REAL NOT NULL,
            duration_seconds INTEGER NOT NULL,
            is_completed INTEGER DEFAULT 0,
            FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS test_responses (
            response_id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            user_answer TEXT,
            result TEXT,
            time_spent_seconds INTEGER DEFAULT 0,
            FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(question_id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit_logs (
            log_id TEXT PRIMARY KEY,
            admin_id TEXT NOT NULL,
            action TEXT NOT NULL,
            target_object TEXT,
            new_value TEXT,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(user_id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        );
        """)

        cur.execute("SELECT COUNT(*) as c FROM system_settings")
        if cur.fetchone()["c"] == 0:
            defaults = [
                ("quant_time_mins", "47"),
                ("verbal_time_mins", "41"),
                ("adaptive_threshold_hard", "0.75"),
                ("adaptive_threshold_medium", "0.40")
            ]
            cur.executemany("INSERT OR REPLACE INTO system_settings (setting_key, setting_value) VALUES (?, ?)", defaults)

def create_user_account(username: str, email: str, password_plain: str, role: str = "STUDENT", is_verified: int = 0) -> str:
    user_id = _generate_secure_id("USR")
    hashed = ph.hash(password_plain)
    with db_transaction() as cur:
        cur.execute(
            "INSERT INTO users (user_id, username, email, password_hash, role, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, email, hashed, role, is_verified)
        )
    return user_id

def verify_login_credentials(username_or_email: str, password_plain: str):
    now = datetime.datetime.now()
    with db_transaction() as cur:
        cur.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username_or_email, username_or_email))
        user = cur.fetchone()
        if not user:
            return None

        if user["locked_until"] and now < datetime.datetime.fromisoformat(user["locked_until"]):
            raise ValueError("🔒 Account temporarily locked due to repeated authentication failures. Please try again in 15 minutes.")

        try:
            ph.verify(user["password_hash"], password_plain)
            if ph.check_needs_rehash(user["password_hash"]):
                new_hash = ph.hash(password_plain)
                cur.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user["user_id"]))
            
            cur.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE user_id = ?", (user["user_id"],))
            return dict(user)
        except VerifyMismatchError:
            attempts = user["failed_login_attempts"] + 1
            lock_timestamp = (now + datetime.timedelta(minutes=15)).isoformat() if attempts >= 5 else None
            cur.execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE user_id = ?", (attempts, lock_timestamp, user["user_id"]))
            if lock_timestamp:
                raise ValueError("🔒 Security Limit Reached: Account locked for 15 minutes following 5 consecutive failed login attempts.")
            return None

def log_admin_action(admin_id: str, action: str, target_object: str, new_value: str, reason: str):
    with db_transaction() as cur:
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (admin_id,))
        if cur.fetchone():
            log_id = _generate_secure_id("LOG")
            cur.execute(
                "INSERT INTO admin_audit_logs (log_id, admin_id, action, target_object, new_value, reason) VALUES (?, ?, ?, ?, ?, ?)",
                (log_id, admin_id, action, target_object, new_value, reason)
            )
