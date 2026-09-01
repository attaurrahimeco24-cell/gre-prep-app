import streamlit as st
from datetime import datetime
from modules import analytics_engine, testing_engine

def get_greeting():
    hour = datetime.now().hour
    if hour < 12: return "Good morning"
    elif hour < 17: return "Good afternoon"
    else: return "Good evening"

def render_analytics_dashboard():
    user_id = st.session_state.get("user_id")
    username = st.session_state.get("username", "Student")
    
    st.markdown(f"## {get_greeting()}, {username}.")
    st.caption("Here is your data-driven psychometric performance analysis.")
    st.divider()
    
    with st.spinner("Compiling your performance telemetry..."):
        data = analytics_engine.get_student_dashboard_data(user_id)
        
    if data["total_tests"] == 0:
        st.info("You haven't completed any practice tests yet. Your dashboard requires data to generate insights.")
        st.markdown("### Let's establish your baseline.")
        if st.button("🚀 Start Diagnostic Exam", type="primary"):
            st.session_state["active_test_id"] = testing_engine.initialize_test_session(user_id)["test_id"]
            st.session_state["active_page"] = "⏱️ Exam Simulator"
            st.rerun()
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Exams Completed", data["total_tests"])
    c2.metric("Overall Accuracy", f"{data['accuracy']:.1f}%")
    c3.metric("Questions Answered", data["total_answered"])
    c4.metric("Avg. Time per Question", f"{data['avg_time']:.1f}s")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart, col_recs = st.columns([2, 1])
    with col_chart:
        st.markdown("### 📊 Domain Accuracy Profile")
        if not data["domain_df"].empty:
            st.bar_chart(data["domain_df"].set_index("Domain"))
        else:
            st.warning("Not enough domain data to plot.")
            
    with col_recs:
        st.markdown("### 🎯 AI Recommendations")
        st.markdown(
            """
            <div style="background: var(--surface); padding: 16px; border-radius: 8px; border: 1px solid var(--border);">
                <p style="margin:0; font-size: 0.9rem; color: var(--text-muted);">RECOMMENDED NEXT ACTION</p>
            """, unsafe_allow_html=True
        )
        
        if data["weakest_domain"]:
            st.markdown(f"**Focus Area:** {data['weakest_domain']}")
            st.markdown(f"Your accuracy in this domain is currently **{data['lowest_acc']:.1f}%**. To maximize your score increase, prioritize practice in this area.")
            st.button(f"Start {data['weakest_domain']} Drill", type="primary", use_container_width=True)
        else:
            st.markdown("**Maintain Consistency**")
            st.markdown("Your accuracy is balanced across all domains. Continue taking full-length adaptive simulations to build stamina.")
            st.button("Start Full Simulation", type="primary", use_container_width=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
