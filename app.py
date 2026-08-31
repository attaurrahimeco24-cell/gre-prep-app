import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import gre_platform_merged as db_manager
from modules import question_engine, testing_engine
from ui import components, test_views, dashboard_views, admin_views

st.set_page_config(page_title="GRE AI Prep Platform", layout="wide", initial_sidebar_state="expanded")
components.apply_gre_theme()

# --- INITIALIZATION & BOOTSTRAPPING ---
@st.cache_resource
def setup_system():
    db_manager.initialize_database()
    question_engine.seed_initial_question_bank()
    
    # Create default SUPER_ADMIN if none exists
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role = 'SUPER_ADMIN'")
        if cur.fetchone()["c"] == 0:
            try:
                db_manager.create_user("admin", "admin@greplatform.local", "admin123", "SUPER_ADMIN")
            except Exception:
                pass # Fail silently if it somehow exists

setup_system()

# --- STATE UTILITIES ---
def clear_test_state():
    keys_to_clear = [
        "active_test_id", "current_section_payload", "active_sec_instance_id", 
        "current_q_index", "user_answers", "q_start_time", "marked_for_review"
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)

def perform_logout():
    st.session_state.clear()
    st.rerun()

# --- AUTHENTICATION GATEWAY ---
if not st.session_state.get("authenticated", False):
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 3rem; font-weight: 800; color: #0F172A;">GRE AI Prep Platform</h1>
            <p style="color: #64748B;">Secure Student & Administration Portal</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔒 Secure Login", "📝 Student Registration"])
        
        with tab_login:
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Authenticate", type="primary", use_container_width=True):
                user_data = db_manager.verify_login(login_user, login_pass)
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = user_data["user_id"]
                    st.session_state["username"] = user_data["username"]
                    st.session_state["user_role"] = user_data["role"]
                    # Route based on role
                    st.session_state["active_page"] = "Home" if user_data["role"] == "STUDENT" else "Admin Dashboard"
                    st.toast(f"Welcome back, {user_data['username']}!", icon="✅")
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid username, password, or inactive account.")
                    
        with tab_register:
            reg_user = st.text_input("Choose Username", key="reg_user")
            reg_email = st.text_input("Email Address", key="reg_email")
            reg_pass = st.text_input("Choose Password", type="password", key="reg_pass")
            if st.button("Register Student Account", type="primary", use_container_width=True):
                if not reg_user or not reg_email or not reg_pass:
                    st.error("All fields are required.")
                else:
                    try:
                        db_manager.create_user(reg_user, reg_email, reg_pass, "STUDENT")
                        st.success("Account created successfully! You may now log in.")
                    except ValueError as e:
                        st.error(str(e))
    
    # SECURITY HARD-STOP: Prevent execution of protected code
    st.stop()


# ==============================================================================
# ======================== PROTECTED APPLICATION AREA ==========================
# ==============================================================================

role = st.session_state.get("user_role", "STUDENT")

# --- SIDEBAR NAVIGATION (ROLE-BASED) ---
st.sidebar.title(f"🎓 GRE Platform")
st.sidebar.markdown(f"**Logged in as:** `{st.session_state['username']}` ({role})")

if st.sidebar.button("🚪 Secure Logout", use_container_width=True):
    perform_logout()

st.sidebar.divider()

if role == "STUDENT":
    nav_options = ["Home", "Full GRE Simulation", "Analytics Dashboard"]
else:
    nav_options = [
        "Admin Dashboard", 
        "Question Bank", 
        "Test Configurations", 
        "User Management",
        "System Audit Logs"
    ]

# Safe routing fallback if switching roles via logout/login
current_page = st.session_state.get("active_page")
if current_page not in nav_options:
    current_page = nav_options[0]

page = st.sidebar.radio("Navigation", nav_options, index=nav_options.index(current_page))
st.session_state["active_page"] = page


# --- ROUTE: STUDENT VIEWS ---
if page == "Home":
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="font-size: 3.5rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">Elevate Your Future.</h1>
            <p style="font-size: 1.25rem; color: #475569; max-width: 700px; margin: 0 auto;">
                Master the modern, shortened GRE with adaptive AI algorithms, high-fidelity simulations, and deep diagnostic telemetry.
            </p>
        </div>
        """, unsafe_allow_html=True
    )
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Full GRE Simulation", type="primary", use_container_width=True):
            clear_test_state()
            test_data = testing_engine.initialize_test_session("full_length")
            st.session_state["active_test_id"] = test_data["test_id"]
            st.session_state["active_page"] = "Full GRE Simulation"
            st.rerun()
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("📊 Open Analytics Dashboard", use_container_width=True):
            st.session_state["active_page"] = "Analytics Dashboard"
            st.rerun()

elif page == "Full GRE Simulation":
    if not st.session_state.get("active_test_id"):
        st.warning("No active exam found. Return home to initialize a new test session.")
    else:
        test_views.render_exam_simulation(st.session_state["active_test_id"])

elif page == "Analytics Dashboard":
    dashboard_views.render_analytics_dashboard()

# --- ROUTE: ADMIN VIEWS (STRICTLY GUARDED) ---
elif page == "Admin Dashboard":
    if role not in ["ADMIN", "SUPER_ADMIN"]:
        st.error("Unauthorized Access Protocol Triggered.")
        st.stop()
        
    st.title("🛡️ Admin Control Center")
    st.caption("Central Platform Telemetry & System Health")
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM users")
        total_users = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM questions WHERE status = 'APPROVED'")
        total_qs = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM tests")
        total_tests = cur.fetchone()["c"]
        
    c1, c2, c3 = st.columns(3)
    with c1:
        components.render_score_card("Registered Users", str(total_users))
    with c2:
        components.render_score_card("Approved Questions", str(total_qs))
    with c3:
        components.render_score_card("Tests Administered", str(total_tests))

    st.divider()
    st.info("Additional Administrative Modules (Question Bank, Users, Logs) are now active in the sidebar.")

# NEW: Connected the Question Bank module securely
elif page == "Question Bank":
    if role not in ["ADMIN", "SUPER_ADMIN"]:
        st.error("Unauthorized Access Protocol Triggered.")
        st.stop()
    admin_views.render_question_bank()

elif page in ["Test Configurations", "User Management", "System Audit Logs"]:
    if role not in ["ADMIN", "SUPER_ADMIN"]:
        st.error("Unauthorized Access Protocol Triggered.")
        st.stop()
    st.title(f"🛠️ {page}")
    st.warning("Module under construction (Scheduled for Phase 6 & 7).")
