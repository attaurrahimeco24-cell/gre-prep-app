import pandas as pd
import gre_platform_merged as db

def get_student_performance_telemetry(user_id: str) -> dict:
    with db.db_transaction() as cur:
        cur.execute("SELECT COUNT(*) as c FROM tests WHERE user_id = ? AND status = 'completed'", (user_id,))
        total_tests = cur.fetchone()["c"]
        
        if total_tests == 0:
            return {"total_tests": 0, "domain_df": pd.DataFrame(), "total_answered": 0, "accuracy": 0.0, "weakest_domain": None, "lowest_acc": 0.0}
            
        cur.execute("""
            SELECT 
                COUNT(*) as total_answered,
                SUM(CASE WHEN tr.result = 'correct' THEN 1 ELSE 0 END) as total_correct
            FROM test_responses tr
            JOIN tests t ON tr.test_id = t.test_id
            WHERE t.user_id = ?
        """, (user_id,))
        overall = cur.fetchone()
        
        cur.execute("""
            SELECT 
                q.domain,
                COUNT(tr.response_id) as attempted,
                SUM(CASE WHEN tr.result = 'correct' THEN 1 ELSE 0 END) as correct
            FROM test_responses tr
            JOIN questions q ON tr.question_id = q.question_id
            JOIN tests t ON tr.test_id = t.test_id
            WHERE t.user_id = ?
            GROUP BY q.domain
        """, (user_id,))
        domain_rows = cur.fetchall()

    total_answered = overall["total_answered"] or 0
    total_correct = overall["total_correct"] or 0
    accuracy = (total_correct / total_answered * 100) if total_answered > 0 else 0.0
    
    domains = []
    weakest_domain = None
    lowest_acc = 100.0
    
    for row in domain_rows:
        dom_acc = (row["correct"] / row["attempted"] * 100) if row["attempted"] > 0 else 0
        domains.append({"Domain": row["domain"], "Accuracy (%)": round(dom_acc, 1)})
        if dom_acc < lowest_acc and row["attempted"] >= 1:
            lowest_acc = dom_acc
            weakest_domain = row["domain"]

    domain_df = pd.DataFrame(domains) if domains else pd.DataFrame()

    return {
        "total_tests": total_tests,
        "total_answered": total_answered,
        "accuracy": accuracy,
        "domain_df": domain_df,
        "weakest_domain": weakest_domain,
        "lowest_acc": lowest_acc
    }
