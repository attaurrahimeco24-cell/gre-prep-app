import random
import uuid
import gre_platform_merged as db_manager

def generate_svg_triangle(base, height):
    """Generates an authentic, high-contrast black & white GRE triangle diagram."""
    return f'''
    <div style="background: #FFFFFF; padding: 24px; border-radius: 4px; width: max-content; margin: 16px 0; border: 2px solid #000000; box-shadow: 2px 2px 0px #000000;">
        <svg height="160" width="240" xmlns="http://www.w3.org/2000/svg">
            <polygon points="40,130 200,130 120,30" style="fill:transparent;stroke:#000000;stroke-width:3;stroke-linejoin:round" />
            <line x1="120" y1="30" x2="120" y2="130" style="stroke:#000000;stroke-width:2;stroke-dasharray:6,4" />
            <polyline points="120,115 135,115 135,130" style="fill:transparent;stroke:#000000;stroke-width:2" />
            <text x="100" y="152" fill="#000000" font-weight="bold" font-family="Arial, sans-serif" font-size="16">Base = {base}</text>
            <text x="130" y="85" fill="#000000" font-weight="bold" font-family="Arial, sans-serif" font-size="16">h = {height}</text>
        </svg>
    </div>
    '''

def generate_svg_circle(radius):
    """Generates an authentic, high-contrast black & white GRE circle diagram."""
    return f'''
    <div style="background: #FFFFFF; padding: 24px; border-radius: 4px; width: max-content; margin: 16px 0; border: 2px solid #000000; box-shadow: 2px 2px 0px #000000;">
        <svg height="160" width="160" xmlns="http://www.w3.org/2000/svg">
            <circle cx="80" cy="80" r="65" style="fill:transparent;stroke:#000000;stroke-width:3" />
            <circle cx="80" cy="80" r="4" style="fill:#000000" />
            <line x1="80" y1="80" x2="145" y2="80" style="stroke:#000000;stroke-width:2;stroke-dasharray:6,4" />
            <text x="95" y="72" fill="#000000" font-weight="bold" font-family="Arial, sans-serif" font-size="16">r = {radius}</text>
        </svg>
    </div>
    '''

