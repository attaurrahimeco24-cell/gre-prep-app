import os
import sqlite3
import json
import uuid
import time
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any, Sequence

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
QUESTION_SOURCE_TAG = "AI-Generated Practice (GRE Engine v1.0)"

# ==============================================================================
# ============================  SCHEMA SECTION  ===============================
# ==============================================================================
SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

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

CREATE TABLE IF NOT EXISTS error_log (
    error_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    error_category TEXT NOT NULL,
    user_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_performance (
    user_id TEXT NOT NULL DEFAULT 'default_user',
    topic TEXT NOT NULL,
    subtopic TEXT NOT NULL DEFAULT '',
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    accuracy_pct REAL NOT NULL DEFAULT 0.0,
    avg_speed_seconds REAL,
    mastery_rating TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, topic, subtopic)
);
"""

# ==============================================================================
# ==========================  DB MANAGER SECTION  =============================
# ==============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_manager")

class DatabaseError(Exception):
    pass

# Global connection pool (persistent across reruns on the Streamlit worker)
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
        _global_conn.execute("PRAGMA busy_timeout = 10000;")
    return _global_conn

@contextmanager
def db_cursor(commit: bool = False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
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
        raise DatabaseError(f"Transaction failed and was rolled back: {e}") from e
    finally:
        cur.close()

def initialize_database() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to initialize schema: {e}")

def verify_schema() -> Dict[str, bool]:
    required_tables = ["questions", "tests", "test_responses", "error_log", "user_performance", "session_sections"]
    try:
        with db_cursor() as cur:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing = {row["name"] for row in cur.fetchall()}
        return {t: (t in existing) for t in required_tables}
    except DatabaseError:
        return {t: False for t in required_tables}

def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"

def insert_question(q: Dict[str, Any]) -> str:
    options_json = json.dumps(q.get("options")) if q.get("options") is not None else None
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(
                """INSERT INTO questions (
                    question_id, section, domain, topic, subtopic, question_type,
                    difficulty_level, question_text, options_json, correct_answer, explanation, estimated_time_seconds, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    q["question_id"], q["section"], q["domain"], q["topic"], q.get("subtopic"), q["question_type"], int(q["difficulty_level"]),
                    q["question_text"], options_json, q["correct_answer"], q["explanation"], int(q.get("estimated_time_seconds", 90)), q.get("source", QUESTION_SOURCE_TAG)
                )
            )
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e):
            raise DatabaseError(f"Question ID '{q['question_id']}' already exists.")
        raise
    return q["question_id"]

def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
        row = cur.fetchone()
    if row is None:
        return None
    result = dict(row)
    result["options"] = json.loads(result["options_json"]) if result["options_json"] else None
    return result

def get_questions_filtered(section: Optional[str] = None, difficulty_levels: Optional[Sequence[int]] = None, exclude_ids: Optional[Sequence[str]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if limit == 0: return []
    clauses = []
    params = []
    if section:
        clauses.append("section = ?")
        params.append(section)
    if difficulty_levels:
        placeholders = ",".join("?" * len(difficulty_levels))
        clauses.append(f"difficulty_level IN ({placeholders})")
        params.extend(difficulty_levels)
    if exclude_ids:
        placeholders = ",".join("?" * len(exclude_ids))
        clauses.append(f"question_id NOT IN ({placeholders})")
        params.extend(exclude_ids)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM questions {where_sql} ORDER BY RANDOM()"
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

def count_questions() -> int:
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM questions")
        return cur.fetchone()["c"]

def create_test(test_type: str) -> str:
    test_id = _new_id("TEST")
    with db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO tests (test_id, test_type, start_timestamp, status) VALUES (?, ?, ?, 'in_progress')", (test_id, test_type, datetime.now().isoformat()))
    return test_id

def create_session_section(test_id: str, section_key: str, difficulty_tier: Optional[str] = None) -> str:
    section_instance_id = _new_id("SEC")
    time_allotted = SECTION_STRUCTURE[section_key]["time_seconds"]
    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO session_sections (section_instance_id, test_id, section_key, difficulty_tier, time_allotted_seconds, status)
            VALUES (?, ?, ?, ?, ?, 'pending')""",
            (section_instance_id, test_id, section_key, difficulty_tier, time_allotted),
        )
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

def health_check() -> Dict[str, Any]:
    status = {"db_reachable": False, "schema_ok": False, "question_count": 0, "errors": []}
    try:
        initialize_database()
        status["db_reachable"] = True
        tables = verify_schema()
        status["schema_ok"] = all(tables.values())
        status["question_count"] = count_questions()
    except Exception as e:
        status["errors"].append(str(e))
    return status
