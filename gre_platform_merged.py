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

# 1. Global connection pool (persistent across reruns on the Streamlit worker)
_global_conn = None

def get_connection() -> sqlite3.Connection:
    global _global_conn
    if _global_conn is None:
        # check_same_thread=False is REQUIRED for Streamlit's multi-threaded reruns
        _global_conn = sqlite3.connect(DATABASE_PATH, timeout=20, check_same_thread=False)
        _global_conn.row_factory = sqlite3.Row
        _global_conn.execute("PRAGMA foreign_keys = ON;")
        _global_conn.execute("PRAGMA journal_mode = WAL;") # Write-Ahead Logging for concurrency
        _global_conn.execute("PRAGMA synchronous = NORMAL;") # Perf boost for WAL
        _global_conn.execute("PRAGMA temp_store = MEMORY;") # Moves temp tables to RAM
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
        # ONLY close the cursor. Do NOT close the connection.
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
