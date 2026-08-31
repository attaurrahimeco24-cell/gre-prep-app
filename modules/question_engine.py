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

def seed_initial_question_bank(force_reset: bool = False) -> None:
    if force_reset:
        with db_manager.db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM questions")
            cur.execute("DELETE FROM user_performance")
            cur.execute("DELETE FROM error_log")

    metrics = db_manager.health_check()
    if metrics["question_count"] >= 10 and not force_reset:
        return
        
    starter_questions = [
        # --- ANALYTICAL WRITING ---
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
            "explanation": "Evaluate clear thesis, structured arguments, and concrete evidence.",
            "estimated_time_seconds": 1800,
        },
        
        # --- QUANTITATIVE REASONING ---
        {
            "question_id": "QNT-ALG-001",
            "section": "Quantitative Reasoning",
            "domain": "Algebra",
            "topic": "Quadratic Equations",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "If x² - 7x + 12 = 0, what is the product of all possible values of x?",
            "options": ["7", "12", "-7", "-12", "5"],
            "correct_answer": "12",
            "explanation": "Factoring yields (x - 3)(x - 4) = 0, so x = 3 or 4. Product = 3 * 4 = 12.",
            "estimated_time_seconds": 60,
        },
        {
            "question_id": "QNT-GEO-002",
            "section": "Quantitative Reasoning",
            "domain": "Geometry",
            "topic": "Circles & Cylinders",
            "question_type": "Multiple Choice",
            "difficulty_level": 4,
            "question_text": "A circle has an area of 36π. What is the length of the longest straight line segment that can be drawn entirely inside the circle?",
            "options": ["6", "12", "18", "36", "12π"],
            "correct_answer": "12",
            "explanation": "Area = πr² = 36π -> r = 6. Longest internal segment is diameter = 2r = 12.",
            "estimated_time_seconds": 75,
        },
        {
            "question_id": "QNT-QC-003",
            "section": "Quantitative Reasoning",
            "domain": "Arithmetic",
            "topic": "Quantitative Comparison",
            "question_type": "Quantitative Comparison",
            "difficulty_level": 3,
            "question_text": "Quantity A: 2⁵⁰\nQuantity B: 3³³",
            "options": [
                "Quantity A is greater.",
                "Quantity B is greater.",
                "The two quantities are equal.",
                "The relationship cannot be determined from the information given."
            ],
            "correct_answer": "Quantity B is greater.",
            "explanation": "2⁵⁰ = (2⁵)¹⁰ = 32¹⁰. 3³³ ≈ (3³)¹¹ = 27¹¹. Comparing 32¹⁰ to 27¹¹, 3³³ is larger.",
            "estimated_time_seconds": 90,
        },
        {
            "question_id": "QNT-NUM-004",
            "section": "Quantitative Reasoning",
            "domain": "Data Analysis",
            "topic": "Statistics & Means",
            "question_type": "Numeric Entry",
            "difficulty_level": 2,
            "question_text": "The average (arithmetic mean) of five integers is 18. If four of the numbers are 12, 15, 20, and 24, what is the fifth number?",
            "options": None,
            "correct_answer": "19",
            "explanation": "Sum needed = 5 * 18 = 90. Known sum = 12 + 15 + 20 + 24 = 71. Fifth = 90 - 71 = 19.",
            "estimated_time_seconds": 45,
        },
        {
            "question_id": "QNT-ALG-005",
            "section": "Quantitative Reasoning",
            "domain": "Algebra",
            "topic": "Exponents & Powers",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "If 2ˣ⁺³ = 64, what is the value of 3ˣ?",
            "options": ["9", "27", "81", "243", "729"],
            "correct_answer": "27",
            "explanation": "264 = 2⁶ -> x + 3 = 6 -> x = 3. Therefore 3³ = 27.",
            "estimated_time_seconds": 60,
        },

        # --- VERBAL REASONING ---
        {
            "question_id": "VRB-TC-001",
            "section": "Verbal Reasoning",
            "domain": "Text Completion",
            "topic": "Contextual Logic",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "The speaker's presentation was marked by extreme ________; she managed to synthesize a decade of complex research in under eight minutes.",
            "options": ["loquacity", "brevity", "veracity", "arrogance", "ambiguity"],
            "correct_answer": "brevity",
            "explanation": "'under eight minutes' points directly to conciseness / brevity.",
            "estimated_time_seconds": 45,
        },
        {
            "question_id": "VRB-SE-002",
            "section": "Verbal Reasoning",
            "domain": "Sentence Equivalence",
            "topic": "Vocabulary in Context",
            "question_type": "Multiple Choice",
            "difficulty_level": 4,
            "question_text": "Despite early harsh assessments by critics, the architectural design has proven remarkably ________, retaining its appeal across decades.",
            "options": ["ephemeral", "enduring", "transient", "perennial", "esoteric", "volatile"],
            "correct_answer": "enduring",
            "explanation": "'retaining its appeal across decades' requires words meaning lasting (enduring).",
            "estimated_time_seconds": 60,
        },
        {
            "question_id": "VRB-RC-003",
            "section": "Verbal Reasoning",
            "domain": "Reading Comprehension",
            "topic": "Inference & Purpose",
            "question_type": "Multiple Choice",
            "difficulty_level": 3,
            "question_text": "Passage Excerpt: 'While early 20th-century geologists assumed continental plates were static, seismic velocity analysis revealed continuous subduction dynamics.' Which claim is supported by the text?",
            "options": [
                "Early geologists utilized seismic velocity analysis extensively.",
                "Subduction dynamics prevent continental drift.",
                "Seismic velocity analysis disproved the static plate assumption.",
                "Continental plates are confirmed to be completely static."
            ],
            "correct_answer": "Seismic velocity analysis disproved the static plate assumption.",
            "explanation": "The passage states seismic analysis revealed dynamics contrary to static assumptions.",
            "estimated_time_seconds": 90,
        },
        {
            "question_id": "VRB-TC-004",
            "section": "Verbal Reasoning",
            "domain": "Text Completion",
            "topic": "Tone & Contrast",
            "question_type": "Multiple Choice",
            "difficulty_level": 4,
            "question_text": "Far from being an ________ force, the new trade policy acted as a major catalyst for regional economic growth.",
            "options": ["inhibiting", "invigorating", "beneficial", "unbiased", "unprecedented"],
            "correct_answer": "inhibiting",
            "explanation": "'Far from being X, it acted as a catalyst for growth'. X must mean hindering/inhibiting.",
            "estimated_time_seconds": 50,
        }
    ]

    batch_add_questions(starter_questions)
    logger.info("Auto-seeded question bank with %d items.", len(starter_questions))
