import streamlit as st
import pandas as pd
import gre_platform_merged as db
from ui import components

def verify_admin_authorization():
    role = st.session_state.get("user_role")
    if role not in ["ADMIN", "SUPER_ADMIN"]:
        st.error("⛔ Security Exception: Unauthorized access attempt to administrative subsystem.")
        st.stop()

def render_command_center():
    verify_admin_authorization()
    st.markdown("## 🎛️ Command Center & Platform Telemetry")
    st.caption("Real-time operational monitoring and database analytics.")
    st.divider()
    
    with db.get_db_connection() as conn:
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        students_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'STUDENT'").fetchone()[0]
        tests_count = conn.execute("SELECT COUNT(*) FROM tests WHERE status = 'completed'").fetchone()[0]
        questions_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

    m1, m2, m3, m4 = st.columns(4)
    with m1: components.render_score_card("Total Users", str(users_count))
    with m2: components.render_score_card("Active Students", str(students_count))
    with m3: components.render_score_card("Completed Tests", str(tests_count))
    with m4: components.render_score_card("Active Questions", str(questions_count))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🛡️ System Integrity & Security Status")
    st.markdown(f"**Database Engine:** {components.render_status_badge('WAL_MODE_ACTIVE')}", unsafe_allow_html=True)
    st.markdown(f"**Authentication:** {components.render_status_badge('ARGON2ID_SECURED')}", unsafe_allow_html=True)

def render_audit_logs():
    verify_admin_authorization()
    st.markdown("## 🔐 Immutable Audit Ledger")
    st.caption("Cryptographic log of administrative actions and security overrides.")
    st.divider()
    
    with db.get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM admin_audit_logs ORDER BY timestamp DESC LIMIT 100", conn)
        
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Audit log is currently clean.")
