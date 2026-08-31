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
    if metrics["question_count"] > 0:
        return
        
    starter_questions = [
        {
            "question_id": "QNT-ALG-001",
            "section": "Quantitative Reasoning",
            "domain": "Algebra",
            "topic": "Quadratic Equations",
            "subtopic": "Roots",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "If x^2-5x+6=0, what is the sum of all possible values of x?",
            "options": ["2", "3", "5", "6"],
            "correct_answer": "5",
            "explanation": "Factoring gives (x-2)(x-3)=0 so x=2 or x=3. Sum = 2+3=5.",
            "estimated_time_seconds": 90,
        },
        {
            "question_id": "QNT-GEO-001",
            "section": "Quantitative Reasoning",
            "domain": "Geometry",
            "topic": "Triangles",
            "subtopic": "Right Triangles",
            "question_type": "Numeric Entry",
            "difficulty_level": 2,
            "question_text": "A right triangle has legs of length 6 and 8. What is the length of the hypotenuse?",
            "options": None,
            "correct_answer": "10",
            "explanation": "Using Pythagorean theorem: sqrt(6^2+8^2)=sqrt(36+64)=sqrt(100)=10.",
            "estimated_time_seconds": 60,
        },
        {
            "question_id": "VRB-TC-001",
            "section": "Verbal Reasoning",
            "domain": "Text Completion",
            "topic": "Single Blank",
            "subtopic": "Contextual Clues",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "The candidate's speeches were marked by extreme ___; she rarely spoke for more than five minutes.",
            "options": ["loquacity", "brevity", "veracity", "arrogance"],
            "correct_answer": "brevity",
            "explanation": "'rarely spoke for more than five minutes' indicates short duration, pointing directly to brevity.",
            "estimated_time_seconds": 45,
        }
    ]
    batch_add_questions(starter_questions)
    logger.info("Auto-seeded starter question bank with %d questions.", len(starter_questions))