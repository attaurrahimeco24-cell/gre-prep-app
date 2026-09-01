import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import gre_platform_merged as db
from modules import email_service, question_engine, testing_engine
from ui import components, dashboard_views, test_views, admin_views

st.set_page_config(page_title="GRE Enterprise Platform", layout="wide", initial_sidebar_state="expanded")
components.apply_gre_design_system()

def bootstrap_system():
    db.initialize_database()
    question_engine.seed_initial_question_bank()
    
    with db.db_transaction() as cur:
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role = 'SUPER_ADMIN'")
        if cur.fetchone()["c"] == 0:
            try:
                db.create_user_account("admin", "admin@greplatform.local", "admin123", "SUPER_ADMIN", is_verified=1)
            except Exception:
                pass

bootstrap_system()

def perform_logout():
    st.session_state.clear()
    st.rerun()

# --- EMAIL VERIFICATION TOKEN ROUTER ---
query_params = st.query_params
if "verify" in query_params:
    raw_token = query_params["verify"]
    res = email_service.verify_email_token(raw_token)
    try:
        del st.query_params["verify"]
    except Exception:
        pass
        
    if res["status"] == "valid":
        st.session_state["verification_success"] = True
    elif res["status"] == "expired":
        st.error("❌ Verification link has expired. Please log in to request a new one.")
    elif res["status"] == "invalid":
        st.error("❌ Invalid verification token.")

if st.session_state.get("verification_success"):
    st.success("✅ Email verified successfully! Your account is now active. Please log in below.")
    st.session_state.pop("verification_success", None)

# --- AUTHENTICATION GATEWAY ---
if not st.session_state.get("authenticated", False):
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; font-weight: 800; color: #0F172A;">GRE Enterprise Platform</h1>
            <p style="color: #64748B;">Secure Student & Administrative Assessment Portal</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔐 Secure Login", "📝 Create Account"])
        
        with tab_login:
            login_user = st.text_input("Username or Email", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Authenticate", type="primary", use_container_width=True):
                try:
                    user_data = db.verify_login_credentials(login_user, login_pass)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = user_data["user_id"]
                        st.session_state["username"] = user_data["username"]
                        st.session_state["user_role"] = user_data["role"]
                        st.session_state["is_verified"] = user_data["is_verified"]
                        st.session_state["active_page"] = "🧭 Workspace" if user_data["role"] == "STUDENT" else "🎛️ Command Center"
                        st.rerun()
                    else:
                        st.error("Authentication failed. Invalid credentials.")
                except ValueError as e:
                    st.error(str(e))
                    
        with tab_register:
            reg_user = st.text_input("Choose Username", key="reg_user")
            reg_email = st.text_input("Email Address", key="reg_email")
            reg_pass = st.text_input("Choose Secure Password", type="password", key="reg_pass")
            if st.button("Register Account", type="primary", use_container_width=True):
                if not reg_user or not reg_email or not reg_pass:
                    st.error("All fields are required.")
                else:
                    try:
                        uid = db.create_user_account(reg_user, reg_email, reg_pass, "STUDENT", is_verified=0)
                        email_service.send_verification_email(uid, reg_email, reg_user)
                        st.success("✅ Account created successfully! Please check your email for verification.")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")
    st.stop()

# --- UNVERIFIED ACCOUNT WALL ---
if not st.session_state.get("is_verified", False):
    st.markdown(
        """
        <div style='text-align: center; padding: 4rem 0 2rem 0;'>
            <h1 style='color: #4F46E5; font-weight: 800;'>✉️ Email Verification Required</h1>
            <p style='color: #64748B; font-size: 1.1rem;'>Account security requires a verified email address.</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    uid = st.session_state["user_id"]
    with db.get_db_connection() as conn:
        email_addr = conn.execute("SELECT email FROM users WHERE user_id = ?", (uid,)).fetchone()[0]
        
    _, col_w, _ = st.columns([1, 2, 1])
    with col_w:
        st.info(f"Verification link sent to **{email_addr}**.")
        if st.button("🔧 INSTANTLY VERIFY (Dev Mode Bypass)", type="primary", use_container_width=True):
            with db.db_transaction() as cur:
                cur.execute("UPDATE users SET is_verified = 1 WHERE user_id = ?", (uid,))
            st.session_state["is_verified"] = True
            st.success("Verified! Rerunning...")
            time.sleep(1)
            st.rerun()
        if st.button("Logout", use_container_width=True):
            perform_logout()
    st.stop()

# --- PROTECTED APP ROUTING (`st.navigation` & `st.Page`) ---
role = st.session_state.get("user_role", "STUDENT")

st.sidebar.markdown(f"**User:** `{st.session_state['username']}`")
st.sidebar.markdown(f"**Access:** {components.render_status_badge(role)}", unsafe_allow_html=True)
st.sidebar.divider()

if role == "STUDENT":
    pages = [
        st.Page("ui/workspace.py" if os.path.exists("ui/workspace.py") else "app.py", title="🧭 Workspace", default=True),
        st.Page("ui/exam.py" if os.path.exists("ui/exam.py") else "app.py", title="⏱️ Exam Simulator"),
        st.Page("ui/analytics.py" if os.path.exists("ui/analytics.py") else "app.py", title="📈 Analytics")
    ]
else:
    pages = [
        st.Page("ui/admin.py" if os.path.exists("ui/admin.py") else "app.py", title="🎛️ Command Center", default=True),
        st.Page("ui/logs.py" if os.path.exists("ui/logs.py") else "app.py", title="🔐 Audit Logs")
    ]

# Fallback manual navigation selector if running single-file router state
nav_options = ["🧭 Workspace", "⏱️ Exam Simulator", "📈 Analytics"] if role == "STUDENT" else ["🎛️ Command Center", "🔐 Audit Logs"]
current_page = st.session_state.get("active_page", nav_options[0])
page = st.sidebar.radio("Navigation", nav_options, index=nav_options.index(current_page) if current_page in nav_options else 0, label_visibility="collapsed")
st.session_state["active_page"] = page

st.sidebar.divider()
if st.sidebar.button("🚪 Secure Logout", use_container_width=True):
    perform_logout()

# --- VIEW RENDERERS ---
if page == "🧭 Workspace":
    st.markdown("<div style='text-align: center; padding: 1rem 0;'><h1 style='font-weight: 800;'>Elevate Your Future.</h1><p style='color: #64748B;'>Master the modern, shortened GRE with adaptive AI algorithms.</p></div>", unsafe_allow_html=True)
    st.divider()
    _, c_mid, _ = st.columns([1, 2, 1])
    with c_mid:
        if st.button("🚀 Start Full GRE Simulation", type="primary", use_container_width=True):
            test_id = testing_engine.initialize_test_session(st.session_state["user_id"], "full_length")
            st.session_state["active_test_id"] = test_id
            st.session_state["active_page"] = "⏱️ Exam Simulator"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📈 Open Analytics Dashboard", use_container_width=True):
            st.session_state["active_page"] = "📈 Analytics"
            st.rerun()

elif page == "⏱️ Exam Simulator":
    if not st.session_state.get("active_test_id"):
        st.warning("No active test session found. Initialize a test from your workspace.")
    else:
        test_views.render_exam_simulation(st.session_state["active_test_id"])

elif page == "📈 Analytics":
    dashboard_views.render_analytics_dashboard()

elif page == "🎛️ Command Center":
    admin_views.render_command_center()

elif page == "🔐 Audit Logs":
    admin_views.render_audit_logs()
