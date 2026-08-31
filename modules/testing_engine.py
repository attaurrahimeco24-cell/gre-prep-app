import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import gre_platform_merged as config
import gre_platform_merged as db_manager
from modules import question_engine, timer

logger = logging.getLogger("GRE_PLATFORM.testing_engine")

class TestingEngineError(Exception):
    pass

def initialize_test_session(test_type: str, mode: str = "exam_simulation") -> Dict[str, Any]:
    if test_type not in config.VALID_MODES and test_type != "full_length":
        target_sections = [test_type]
    elif test_type == "full_length":
        target_sections = ["AW", "VERBAL_1", "VERBAL_2", "QUANT_1", "QUANT_2"]
    
    test_id = db_manager.create_test(test_type=mode)
    
    return {
        "test_id": test_id,
        "test_type": test_type,
        "mode": mode,
        "sections": target_sections,
        "active_section_index": 0,
    }

def get_active_section_info(test_id: str) -> Optional[Dict[str, Any]]:
    with db_manager.db_cursor() as cur:
        cur.execute(
            "SELECT * FROM session_sections WHERE test_id = ? AND status IN ('pending', 'in_progress') ORDER BY section_instance_id ASC LIMIT 1",
            (test_id,)
        )
        row = cur.fetchone()
    if not row:
        return None
    return dict(row)

def start_active_section(section_instance_id: str) -> Dict[str, Any]:
    start_ts = timer.start_section_timer(section_instance_id)
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT * FROM session_sections WHERE section_instance_id = ?", (section_instance_id,))
        sec_row = cur.fetchone()
        
    sec_name = sec_row["section_key"]
    difficulty_baseline = 3 
    
    if "VERBAL" in sec_name:
        sec_type = "Verbal Reasoning"
        target_count = config.SECTION_STRUCTURE["VERBAL_1"]["question_count"] if "1" in sec_name else config.SECTION_STRUCTURE["VERBAL_2"]["question_count"]
        duration = config.SECTION_STRUCTURE["VERBAL_1"]["time_seconds"] if "1" in sec_name else config.SECTION_STRUCTURE["VERBAL_2"]["time_seconds"]
    elif "QUANT" in sec_name:
        sec_type = "Quantitative Reasoning"
        target_count = config.SECTION_STRUCTURE["QUANT_1"]["question_count"] if "1" in sec_name else config.SECTION_STRUCTURE["QUANT_2"]["question_count"]
        duration = config.SECTION_STRUCTURE["QUANT_1"]["time_seconds"] if "1" in sec_name else config.SECTION_STRUCTURE["QUANT_2"]["time_seconds"]
    else:
        sec_type = "Analytical Writing"
        target_count = 1
        duration = config.SECTION_STRUCTURE["AW"]["time_seconds"]

    if sec_row["difficulty_tier"] == "easy":
        difficulty_baseline = 2
    elif sec_row["difficulty_tier"] == "hard":
        difficulty_baseline = 4

    raw_questions = question_engine.build_section_question_set(
        section_name=sec_type,
        target_count=target_count,
        difficulty_baseline=difficulty_baseline,
    )

    sanitized_questions = []
    for q in raw_questions:
        q_copy = dict(q)
        q_copy.pop("correct_answer", None)
        q_copy.pop("explanation", None)
        sanitized_questions.append(q_copy)

    return {
        "section_instance_id": section_instance_id,
        "section_name": sec_name,
        "start_timestamp": start_ts,
        "duration_seconds": duration,
        "questions": sanitized_questions,
    }

