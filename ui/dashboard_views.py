import streamlit as st
from modules.analytics_engine import get_student_performance_telemetry
from ui.components import render_score_card

def render_analytics_dashboard():
    user_id = st.session_state["user_id"]
    data = get_student_performance_telemetry(user_id)
    
    st.markdown("## 📈 Performance Analytics & Diagnostics")
    st.caption("Review historical exam metrics, domain proficiency, and AI recommendations.")
    st.divider()
    
    if data["total_tests"] == 0:
        st.info("No completed exam sessions found. Complete a test in your workspace to unlock performance telemetry.")
        return

    m1, m2, m3 = st.columns(3)
    with m1: render_score_card("Tests Completed", str(data["total_tests"]))
    with m2: render_score_card("Total Answered", str(data["total_answered"]))
    with m3: render_score_card("Overall Accuracy", f"{round(data['accuracy'], 1)}%")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 📊 Domain Accuracy Breakdown")
        if not data["domain_df"].empty:
            st.bar_chart(data["domain_df"].set_index("Domain"))
        else:
            st.info("Insufficient response data for domain breakdown.")
            
    with c2:
        st.markdown("### 🎯 AI Diagnostic & Study Plan")
        if data["weakest_domain"]:
            st.warning(f"**Focus Area Detected:** Your accuracy in **{data['weakest_domain']}** is currently your lowest at **{round(data['lowest_acc'], 1)}%**.")
            st.markdown("**Recommended Action:** Allocate 45 minutes today to targeted practice sets focusing on core formulas and foundational principles in this domain.")
        else:
            st.success("✓ Excellent performance across all tested domains!")
