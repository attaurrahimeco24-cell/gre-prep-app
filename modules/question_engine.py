def seed_initial_question_bank() -> None:
    metrics = db_manager.health_check()
    if metrics["question_count"] >= 5:
        return
        
    starter_questions = [
        {
            "question_id": "AWA-ISS-001",
            "section": "Analytical Writing",
            "domain": "Analytical Writing",
            "topic": "Analyze an Issue",
            "question_type": "Issue Task",
            "difficulty_level": 3,
            "question_text": "To understand the most important characteristics of a society, one must study its major cities. Write a response in which you discuss the extent to which you agree or disagree.",
            "options": None,
            "correct_answer": "N/A",
            "explanation": "Evaluate clear thesis statement, supporting evidence, and counterarguments.",
            "estimated_time_seconds": 1800,
        },
        {
            "question_id": "QNT-GEO-042",
            "section": "Quantitative Reasoning",
            "domain": "Geometry",
            "topic": "Circles and Cylinders",
            "question_type": "Multiple Choice",
            "difficulty_level": 4,
            "question_text": "A right circular cylinder has a volume of 72π and a height of 8. What is the circumference of its base?",
            "options": ["3π", "6π", "9π", "12π", "18π"],
            "correct_answer": "6π",
            "explanation": "Volume = πr²h. 72π = πr²(8). r² = 9, so r = 3. Circumference = 2πr = 2π(3) = 6π.",
            "estimated_time_seconds": 90,
        },
        {
            "question_id": "QNT-STA-018",
            "section": "Quantitative Reasoning",
            "domain": "Data Analysis",
            "topic": "Probability",
            "question_type": "Numeric Entry",
            "difficulty_level": 3,
            "question_text": "A jar contains 4 red marbles, 5 blue marbles, and 3 green marbles. If two marbles are drawn at random without replacement, what is the probability that both are blue? (Enter as a decimal to two places)",
            "options": None,
            "correct_answer": "0.15",
            "explanation": "Total marbles = 12. P(First is blue) = 5/12. P(Second is blue) = 4/11. (5/12) * (4/11) = 20/132 = 5/33 ≈ 0.15.",
            "estimated_time_seconds": 120,
        },
        {
            "question_id": "VRB-TC-088",
            "section": "Verbal Reasoning",
            "domain": "Text Completion",
            "topic": "Contextual Logic",
            "question_type": "Multiple Choice",
            "difficulty_level": 4,
            "question_text": "Despite the team’s outward display of ________, the atmosphere in the locker room was actually fraught with tension and mutual suspicion.",
            "options": ["hostility", "camaraderie", "apathy", "competence", "cynicism"],
            "correct_answer": "camaraderie",
            "explanation": "The word 'Despite' sets up a contrast with 'tension and mutual suspicion'. 'Camaraderie' (friendship/trust) provides the exact opposite meaning required.",
            "estimated_time_seconds": 45,
        },
        {
            "question_id": "VRB-RC-012",
            "section": "Verbal Reasoning",
            "domain": "Reading Comprehension",
            "topic": "Primary Purpose",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "Read the excerpt: 'While early historians viewed the industrial shift as a sudden upheaval, modern economists argue it was a gradual transition layered upon existing agrarian networks.' What is the primary purpose of this sentence?",
            "options": [
                "To disprove a modern economic theory.",
                "To contrast two historical interpretations of an event.",
                "To argue that agrarian networks were inefficient.",
                "To suggest that historians ignore economic data."
            ],
            "correct_answer": "To contrast two historical interpretations of an event.",
            "explanation": "The text explicitly contrasts how 'early historians' viewed the shift versus how 'modern economists' view it.",
            "estimated_time_seconds": 75,
        }
    ]

    batch_add_questions(starter_questions)
    logger.info("Auto-seeded diverse test bank with %d questions.", len(starter_questions))