def generate_2000_questions():
    questions = []
    
    for _ in range(300):
        a = random.randint(2, 9)
        b = random.randint(10, 50)
        c = random.randint(100, 200)
        ans = (c - b) / a
        questions.append({
            "question_id": f"Q-ALG-{uuid.uuid4().hex[:6]}", "section": "Quantitative Reasoning",
            "domain": "Algebra", "topic": "Linear Equations", "question_type": "Numeric Entry",
            "difficulty_level": random.randint(1, 5), "question_text": f"If {a}x + {b} = {c}, what is the exact value of x?",
            "options": None, "correct_answer": f"{ans:.2f}".rstrip('0').rstrip('.'),
            "explanation": f"Subtract {b} from both sides to get {a}x = {c-b}. Then divide by {a}."
        })

    for _ in range(200):
        b, h = random.randint(4, 20), random.randint(4, 20)
        area = 0.5 * b * h
        questions.append({
            "question_id": f"Q-GEO-{uuid.uuid4().hex[:6]}", "section": "Quantitative Reasoning",
            "domain": "Geometry", "topic": "Triangles", "question_type": "Multiple Choice",
            "difficulty_level": random.randint(2, 5),
            "question_text": f"As shown in the figure below, a triangle has a base of {b} and a height of {h}. What is the area of the triangle? {generate_svg_triangle(b, h)}",
            "options": [str(area), str(area + 5), str(b*h), str((b*h)/3), str(area - 2)],
            "correct_answer": str(area), "explanation": f"The area of a triangle is 0.5 * base * height. 0.5 * {b} * {h} = {area}."
        })
        
    for _ in range(200):
        r = random.randint(3, 15)
        area = 3.14159 * (r**2)
        questions.append({
            "question_id": f"Q-GEO-{uuid.uuid4().hex[:6]}", "section": "Quantitative Reasoning",
            "domain": "Geometry", "topic": "Circles", "question_type": "Multiple Choice",
            "difficulty_level": random.randint(2, 5),
            "question_text": f"A circle has a radius of {r} as shown below. Which of the following is closest to its area? {generate_svg_circle(r)}",
            "options": [f"{area:.1f}", f"{(area+10):.1f}", f"{(2*3.14159*r):.1f}", f"{(area*2):.1f}", f"{(r**2):.1f}"],
            "correct_answer": f"{area:.1f}", "explanation": f"Area = πr². 3.14159 * {r}² ≈ {area:.1f}."
        })

    for _ in range(300):
        orig = random.randint(50, 500)
        pct = random.choice([10, 15, 20, 25, 30])
        ans = orig * (1 + pct/100)
        questions.append({
            "question_id": f"Q-ARI-{uuid.uuid4().hex[:6]}", "section": "Quantitative Reasoning",
            "domain": "Arithmetic", "topic": "Percentages", "question_type": "Numeric Entry",
            "difficulty_level": random.randint(1, 4), "question_text": f"A store purchases an item for ${orig} and marks it up by {pct}%. What is the final selling price?",
            "options": None, "correct_answer": str(ans), "explanation": f"{pct}% of {orig} is {orig*(pct/100)}. {orig} + {orig*(pct/100)} = {ans}."
        })

    vocab_words = [("ephemeral", "short-lived"), ("mitigate", "alleviate"), ("sycophant", "flatterer"), ("cacophony", "harsh noise"), ("obdurate", "stubborn")]
    for _ in range(400):
        word, meaning = random.choice(vocab_words)
        questions.append({
            "question_id": f"Q-VER-{uuid.uuid4().hex[:6]}", "section": "Verbal Reasoning",
            "domain": "Text Completion", "topic": "Vocabulary in Context", "question_type": "Multiple Choice",
            "difficulty_level": random.randint(1, 5), "question_text": f"Despite the manager's attempts to ______ the situation, the employees remained extremely upset.",
            "options": ["mitigate", "exacerbate", "obfuscate", "prolong", "celebrate"],
            "correct_answer": "mitigate", "explanation": "The word 'Despite' indicates a contrast. 'Mitigate' means to make less severe."
        })
        
    for _ in range(400):
        questions.append({
            "question_id": f"Q-VER-{uuid.uuid4().hex[:6]}", "section": "Verbal Reasoning",
            "domain": "Reading Comprehension", "topic": "Passage Analysis", "question_type": "Multiple Choice",
            "difficulty_level": random.randint(2, 5),
            "question_text": f"**Passage:** In the late 19th century, biological determinism became a dominant paradigm. However, modern geneticists argue that environment plays a far more critical role.\n\n**Question:** The author's primary purpose is to:",
            "options": ["Contrast two historical scientific paradigms", "Prove that biology is irrelevant", "Argue for biological determinism", "Summarize 19th-century politics", "Describe environmental science"],
            "correct_answer": "Contrast two historical scientific paradigms", "explanation": "The passage shifts from 19th century determinism to modern environmental views."
        })

    for _ in range(200):
        questions.append({
            "question_id": f"Q-AWA-{uuid.uuid4().hex[:6]}", "section": "Analytical Writing",
            "domain": "Issue Task", "topic": "Society & Technology", "question_type": "Issue Task",
            "difficulty_level": random.randint(3, 5),
            "question_text": "To understand the most important characteristics of a society, one must study its major cities.\n\nWrite a response discussing the extent to which you agree or disagree.",
            "options": None, "correct_answer": "ESSAY_RESPONSE", "explanation": "Score is based on logic, structure, and vocabulary."
        })

    return questions

def seed_initial_question_bank(force_reset=False):
    db_manager.initialize_database()
    count = db_manager.count_questions()
    if count >= 1000 and not force_reset: return
    if force_reset:
        with db_manager.db_transaction() as cur: cur.execute("DELETE FROM questions")
    for q in generate_2000_questions():
        try: db_manager.insert_question(q)
        except Exception: pass
