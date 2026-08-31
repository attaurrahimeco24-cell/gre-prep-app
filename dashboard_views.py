import streamlit as st
import gre_platform_merged as db_manager
from ui import components

def render_analytics_dashboard() -> None:
    st.header("Performance Dashboard")
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM tests WHERE status = 'completed'")
        completed_tests = cur.fetchone()["c"]
        
        cur.execute("SELECT topic, accuracy_pct, total_attempts FROM user_performance ORDER BY accuracy_pct ASC LIMIT 5")
        weaknesses = cur.fetchall()

    c1, c2 = st.columns(2)
    with c1:
        components.render_score_card("Completed Tests", str(completed_tests))
    with c2:
        components.render_score_card("Topics Tracked", str(len(weaknesses)))

    st.subheader("Top Weaknesses")
    if weaknesses:
        for w in weaknesses:
            st.markdown(f"- **{w['topic']}**: {w['accuracy_pct']:.1f}% accuracy ({w['total_attempts']} attempts)")
    else:
        st.info("Complete practice sections to generate weakness analytics.")