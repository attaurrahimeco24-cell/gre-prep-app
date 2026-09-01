import json
import gre_platform_merged as db

def seed_initial_question_bank():
    with db.db_transaction() as cur:
        cur.execute("SELECT COUNT(*) as c FROM questions")
        if cur.fetchone()["c"] >= 5:
            return

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

        cur.executemany("""
            INSERT OR REPLACE INTO questions (question_id, section, domain, topic, question_type, difficulty, question_text, options_json, correct_answer, explanation, svg_payload, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, questions)
