def seed_initial_question_bank() -> None:
    metrics = db_manager.health_check()
    # Only seed if the database doesn't have enough questions for a full test
    if metrics["question_count"] >= 55:
        return
        
    starter_questions = []
    
    # 1. Add Analytical Writing Task
    starter_questions.append({
        "question_id": "AWA-ISS-001",
        "section": "Analytical Writing",
        "domain": "Analytical Writing",
        "topic": "Analyze an Issue",
        "question_type": "Issue Task",
        "difficulty_level": 3,
        "question_text": "As technology becomes more integrated into daily life, human independence decreases. Write a response in which you discuss the extent to which you agree or disagree.",
        "options": None,
        "correct_answer": "N/A",
        "explanation": "Evaluate clear thesis statement, supporting evidence, and counterarguments.",
        "estimated_time_seconds": 1800,
    })
    
    # 2. Add 30 Verbal Questions
    for i in range(1, 31):
        starter_questions.append({
            "question_id": f"VRB-TC-{i:03d}",
            "section": "Verbal Reasoning",
            "domain": "Text Completion",
            "topic": "Single Blank",
            "question_type": "Multiple Choice",
            "difficulty_level": (i % 3) + 2, # Rotates difficulties 2, 3, 4
            "question_text": f"[Verbal Practice Q{i}] The candidate's speeches were marked by extreme ___; she rarely spoke for more than five minutes.",
            "options": ["loquacity", "brevity", "veracity", "arrogance"],
            "correct_answer": "brevity",
            "explanation": "Points directly to brevity.",
            "estimated_time_seconds": 45,
        })
        
    # 3. Add 30 Quantitative Questions
    for i in range(1, 31):
        starter_questions.append({
            "question_id": f"QNT-ALG-{i:03d}",
            "section": "Quantitative Reasoning",
            "domain": "Algebra",
            "topic": "Quadratic Equations",
            "question_type": "Multiple Choice",
            "difficulty_level": (i % 3) + 2,
            "question_text": f"[Quant Practice Q{i}] If x^2 - 5x + 6 = 0, what is the sum of all possible values of x?",
            "options": ["2", "3", "5", "6"],
            "correct_answer": "5",
            "explanation": "Factoring gives (x-2)(x-3)=0 so x=2 or x=3. Sum = 5.",
            "estimated_time_seconds": 90,
        })

    batch_add_questions(starter_questions)
    logger.info("Auto-seeded full test bank with %d questions.", len(starter_questions))
