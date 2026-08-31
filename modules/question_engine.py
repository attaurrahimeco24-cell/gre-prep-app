import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Sequence
import gre_platform_merged as config
import gre_platform_merged as db_manager

logger = logging.getLogger("GRE_PLATFORM.question_engine")

def validate_question_structure(q_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    required_keys = ["question_id", "section", "question_text", "question_type", "difficulty_level"]
    for key in required_keys:
        if not q_data.get(key):
            errors.append(f"Missing required field: '{key}'")
            
    valid_sections = ["Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"]
    if q_data.get("section") and q_data["section"] not in valid_sections:
        errors.append(f"Invalid section '{q_data['section']}'. Must be one of {valid_sections}")
        
    diff = q_data.get("difficulty_level")
    if diff is not None and (not isinstance(diff, int) or not (1 <= diff <= 5)):
        errors.append(f"Difficulty level must be integer 1 to 5, got: {diff}")
        
    q_type = q_data.get("question_type", "")
    if q_data.get("section") != "Analytical Writing":
        if not q_data.get("correct_answer"):
            errors.append("Non-AWA question must provide 'correct_answer'")
        if q_type not in ["Numeric Entry", "Issue Task"]:
            options = q_data.get("options")
            if not isinstance(options, list) or len(options) < 2:
                errors.append(f"Question type '{q_type}' requires an options array with >=2 items.")
                
    if q_type == "Quantitative Comparison":
        qc_options = [
            "Quantity A is greater.",
            "Quantity B is greater.",
            "The two quantities are equal.",
            "The relationship cannot be determined from the information given."
        ]
        options = q_data.get("options", [])
        if options != qc_options:
            q_data["options"] = qc_options 
            
    is_valid = len(errors) == 0
    return is_valid, errors

def add_question(q_data: Dict[str, Any]) -> str:
    is_valid, errors = validate_question_structure(q_data)
    if not is_valid:
        raise ValueError(f"Question validation failed for {q_data.get('question_id')}: {'; '.join(errors)}")
    return db_manager.insert_question(q_data)

def batch_add_questions(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    successful = []
    failed = []
    for idx, q in enumerate(questions):
        try:
            q_id = add_question(q)
            successful.append(q_id)
        except Exception as e:
            failed.append({
                "index": idx,
                "question_id": q.get("question_id", "UNKNOWN"),
                "error": str(e)
            })
    return {
        "total_processed": len(questions),
        "inserted_count": len(successful),
        "failed_count": len(failed),
        "successful_ids": successful,
        "failures": failed
    }

def fetch_question(question_id: str) -> Optional[Dict[str, Any]]:
    return db_manager.get_question_by_id(question_id)

def build_section_question_set(section_name: str, target_count: int, difficulty_baseline: int = 3, exclude_ids: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
    if difficulty_baseline <= 2:
        diff_range = [1, 2, 3]
    elif difficulty_baseline >= 4:
        diff_range = [3, 4, 5]
    else:
        diff_range = [2, 3, 4]
        
    questions = db_manager.get_questions_filtered(
        section=section_name,
        difficulty_levels=diff_range,
        exclude_ids=exclude_ids,
        limit=target_count
    )
    
    if len(questions) < target_count:
        fetched_ids = [q["question_id"] for q in questions]
        all_excluded = list(exclude_ids or []) + fetched_ids
        needed = target_count - len(questions)
        fallback = db_manager.get_questions_filtered(
            section=section_name,
            exclude_ids=all_excluded,
            limit=needed
        )
        questions.extend(fallback)
    return questions

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
