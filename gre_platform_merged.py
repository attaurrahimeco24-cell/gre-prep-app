import os
import sqlite3
import json
import uuid
import time
import logging
from contextlib import contextmanager
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Sequence

# ==============================================================================
# ============================  CONFIG SECTION  ===============================
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "gre_questions.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

os.makedirs(DATA_DIR, exist_ok=True)

APP_NAME = "GRE AI Prep Platform"
APP_VERSION = "1.0.0"
QUESTION_SOURCE_TAG = "AI-Generated Practice (GRE Engine v1.0)"

SECTION_STRUCTURE = {
    "AW": {"label": "Analytical Writing", "question_count": 1, "time_seconds": 30 * 60, "order": 1, "adaptive": False},
    "VERBAL_1": {"label": "Verbal Reasoning - Section 1", "measure": "Verbal", "question_count": 12, "time_seconds": 18 * 60, "order": 2, "adaptive": False, "determines_next": "VERBAL_2"},
    "VERBAL_2": {"label": "Verbal Reasoning - Section 2", "measure": "Verbal", "question_count": 15, "time_seconds": 23 * 60, "order": 3, "adaptive": True, "determined_by": "VERBAL_1"},
    "QUANT_1": {"label": "Quantitative Reasoning - Section 1", "measure": "Quant", "question_count": 12, "time_seconds": 21 * 60, "order": 4, "adaptive": False, "determines_next": "QUANT_2"},
    "QUANT_2": {"label": "Quantitative Reasoning - Section 2", "measure": "Quant", "question_count": 15, "time_seconds": 26 * 60, "order": 5, "adaptive": True, "determined_by": "QUANT_1"},
}

DIFFICULTY_TIERS = ["easy", "medium", "hard"]
ADAPTIVE_THRESHOLDS = {"hard": 0.75, "medium": 0.40}
SPACED_REPETITION_INTERVALS = [1, 3, 7, 14, 30]
MASTERY_ACCURACY_THRESHOLD = 0.80

MODE_EXAM_SIMULATION = "exam_simulation"
MODE_PRACTICE = "practice"
VALID_MODES = [MODE_EXAM_SIMULATION, MODE_PRACTICE]
ALL_ERROR_CATEGORIES = [
    "Conceptual Deficit", "Calculation Slip", "Misread Question/Constraint", "Formula Misapplication", 
    "Logical Fallacy", "Trap Fall-For", "Time Pressure Rush", "Careless Entry", "Vocabulary Void", 
    "Context Misinterpretation", "Sentence Logic Error", "RC Main Idea Confusion", "RC Inference Stretch", "Distractor Trap"
]

