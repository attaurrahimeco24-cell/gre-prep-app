import time
import gre_platform_merged as db_manager

def initialize_test_session(test_type: str = "full_length") -> dict:
    """Initializes a new exam and queues up Section 1."""
    if test_type not in db_manager.VALID_MODES and test_type != "full_length":
        test_type = "full_length"
        
    test_id = db_manager.create_test(test_type)
    
    # Dynamically find the first section (Order = 1)
    first_section_key = None
    for key, config in db_manager.SECTION_STRUCTURE.items():
        if config["order"] == 1:
            first_section_key = key
            break
            
    if first_section_key:
        db_manager.create_session_section(test_id, first_section_key)
        
    return {"test_id": test_id}

def get_active_section_info(test_id: str) -> dict:
    """Checks if there is a section currently pending or in progress for this test."""
    with db_manager.db_cursor() as cur:
        cur.execute("""
            SELECT section_instance_id, section_key, difficulty_tier, status, time_allotted_seconds, section_start_timestamp 
            FROM session_sections 
            WHERE test_id = ? AND status IN ('pending', 'in_progress')
            ORDER BY section_start_timestamp DESC LIMIT 1
        """, (test_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
    return None

def start_active_section(section_instance_id: str) -> dict:
    """Starts the timer and fetches the exact questions for this section and difficulty tier."""
    start_ts = db_manager.start_session_section(section_instance_id)
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT test_id, section_key, difficulty_tier, time_allotted_seconds FROM session_sections WHERE section_instance_id = ?", (section_instance_id,))
        sec_info = cur.fetchone()
        
    sec_key = sec_info["section_key"]
    tier = sec_info["difficulty_tier"]
    time_allotted = sec_info["time_allotted_seconds"]
    
    sec_config = db_manager.SECTION_STRUCTURE[sec_key]
    
    # Map section key to domain
    domain_mapping = {
        "AW": "Analytical Writing",
        "VERBAL_1": "Verbal Reasoning",
        "VERBAL_2": "Verbal Reasoning",
        "QUANT_1": "Quantitative Reasoning",
        "QUANT_2": "Quantitative Reasoning"
    }
    measure = domain_mapping.get(sec_key, "Quantitative Reasoning")
    
    # Apply Adaptive Difficulty Tiers for Section 2
    diff_levels = [1, 2, 3, 4, 5]
    if tier == "hard":
        diff_levels = [4, 5]
    elif tier == "medium":
        diff_levels = [3, 4]
    elif tier == "easy":
        diff_levels = [1, 2]
        
    # Fetch questions
    questions = db_manager.get_questions_filtered(
        section=measure, 
        difficulty_levels=diff_levels, 
        limit=sec_config["question_count"]
    )
    
    return {
        "section_instance_id": section_instance_id,
        "section_name": sec_config["label"],
        "duration_seconds": time_allotted,
        "start_timestamp": start_ts,
        "questions": questions
    }

def submit_answer_atomically(test_id: str, section_instance_id: str, question_id: str, user_answer: str, time_spent: int):
    """Saves the student's answer to the database instantly."""
    q = db_manager.get_question_by_id(question_id)
    if not q:
        return
        
    # Evaluate correctness
    is_correct = (str(user_answer).strip().lower() == str(q["correct_answer"]).strip().lower())
    result = "correct" if is_correct else "incorrect"
    
    with db_manager.db_transaction() as cur:
        cur.execute("SELECT response_id FROM test_responses WHERE test_id = ? AND question_id = ?", (test_id, question_id))
        existing = cur.fetchone()
        
        if existing:
            # Update if they changed their answer
            cur.execute("UPDATE test_responses SET user_answer = ?, result = ?, time_spent_seconds = ? WHERE response_id = ?", 
                        (user_answer, result, time_spent, existing["response_id"]))
        else:
            # Insert new answer
            cur.execute("INSERT INTO test_responses (test_id, question_id, section_instance_id, user_answer, correct_answer, result, time_spent_seconds) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (test_id, question_id, section_instance_id, user_answer, q["correct_answer"], result, time_spent))

def complete_section_and_adapt(test_id: str, section_instance_id: str):
    """Closes the current section, calculates the score, and adaptively routes to Hard/Medium/Easy."""
    db_manager.complete_session_section(section_instance_id)
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT section_key FROM session_sections WHERE section_instance_id = ?", (section_instance_id,))
        row = cur.fetchone()
        if not row: return
        current_sec_key = row["section_key"]
        
    current_config = db_manager.SECTION_STRUCTURE.get(current_sec_key, {})
    determines_next = current_config.get("determines_next")
    
    # Find the logically next section (Order + 1)
    next_sec_key = None
    for k, v in db_manager.SECTION_STRUCTURE.items():
        if v.get("order") == current_config.get("order", 0) + 1:
            next_sec_key = k
            break
            
    # If there is no next section, the exam is over
    if not next_sec_key:
        db_manager.complete_test(test_id)
        return
        
    # Calculate Adaptive Routing (if applicable)
    next_tier = None
    if determines_next and determines_next == next_sec_key:
        with db_manager.db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as c FROM test_responses WHERE section_instance_id = ? AND result = 'correct'", (section_instance_id,))
            correct = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM test_responses WHERE section_instance_id = ?", (section_instance_id,))
            total = cur.fetchone()["c"]
            
        acc = correct / total if total > 0 else 0
        
        hard_th = db_manager.ADAPTIVE_THRESHOLDS["hard"]
        med_th = db_manager.ADAPTIVE_THRESHOLDS["medium"]
        
        if acc >= hard_th:
            next_tier = "hard"
        elif acc >= med_th:
            next_tier = "medium"
        else:
            next_tier = "easy"
        
    # Queue up the next section with the calculated difficulty tier
    db_manager.create_session_section(test_id, next_sec_key, difficulty_tier=next_tier)
