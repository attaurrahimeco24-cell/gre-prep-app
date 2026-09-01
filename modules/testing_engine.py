import time
import gre_platform_merged as db

def initialize_test_session(user_id: str, test_type: str) -> str:
    test_id = db._generate_secure_id("TST")
    with db.db_transaction() as cur:
        cur.execute("INSERT INTO tests (test_id, user_id, test_type, status) VALUES (?, ?, ?, 'in_progress')",
                    (test_id, user_id, test_type))
                    
        sec_instance_id = db._generate_secure_id("SEC")
        cur.execute("""
            INSERT INTO session_sections (sec_instance_id, test_id, section_name, difficulty_tier, start_epoch, duration_seconds, is_completed)
            VALUES (?, ?, 'Quantitative Section 1', 'medium', ?, 1800, 0)
        """, (sec_instance_id, test_id, time.time()))
    return test_id

def get_safe_active_section_payload(test_id: str) -> dict:
    with db.db_transaction() as cur:
        cur.execute("SELECT * FROM session_sections WHERE test_id = ? AND is_completed = 0 ORDER BY start_epoch ASC LIMIT 1", (test_id,))
        sec = cur.fetchone()
        if not sec:
            return None
        
        # CRITICAL SECURITY RULE: NEVER select correct_answer or explanation here.
        cur.execute("SELECT question_id, section, domain, topic, question_type, difficulty, question_text, options_json, svg_payload FROM questions LIMIT 5")
        questions = [dict(row) for row in cur.fetchall()]
        
        return dict(sec) | {"questions": questions}

def submit_answer_atomically(test_id: str, question_id: str, user_answer: str):
    with db.db_transaction() as cur:
        cur.execute("SELECT correct_answer FROM questions WHERE question_id = ?", (question_id,))
        q = cur.fetchone()
        if not q:
            return
        
        result = "correct" if user_answer == q["correct_answer"] else "incorrect"
        response_id = db._generate_secure_id("RES")
        cur.execute("""
            INSERT OR REPLACE INTO test_responses (response_id, test_id, question_id, user_answer, result)
            VALUES (?, ?, ?, ?, ?)
        """, (response_id, test_id, question_id, user_answer, result))