def submit_answer_atomically(test_id: str, section_instance_id: str, question_id: str, user_answer: Optional[str], time_spent_seconds: int) -> bool:
    question = question_engine.fetch_question(question_id)
    if not question:
        raise TestingEngineError(f"Question ID {question_id} not found.")
        
    correct_ans = question["correct_answer"]
    topic = question.get("topic", "General")
    q_type = question.get("question_type")
    
    is_correct = False
    if user_answer is not None and user_answer.strip() != "":
        if q_type == "Numeric Entry":
            try:
                is_correct = abs(float(user_answer.strip()) - float(correct_ans.strip())) < 1e-4
            except ValueError:
                is_correct = user_answer.strip().lower() == correct_ans.strip().lower()
        elif q_type == "Multiple Choice (Multiple Answers)":
            user_set = {x.strip() for x in user_answer.split(",") if x.strip()}
            correct_set = {x.strip() for x in correct_ans.split(",") if x.strip()}
            is_correct = user_set == correct_set
        else:
            is_correct = user_answer.strip().lower() == correct_ans.strip().lower()

    with db_manager.db_transaction() as cur:
        cur.execute(
            "SELECT response_id, result FROM test_responses WHERE test_id = ? AND question_id = ?",
            (test_id, question_id),
        )
        existing_row = cur.fetchone()
        
        if existing_row:
            cur.execute(
                "UPDATE test_responses SET user_answer = ?, result = ?, time_spent_seconds = time_spent_seconds + ?, timestamp = ? WHERE response_id = ?",
                (user_answer, "correct" if is_correct else "incorrect", time_spent_seconds, time.time(), existing_row["response_id"]),
            )
        else:
            cur.execute(
                """INSERT INTO test_responses (test_id, section_instance_id, question_id, user_answer, correct_answer, result, time_spent_seconds, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (test_id, section_instance_id, question_id, user_answer, correct_ans, "correct" if is_correct else "incorrect", time_spent_seconds, time.time()),
            )
            
            cur.execute("SELECT * FROM user_performance WHERE topic = ?", (topic,))
            perf_row = cur.fetchone()
            if not perf_row:
                cur.execute(
                    """INSERT INTO user_performance (topic, subtopic, total_attempts, correct_attempts, accuracy_pct, avg_speed_seconds) 
                    VALUES (?, '', 1, ?, ?, ?)""",
                    (topic, 1 if is_correct else 0, 100.0 if is_correct else 0.0, float(time_spent_seconds)),
                )
            else:
                tot_att = perf_row["total_attempts"] + 1
                corr_att = perf_row["correct_attempts"] + (1 if is_correct else 0)
                acc_rate = (float(corr_att) / float(tot_att)) * 100
                avg_time = ((perf_row["avg_speed_seconds"] * perf_row["total_attempts"]) + time_spent_seconds) / tot_att
                cur.execute(
                    "UPDATE user_performance SET total_attempts = ?, correct_attempts = ?, accuracy_pct = ?, avg_speed_seconds = ? WHERE topic = ?",
                    (tot_att, corr_att, acc_rate, avg_time, topic),
                )

        if not is_correct and not existing_row:
            err_cat = "Conceptual Deficit" if q_type in ["Numeric Entry", "Multiple Choice"] else "Careless Mistake"
            cur.execute(
                "INSERT INTO error_log (question_id, error_category, user_notes, created_at) VALUES (?, ?, ?, ?)",
                (question_id, err_cat, "Auto-logged during test run", time.time()),
            )
            
    return is_correct

def complete_section_and_adapt(test_id: str, section_instance_id: str) -> Optional[str]:
    db_manager.complete_session_section(section_instance_id)
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT section_key FROM session_sections WHERE section_instance_id = ?", (section_instance_id,))
        completed_sec_name = cur.fetchone()["section_key"]

    if "_1" in completed_sec_name:
        base_measure = completed_sec_name.split("_")[0]
        target_sec_2_name = f"{base_measure}_2"
        
        with db_manager.db_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN result='correct' THEN 1 ELSE 0 END) as correct FROM test_responses WHERE section_instance_id = ?",
                (section_instance_id,)
            )
            stats = cur.fetchone()
            
        total = stats["total"] or 1
        correct = stats["correct"] or 0
        acc = float(correct) / float(total)

        if acc > config.ADAPTIVE_THRESHOLDS["hard"]:
            tier = "hard"
        elif acc <= config.ADAPTIVE_THRESHOLDS["medium"]:
            tier = "easy"
        else:
            tier = "medium"

        with db_manager.db_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE session_sections SET difficulty_tier = ? WHERE test_id = ? AND section_key = ?",
                (tier, test_id, target_sec_2_name),
            )

    next_sec = get_active_section_info(test_id)
    if not next_sec:
        db_manager.complete_test(test_id)
        return None
    return next_sec["section_instance_id"]
