import json
import gre_platform_merged as db

def seed_initial_question_bank():
    with db.db_transaction() as cur:
        cur.execute("SELECT COUNT(*) as c FROM questions")
        current_count = cur.fetchone()["c"]
        if current_count >= 2000:
            return

        # Core seed baseline
        questions = [
            (
                "Q1", "Quantitative", "Algebra", "Linear Equations", "Multiple Choice", 2,
                "If $3x + 7 = 22$, what is the value of $2x - 3$?",
                json.dumps(["5", "7", "10", "12", "15"]), "7",
                "Subtract 7 from both sides: $3x = 15 \\implies x = 5$. Substitute into $2x - 3$: $2(5) - 3 = 7$.",
                None, "APPROVED"
            ),
            (
                "Q2", "Quantitative", "Geometry", "Triangles", "Multiple Choice", 3,
                "In a right-angled triangle, one leg has length 6 and the hypotenuse has length 10. What is the area of the triangle?",
                json.dumps(["12", "24", "30", "48", "60"]), "24",
                "Using Pythagorean theorem: $6^2 + b^2 = 10^2 \\implies b = 8$. Area = $\\frac{1}{2} \\times 6 \\times 8 = 24$.",
                "<svg width='200' height='150' role='img' aria-label='Right Triangle Diagram'><polygon points='20,130 180,130 20,30' fill='none' stroke='#0F172A' stroke-width='2'/><text x='90' y='145'>6</text><text x='5' y='80'>8</text><text x='110' y='75'>10</text></svg>",
                "APPROVED"
            ),
            (
                "Q3", "Quantitative", "Arithmetic", "Percentages", "Multiple Choice", 1,
                "An item originally priced at $120 is on sale for 25% off. What is the sale price?",
                json.dumps(["$80", "$85", "$90", "$95", "$100"]), "$90",
                "Discount = $120 \\times 0.25 = $30. Sale price = $120 - $30 = $90.",
                None, "APPROVED"
            ),
            (
                "V1", "Verbal", "Text Completion", "Vocabulary", "Text Completion", 2,
                "The CEO's ______ demeanor during the crisis calmed the jittery investors and prevented a massive sell-off.",
                json.dumps(["belligerent", "sangfroid", "petulant", "laconic", "truculent"]), "sangfroid",
                "Sangfroid refers to calmness or composure, especially in a difficult situation, which matches the context.",
                None, "APPROVED"
            ),
            (
                "V2", "Verbal", "Reading Comprehension", "Science", "Reading Comprehension", 3,
                "Passage: Recent studies on marine phytoplankton indicate that rising ocean temperatures may paradoxically stimulate sudden localized blooms while reducing overall global biomass.<br><br>Question: According to the passage, what is the effect of rising ocean temperatures on marine phytoplankton?",
                json.dumps([
                    "It uniformly increases global biomass.",
                    "It decreases local blooms everywhere.",
                    "It may stimulate localized blooms while decreasing overall global biomass.",
                    "It has no measurable impact on phytoplankton distribution.",
                    "It permanently eradicates coastal species."
                ]),
                "It may stimulate localized blooms while decreasing overall global biomass.",
                "The passage explicitly states that rising temperatures 'paradoxically stimulate sudden localized blooms while reducing overall global biomass.'",
                None, "APPROVED"
            )
        ]

        # Procedurally expand to 2,000 items for testing performance and analytics
        domains = [("Quantitative", "Algebra"), ("Quantitative", "Geometry"), ("Quantitative", "Arithmetic"), ("Verbal", "Text Completion"), ("Verbal", "Reading Comprehension")]
        
        for i in range(current_count + 1, 2001):
            dom, top = domains[i % len(domains)]
            q_id = f"GEN_{i}"
            sec = dom
            q_type = "Multiple Choice" if dom == "Quantitative" else "Text Completion"
            diff = (i % 3) + 1
            text = f"Sample generated GRE {dom} question #{i} concerning {top} principles."
            options = json.dumps([f"Option A{i}", f"Option B{i}", f"Option C{i}", f"Option D{i}", f"Correct Answer {i}"])
            correct = f"Correct Answer {i}"
            explanation = f"Detailed step-by-step solution breakdown for generated asset {i}."
            svg = "<svg width='150' height='100'><circle cx='75' cy='50' r='40' fill='#E2E8F0'/></svg>" if top == "Geometry" else None
            
            questions.append((q_id, sec, dom, top, q_type, diff, text, options, correct, explanation, svg, "APPROVED"))

        cur.executemany("""
            INSERT OR IGNORE INTO questions (question_id, section, domain, topic, question_type, difficulty, question_text, options_json, correct_answer, explanation, svg_payload, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, questions)
