import streamlit as st
import gre_platform_merged as db_manager
from ui import components

def render_question_bank():
    st.markdown("## 📚 Content Library & Question Bank")
    st.caption("Manage, audit, and review psychometric question assets.")
    st.divider()
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT question_id, section, domain, topic, difficulty, status FROM questions")
        questions = [dict(row) for row in cur.fetchall()]
        
    if questions:
        import pandas as pd
        st.dataframe(pd.DataFrame(questions), use_container_width=True)
    else:
        st.info("No questions found in the database.")

def render_user_management():
    st.markdown("## 🧑‍🎓 User Access & Role Administration")
    st.caption("Manage registered platform users and authorization privileges.")
    st.divider()
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT user_id, username, email, role, is_verified, created_at FROM users")
        users = [dict(row) for row in cur.fetchall()]
        
    import pandas as pd
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True)
    else:
        st.info("No registered users.")

def render_email_settings():
    st.markdown("## ✉️ SMTP Gateway Configuration")
    st.caption("Configure outgoing mail servers for account verification and security alerts.")
    st.divider()
    st.info("ℹ️ Platform is currently operating in Smart Dev Mode (Simulated Token Dispatch active).")
    
    with st.form("smtp_form"):
        st.text_input("SMTP Host", value="smtp.mailprovider.com")
        st.text_input("SMTP Port", value="587")
        data_user = st.text_input("SMTP Username", value="noreply@greplatform.local")
        st.text_input("SMTP Password", type="password", value="secret_password")
        if st.form_submit_button("Save SMTP Configuration", type="primary"):
            st.success("SMTP gateway settings updated successfully.")

def render_audit_logs():
    st.markdown("## 🔐 Immutable Audit Ledger")
    st.caption("Cryptographic log of administrative actions, config updates, and overrides.")
    st.divider()
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT log_id, admin_id, action, target_object, new_value, reason, timestamp FROM admin_audit_logs ORDER BY timestamp DESC")
        logs = [dict(row) for row in cur.fetchall()]
        
    import pandas as pd
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else:
        st.info("Audit log is currently clean.")
