import json
import gre_platform_merged as db_manager

def seed_initial_question_bank():
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM questions")
        count = cur.fetchone()["c"]
        if count >= 10:
            return  # Already seeded with sufficient questions

        questions = [
            # Quantitative 1
            (
                "Q1", "Quantitative", "Algebra", "Linear Equations", "Multiple Choice", 2,
                "If $3x + 7 = 22$, what is the value of $2x - 3$?",
                json.dumps(["5", "7", "10", "12", "15"]), "7",
                "Subtract 7 from both sides: $3x = 15 \\implies x = 5$. Substitute into $2x - 3$: $2(5) - 3 = 7$.",
                None, "APPROVED"
            ),
            # Quantitative 2
            (
                "Q2", "Quantitative", "Geometry", "Triangles", "Multiple Choice", 3,
                "In a right-angled triangle, one leg has length 6 and the hypotenuse has length 10. What is the area of the triangle?",
                json.dumps(["12", "24", "30", "48", "60"]), "24",
                "Using Pythagorean theorem: $6^2 + b^2 = 10^2 \\implies b = 8$. Area = $\\frac{1}{2} \\times 6 \\times 8 = 24$.",
                "<svg width='200' height='150'><polygon points='20,130 180,130 20,30' fill='none' stroke='black' stroke-width='2'/><text x='90' y='145'>6</text><text x='5' y='80'>8</text><text x='110' y='75'>10</text></svg>",
                "APPROVED"
            ),
            # Quantitative 3
            (
                "Q3", "Quantitative", "Arithmetic", "Percentages", "Multiple Choice", 1,
                "An item originally priced at $120 is on sale for 25% off. What is the sale price?",
                json.dumps(["$80", "$85", "$90", "$95", "$100"]), "$90",
                "Discount = $120 \\times 0.25 = $30. Sale price = $120 - $30 = $90.",
                None, "APPROVED"
            ),
            # Quantitative 4
            (
                "Q4", "Quantitative", "Data Analysis", "Statistics", "Multiple Choice", 2,
                "What is the median of the following set of numbers: 14, 7, 22, 19, 3, 11, 28?",
                json.dumps(["11", "14", "15", "19", "22"]), "14",
                "First, arrange in ascending order: 3, 7, 11, 14, 19, 22, 28. The middle (4th) number is 14.",
                None, "APPROVED"
            ),
            # Quantitative 5
            (
                "Q5", "Quantitative", "Algebra", "Exponents", "Multiple Choice", 3,
                "If $2^{x+1} = 32$, what is the value of $x$?",
                json.dumps(["2", "3", "4", "5", "6"]), "4",
                "Rewrite 32 as $2^5$. Thus, $2^{x+1} = 2^5 \\implies x + 1 = 5 \\implies x = 4$.",
                None, "APPROVED"
            ),
            # Verbal 1
            (
                "V1", "Verbal", "Text Completion", "Vocabulary", "Text Completion", 2,
                "The CEO's ______ demeanor during the crisis calmed the jittery investors and prevented a massive sell-off.",
                json.dumps(["belligerent", "sangfroid", "petulant", "laconic", "truculent"]), "sangfroid",
                "Sangfroid refers to calmness or composure, especially in a difficult situation, which matches the context.",
                None, "APPROVED"
            ),
            # Verbal 2
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
            ),
            # Verbal 3
            (
                "V3", "Verbal", "Sentence Equivalence", "Vocabulary", "Multiple Choice", 3,
                "The politician's speech was remarkable for its ______, deftly avoiding taking a firm stance on any of the contentious ballot measures.",
                json.dumps(["candor", "equivocation", "brevity", "perspicuity", "terpitude", "prevarication"]), "equivocation",
                "Equivocation and prevarication both mean using ambiguous language to conceal the truth or avoid committing to a stance. (Note: select equivalent pair contextually; here equivocation fits best).",
                None, "APPROVED"
            )
        ]

        cur.executemany("""
            INSERT OR REPLACE INTO questions (question_id, section, domain, topic, question_type, difficulty, question_text, options_json, correct_answer, explanation, svg_payload, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, questions)