# ==============================================================================
# ============================  SCHEMA SECTION  ===============================
# ==============================================================================
SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS questions (
    question_id             TEXT PRIMARY KEY,
    section                 TEXT NOT NULL CHECK (section IN ('Quantitative Reasoning', 'Verbal Reasoning', 'Analytical Writing')),
    domain                  TEXT NOT NULL,
    topic                   TEXT NOT NULL,
    subtopic                TEXT,
    question_type           TEXT NOT NULL,
    difficulty_level        INTEGER NOT NULL CHECK (difficulty_level BETWEEN 1 AND 5),
    conceptual_depth        INTEGER CHECK (conceptual_depth BETWEEN 1 AND 5),
    calculation_rigor       INTEGER CHECK (calculation_rigor BETWEEN 1 AND 5),
    reading_complexity      INTEGER CHECK (reading_complexity BETWEEN 1 AND 5),
    trap_density             INTEGER CHECK (trap_density BETWEEN 1 AND 5),
    question_text           TEXT NOT NULL,
    options_json            TEXT,
    correct_answer          TEXT NOT NULL,
    explanation              TEXT NOT NULL,
    skill_tested             TEXT,
    estimated_time_seconds   INTEGER NOT NULL DEFAULT 90,
    passage_id               TEXT,
    source                   TEXT NOT NULL DEFAULT 'AI-Generated Practice (GRE Engine v1.0)',
    created_at                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS passages (
    passage_id      TEXT PRIMARY KEY,
    passage_text    TEXT NOT NULL,
    domain          TEXT,
    word_count      INTEGER,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tests (
    test_id             TEXT PRIMARY KEY,
    test_type           TEXT NOT NULL CHECK (test_type IN ('exam_simulation', 'practice')),
    start_timestamp     TIMESTAMP,
    end_timestamp       TIMESTAMP,
    total_score          INTEGER,
    quant_score          INTEGER CHECK (quant_score IS NULL OR quant_score BETWEEN 130 AND 170),
    verbal_score         INTEGER CHECK (verbal_score IS NULL OR verbal_score BETWEEN 130 AND 170),
    aw_score             REAL CHECK (aw_score IS NULL OR (aw_score >= 0.0 AND aw_score <= 6.0)),
    status               TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_sections (
    section_instance_id    TEXT PRIMARY KEY,
    test_id                 TEXT NOT NULL,
    section_key             TEXT NOT NULL,
    difficulty_tier         TEXT CHECK (difficulty_tier IN ('easy', 'medium', 'hard') OR difficulty_tier IS NULL),
    time_allotted_seconds   INTEGER NOT NULL,
    section_start_timestamp REAL,
    section_end_timestamp   REAL,
    status                  TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_responses (
    response_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id               TEXT NOT NULL,
    question_id           TEXT NOT NULL,
    section_instance_id   TEXT,
    user_answer           TEXT,
    correct_answer        TEXT NOT NULL,
    result                TEXT NOT NULL CHECK (result IN ('correct', 'incorrect', 'unanswered')),
    time_spent_seconds    INTEGER NOT NULL DEFAULT 0,
    marked_for_review     INTEGER NOT NULL DEFAULT 0 CHECK (marked_for_review IN (0, 1)),
    timestamp             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE RESTRICT,
    FOREIGN KEY (section_instance_id) REFERENCES session_sections(section_instance_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS error_log (
    error_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id               TEXT NOT NULL,
    test_id                    TEXT,
    response_id                INTEGER,
    error_category             TEXT NOT NULL,
    user_notes                 TEXT,
    repetition_review_due_date DATE,
    resolved                   INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1)),
    created_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE RESTRICT,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE SET NULL,
    FOREIGN KEY (response_id) REFERENCES test_responses(response_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS user_performance (
    user_id                     TEXT NOT NULL DEFAULT 'default_user',
    topic                        TEXT NOT NULL,
    subtopic                     TEXT NOT NULL DEFAULT '',
    total_attempts                INTEGER NOT NULL DEFAULT 0,
    correct_attempts              INTEGER NOT NULL DEFAULT 0,
    accuracy_pct                  REAL NOT NULL DEFAULT 0.0,
    avg_speed_seconds             REAL,
    mastery_rating                TEXT CHECK (mastery_rating IN ('weak', 'developing', 'proficient', 'mastered') OR mastery_rating IS NULL),
    dominant_error_category        TEXT,
    current_repetition_interval    INTEGER DEFAULT 1,
    last_practiced                 TIMESTAMP,
    next_review_due                DATE,
    updated_at                     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

def get_connection() -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 10000;")
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to connect to database at {DATABASE_PATH}: {e}")

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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize_database() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info("Database schema initialized/verified at %s", DATABASE_PATH)
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to initialize schema: {e}")
    finally:
        conn.close()

def verify_schema() -> Dict[str, bool]:
    required_tables = ["questions", "tests", "test_responses", "error_log", "user_performance", "passages", "session_sections"]
    try:
        with db_cursor() as cur:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing = {row["name"] for row in cur.fetchall()}
        return {t: (t in existing) for t in required_tables}
    except DatabaseError as e:
        logger.error("verify_schema() could not query sqlite_master: %s", e)
        return {t: False for t in required_tables}

def _require(value: Any, field_name: str) -> None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise DatabaseError(f"Missing required field: '{field_name}'")

def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"

def insert_question(q: Dict[str, Any]) -> str:
    required_fields = ["question_id", "section", "domain", "topic", "question_type", "difficulty_level", "question_text", "correct_answer", "explanation"]
    for field in required_fields:
        _require(q.get(field), field)
    options_json = json.dumps(q.get("options")) if q.get("options") is not None else None
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(
                """INSERT INTO questions (
                    question_id, section, domain, topic, subtopic, question_type,
                    difficulty_level, conceptual_depth, calculation_rigor, reading_complexity, trap_density, 
                    question_text, options_json, correct_answer, explanation, skill_tested, estimated_time_seconds, passage_id, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    q["question_id"], q["section"], q["domain"], q["topic"], q.get("subtopic"), q["question_type"], int(q["difficulty_level"]),
                    q.get("complexity_factors", {}).get("conceptual_depth"), q.get("complexity_factors", {}).get("calculation_rigor"),
                    q.get("complexity_factors", {}).get("reading_complexity"), q.get("complexity_factors", {}).get("trap_density"),
                    q["question_text"], options_json, q["correct_answer"], q["explanation"], q.get("skill_tested"),
                    int(q.get("estimated_time_seconds", 90)), q.get("passage_id"), q.get("source", QUESTION_SOURCE_TAG),
                ),
            )
    except DatabaseError as e:
        if "UNIQUE constraint failed" in str(e):
            raise DatabaseError(f"Question ID '{q['question_id']}' already exists.")
        raise
    return q["question_id"]

def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    _require(question_id, "question_id")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
        row = cur.fetchone()
    if row is None:
        return None
    result = dict(row)
    result["options"] = json.loads(result["options_json"]) if result["options_json"] else None
    return result

def get_questions_filtered(section: Optional[str] = None, topic: Optional[str] = None, difficulty_levels: Optional[Sequence[int]] = None, question_type: Optional[str] = None, exclude_ids: Optional[Sequence[str]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if limit is not None and limit < 0:
        raise DatabaseError("limit cannot be negative")
    if limit == 0:
        return []
    clauses = []
    params: List[Any] = []
    
    if section:
        clauses.append("section = ?")
        params.append(section)
    if topic:
        clauses.append("topic = ?")
        params.append(topic)
    if question_type:
        clauses.append("question_type = ?")
        params.append(question_type)
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

def count_questions(section: Optional[str] = None) -> int:
    with db_cursor() as cur:
        if section:
            cur.execute("SELECT COUNT(*) as c FROM questions WHERE section = ?", (section,))
        else:
            cur.execute("SELECT COUNT(*) as c FROM questions")
        return cur.fetchone()["c"]

def insert_passage(passage_id: str, passage_text: str, domain: Optional[str] = None) -> str:
    _require(passage_id, "passage_id")
    _require(passage_text, "passage_text")
    word_count = len(passage_text.split())
    with db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO passages (passage_id, passage_text, domain, word_count) VALUES (?, ?, ?, ?)",(passage_id, passage_text, domain, word_count))
    return passage_id

def create_test(test_type: str) -> str:
    if test_type not in VALID_MODES:
        raise DatabaseError(f"Invalid test_type '{test_type}'. Must be one of {VALID_MODES}")
    test_id = _new_id("TEST")
    with db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO tests (test_id, test_type, start_timestamp, status) VALUES (?, ?, ?, 'in_progress')", (test_id, test_type, datetime.now().isoformat()))
    return test_id

def update_test_scores(test_id: str, quant_score: Optional[int] = None, verbal_score: Optional[int] = None, aw_score: Optional[float] = None, total_score: Optional[int] = None) -> None:
    _require(test_id, "test_id")
    ALLOWED_UPDATES = {"quant_score": quant_score, "verbal_score": verbal_score, "aw_score": aw_score, "total_score": total_score}
    fields, params = [], []
    for column, value in ALLOWED_UPDATES.items():
        if value is not None:
            fields.append(f"{column} = ?")
            params.append(value)
    if not fields:
        return
    params.append(test_id)
    with db_cursor(commit=True) as cur:
        cur.execute(f"UPDATE tests SET {', '.join(fields)} WHERE test_id = ?", params)

def complete_test(test_id: str) -> None:
    _require(test_id, "test_id")
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE tests SET status = 'completed', end_timestamp = ? WHERE test_id = ?",(datetime.now().isoformat(), test_id))

def abandon_test(test_id: str) -> None:
    _require(test_id, "test_id")
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE tests SET status = 'abandoned', end_timestamp = ? WHERE test_id = ?", (datetime.now().isoformat(), test_id))

def get_test(test_id: str) -> Optional[Dict[str, Any]]:
    _require(test_id, "test_id")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM tests WHERE test_id = ?", (test_id,))
        row = cur.fetchone()
    return dict(row) if row else None

def get_all_tests(status: Optional[str] = None) -> List[Dict[str, Any]]:
    with db_cursor() as cur:
        if status:
            cur.execute("SELECT * FROM tests WHERE status = ? ORDER BY start_timestamp DESC", (status,))
        else:
            cur.execute("SELECT * FROM tests ORDER BY start_timestamp DESC")
        return [dict(r) for r in cur.fetchall()]

def create_session_section(test_id: str, section_key: str, difficulty_tier: Optional[str] = None) -> str:
    _require(test_id, "test_id")
    _require(section_key, "section_key")
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
    _require(section_instance_id, "section_instance_id")
    start_ts = time.time()
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE session_sections SET status = 'in_progress', section_start_timestamp = ? WHERE section_instance_id = ?", (start_ts, section_instance_id))
    return start_ts

def complete_session_section(section_instance_id: str) -> None:
    _require(section_instance_id, "section_instance_id")
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE session_sections SET status = 'completed', section_end_timestamp = ? WHERE section_instance_id = ?", (time.time(), section_instance_id))

def get_session_section(section_instance_id: str) -> Optional[Dict[str, Any]]:
    _require(section_instance_id, "section_instance_id")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM session_sections WHERE section_instance_id = ?", (section_instance_id,))
        row = cur.fetchone()
    return dict(row) if row else None

def get_sections_for_test(test_id: str) -> List[Dict[str, Any]]:
    _require(test_id, "test_id")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM session_sections WHERE test_id = ? ORDER BY section_instance_id", (test_id,))
        return [dict(r) for r in cur.fetchall()]

def insert_response(test_id: str, question_id: str, correct_answer: str, user_answer: Optional[str], result: str, time_spent_seconds: int, section_instance_id: Optional[str] = None, marked_for_review: bool = False) -> int:
    _require(test_id, "test_id")
    _require(question_id, "question_id")
    _require(correct_answer, "correct_answer")
    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO test_responses (test_id, question_id, section_instance_id, user_answer, correct_answer, result, time_spent_seconds, marked_for_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (test_id, question_id, section_instance_id, user_answer, correct_answer, result, int(time_spent_seconds), int(marked_for_review)),
        )
        return cur.lastrowid

def get_responses_for_test(test_id: str) -> List[Dict[str, Any]]:
    _require(test_id, "test_id")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM test_responses WHERE test_id = ? ORDER BY response_id", (test_id,))
        return [dict(r) for r in cur.fetchall()]

def get_responses_for_section(section_instance_id: str) -> List[Dict[str, Any]]:
    _require(section_instance_id, "section_instance_id")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM test_responses WHERE section_instance_id = ? ORDER BY response_id", (section_instance_id,))
        return [dict(r) for r in cur.fetchall()]

def log_error(question_id: str, error_category: str, test_id: Optional[str] = None, response_id: Optional[int] = None, user_notes: Optional[str] = None, repetition_review_due_date: Optional[str] = None) -> int:
    _require(question_id, "question_id")
    _require(error_category, "error_category")
    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO error_log (question_id, test_id, response_id, error_category, user_notes, repetition_review_due_date)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (question_id, test_id, response_id, error_category, user_notes, repetition_review_due_date),
        )
        return cur.lastrowid

def get_error_log(resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
    with db_cursor() as cur:
        if resolved is None:
            cur.execute("SELECT * FROM error_log ORDER BY created_at DESC")
        else:
            cur.execute("SELECT * FROM error_log WHERE resolved = ? ORDER BY created_at DESC", (int(resolved),))
        return [dict(r) for r in cur.fetchall()]

def mark_error_resolved(error_id: int) -> None:
    with db_cursor(commit=True) as cur:
        cur.execute("UPDATE error_log SET resolved = 1 WHERE error_id = ?", (error_id,))

def upsert_user_performance(topic: str, subtopic: str, correct: bool, time_spent_seconds: int, error_category: Optional[str] = None, user_id: str = "default_user") -> None:
    _require(topic, "topic")
    subtopic = subtopic or ""
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT total_attempts, correct_attempts, avg_speed_seconds FROM user_performance WHERE user_id = ? AND topic = ? AND subtopic = ?", (user_id, topic, subtopic))
        row = cur.fetchone()

        if row is None:
            total_attempts = 1
            correct_attempts = 1 if correct else 0
            avg_speed = float(time_spent_seconds)
            accuracy_pct = (correct_attempts / total_attempts) * 100
            cur.execute(
                """INSERT INTO user_performance (user_id, topic, subtopic, total_attempts, correct_attempts, accuracy_pct, avg_speed_seconds, dominant_error_category, last_practiced, current_repetition_interval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, topic, subtopic, total_attempts, correct_attempts, accuracy_pct, avg_speed, error_category, datetime.now().isoformat(), SPACED_REPETITION_INTERVALS[0]),
            )
        else:
            new_total = row["total_attempts"] + 1
            new_correct = row["correct_attempts"] + (1 if correct else 0)
            new_accuracy = (new_correct / new_total) * 100
            new_avg_speed = ((row["avg_speed_seconds"] or 0.0 * row["total_attempts"]) + time_spent_seconds) / new_total
            mastery = "mastered" if new_accuracy >= 90 else "proficient" if new_accuracy >= 80 else "developing" if new_accuracy >= 50 else "weak"
            cur.execute(
                """UPDATE user_performance SET total_attempts = ?, correct_attempts = ?, accuracy_pct = ?, avg_speed_seconds = ?, mastery_rating = ?, dominant_error_category = COALESCE(?, dominant_error_category), last_practiced = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND topic = ? AND subtopic = ?""",
                (new_total, new_correct, new_accuracy, new_avg_speed, mastery, error_category, datetime.now().isoformat(), user_id, topic, subtopic),
            )

def get_weakness_matrix(user_id: str = "default_user") -> List[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM user_performance WHERE user_id = ? ORDER BY accuracy_pct ASC", (user_id,))
        return [dict(r) for r in cur.fetchall()]

def set_next_review_due(topic: str, subtopic: str, due_date: str, new_interval: int, user_id: str = "default_user") -> None:
    _require(topic, "topic")
    subtopic = subtopic or ""
    with db_cursor(commit=True) as cur:
        cur.execute(
            """UPDATE user_performance SET next_review_due = ?, current_repetition_interval = ? WHERE user_id = ? AND topic = ? AND subtopic = ?""",
            (due_date, new_interval, user_id, topic, subtopic),
        )

def get_due_reviews(as_of_date: Optional[str] = None, user_id: str = "default_user") -> List[Dict[str, Any]]:
    as_of_date = as_of_date or date.today().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """SELECT * FROM user_performance WHERE user_id = ? AND next_review_due IS NOT NULL AND next_review_due <= ? ORDER BY next_review_due ASC""",
            (user_id, as_of_date),
        )
        return [dict(r) for r in cur.fetchall()]

def health_check() -> Dict[str, Any]:
    status = {"db_reachable": False, "schema_ok": False, "question_count": 0, "errors": []}
    try:
        initialize_database()
        status["db_reachable"] = True
    except DatabaseError as e:
        status["errors"].append(str(e))
        return status

    tables = verify_schema()
    status["schema_ok"] = all(tables.values())
    if not status["schema_ok"]:
        missing = [t for t, ok in tables.items() if not ok]
        status["errors"].append(f"Missing tables: {missing}")

    try:
        status["question_count"] = count_questions()
    except DatabaseError as e:
        status["errors"].append(str(e))

    return status
