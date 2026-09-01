import time
import json
import gre_platform_merged as db_manager

def initialize_test_session(user_id: str, test_type: str) -> dict:
    test_id = db_manager._new_id("TST")
    with db_manager.db_transaction() as cur:
        cur.execute("INSERT INTO tests (test_id, user_id, test_type, status) VALUES (?, ?, ?, 'in_progress')",
                    (test_id, user_id, test_type))
                    
        # Initialize Section 1: Quantitative 1
        sec_id = db_manager._new_id("SEC")
        cur.execute("""
            INSERT INTO session_sections (sec_instance_id, test_id, section_name, difficulty_tier, start_epoch, duration_seconds, is_completed)
            VALUES (?, ?, 'Quantitative Section 1', 'medium', ?, 1680, 0)
        """, (sec_id, test_id, time.time()))
        
    return {"test_id": test_id}

def get_active_section_payload(test_id: str) -> dict:
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT * FROM session_sections WHERE test_id = ? AND is_completed = 0 ORDER BY start_epoch ASC LIMIT 1", (test_id,))
        sec = cur.fetchone()
        if not sec: return None
        
        cur.execute("SELECT question_id, question_text, options_json, section, domain, topic, difficulty, svg_payload FROM questions LIMIT 10")
        questions = [dict(row) for row in cur.fetchall()]
        
        return {
            "sec_instance_id": sec["sec_instance_id"],
            "section_name": sec["section_name"],
            "difficulty_tier": sec["difficulty_tier"],
            "start_epoch": sec["start_epoch"],
            "duration_seconds": sec["duration_seconds"],
            "questions": questions
        }
