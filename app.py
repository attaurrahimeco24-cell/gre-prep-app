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
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM users WHERE role = 'SUPER_ADMIN'")
        if cur.fetchone()["c"] == 0:
            try:
                db_manager.create_user("admin", "admin@greplatform.local", "admin123", "SUPER_ADMIN")
            except Exception:
                pass 

setup_system()

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

# ==============================================================================
# ========================= AUTHENTICATION GATEWAY =============================
# ==============================================================================
if not st.session_state.get("authenticated", False):
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 0 2rem 0;">
            <h1 style="font-size: 2.5rem; font-weight: 800; color: var(--text-main);">GRE Platform Control Center</h1>
            <p style="color: var(--text-muted);">Secure Student & Administration Portal</p>
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
                    st.session_state["active_page"] = "🏠 Home" if user_data["role"] == "STUDENT" else "📊 Admin Dashboard"
                    st.toast(f"Welcome back, {user_data['username']}!", icon="✅")
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid credentials or inactive account.")
                    
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
    st.stop()


# ==============================================================================
# ======================== PROTECTED APPLICATION AREA ==========================
# ==============================================================================
role = st.session_state.get("user_role", "STUDENT")
admin_id = st.session_state.get("user_id", "system")

# --- HIERARCHICAL SIDEBAR NAVIGATION ---
st.sidebar.markdown(f"**User:** `{st.session_state['username']}`")
st.sidebar.markdown(f"**Role:** {components.status_badge(role)}", unsafe_allow_html=True)
st.sidebar.divider()

if role == "STUDENT":
    nav_options = ["🏠 Home", "🚀 Full GRE Simulation", "📊 Analytics Dashboard"]
else:
    nav_options = [
        "📊 Admin Dashboard", 
        "📝 Question Bank", 
        "⚙️ Test Configurations", 
        "👥 User Management",
        "🛡️ Audit & Security"
    ]

current_page = st.session_state.get("active_page")
if current_page not in nav_options:
    current_page = nav_options[0]

page = st.sidebar.radio("Navigation Menu", nav_options, index=nav_options.index(current_page), label_visibility="collapsed")
st.session_state["active_page"] = page

st.sidebar.divider()
if st.sidebar.button("🚪 Secure Logout", use_container_width=True):
    perform_logout()

# ------------------------------------------------------------------------------
# STUDENT ROUTES
# ------------------------------------------------------------------------------
if page == "🏠 Home":
    st.markdown("<div style='text-align: center; padding: 1rem 0;'><h1 style='font-weight: 800;'>Elevate Your Future.</h1><p style='color: var(--text-muted);'>Master the modern, shortened GRE with adaptive AI algorithms.</p></div>", unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Full GRE Simulation", type="primary", use_container_width=True):
            clear_test_state()
            test_data = testing_engine.initialize_test_session("full_length")
            st.session_state["active_test_id"] = test_data["test_id"]
            st.session_state["active_page"] = "🚀 Full GRE Simulation"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Open Analytics Dashboard", use_container_width=True):
            st.session_state["active_page"] = "📊 Analytics Dashboard"
            st.rerun()

elif page == "🚀 Full GRE Simulation":
    if not st.session_state.get("active_test_id"):
        st.warning("No active exam found. Return home to initialize a new test session.")
    else:
        test_views.render_exam_simulation(st.session_state["active_test_id"])

elif page == "📊 Analytics Dashboard":
    dashboard_views.render_analytics_dashboard()

# ------------------------------------------------------------------------------
# ADMIN ROUTES (STRICTLY GUARDED)
# ------------------------------------------------------------------------------
elif page == "📊 Admin Dashboard":
    if role not in ["ADMIN", "SUPER_ADMIN"]: st.stop()
        
    st.markdown("## 🛡️ Admin Control Center")
    st.caption("Central Platform Telemetry & System Health")
    
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM users")
        total_users = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM questions WHERE status = 'APPROVED'")
        total_qs = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM questions WHERE status = 'PENDING_REVIEW'")
        pending_qs = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM tests")
        total_tests = cur.fetchone()["c"]
        
    c1, c2, c3 = st.columns(3)
    with c1: components.render_score_card("Registered Users", str(total_users))
    with c2: components.render_score_card("Tests Administered", str(total_tests))
    with c3: components.render_score_card("Approved Questions", str(total_qs))

    st.markdown("### Requires Attention")
    if pending_qs > 0:
        st.warning(f"⚠️ **{pending_qs} questions** are currently awaiting administrative review and approval.")
    else:
        st.success("✓ No content currently requires administrative review.")

    st.markdown("### System Health")
    h1, h2, h3 = st.columns(3)
    with h1: st.markdown(f"**Database:** {components.status_badge('HEALTHY')}", unsafe_allow_html=True)
    with h2: st.markdown(f"**Auth Gateway:** {components.status_badge('OPERATIONAL')}", unsafe_allow_html=True)
    with h3: st.markdown(f"**Test Engine:** {components.status_badge('ACTIVE')}", unsafe_allow_html=True)

elif page == "👥 User Management":
    if role not in ["ADMIN", "SUPER_ADMIN"]: st.stop()
    admin_views.render_user_management()

elif page == "🛡️ Audit & Security":
    if role not in ["ADMIN", "SUPER_ADMIN"]: st.stop()
    admin_views.render_audit_logs()
    
    st.markdown("## ⚙️ Test Configurations")
    st.caption("Configure how simulated GRE tests are timed and adaptively routed.")
    
    current_settings = db_manager.get_all_settings()
    
    with st.form("settings_form"):
        st.markdown("### ⏱️ Global Timing Settings")
        c1, c2, c3 = st.columns(3)
        with c1:
            components.render_setting_row("Quant Duration", "Total minutes for Quant 1 & 2.")
            quant_time = st.number_input("Mins", value=int(current_settings.get("quant_time_mins", 47)), key="s_qt")
        with c2:
            components.render_setting_row("Verbal Duration", "Total minutes for Verbal 1 & 2.")
            verbal_time = st.number_input("Mins", value=int(current_settings.get("verbal_time_mins", 41)), key="s_vt")
        with c3:
            components.render_setting_row("AWA Duration", "Minutes for the Analytical Writing task.")
            aw_time = st.number_input("Mins", value=int(current_settings.get("aw_time_mins", 30)), key="s_aw")
            
        st.divider()
        st.markdown("### 🧠 Adaptive Routing Thresholds")
        st.info("These thresholds dictate when a student is routed to a Hard or Medium Section 2.")
        c4, c5 = st.columns(2)
        with c4:
            components.render_setting_row("Hard Threshold", "Accuracy required in Sec 1 to reach Hard Sec 2.")
            hard_thresh = st.slider("Percentage", 0.0, 1.0, float(current_settings.get("adaptive_threshold_hard", 0.75)), 0.01)
        with c5:
            components.render_setting_row("Medium Threshold", "Accuracy required in Sec 1 to reach Medium Sec 2.")
            med_thresh = st.slider("Percentage", 0.0, 1.0, float(current_settings.get("adaptive_threshold_medium", 0.40)), 0.01)
            
        st.divider()
        audit_reason = st.text_input("Audit Reason (Required for system log)")
        
        if st.form_submit_button("💾 Save Platform Configurations", type="primary"):
            if not audit_reason:
                st.error("🔒 Security Halt: You must provide a reason for configuration changes.")
            else:
                updates = {
                    "quant_time_mins": str(quant_time),
                    "verbal_time_mins": str(verbal_time),
                    "aw_time_mins": str(aw_time),
                    "adaptive_threshold_hard": str(hard_thresh),
                    "adaptive_threshold_medium": str(med_thresh)
                }
                db_manager.update_settings(updates, admin_id, audit_reason)
                st.success("✅ Configurations successfully updated and applied to the Test Engine.")
                st.rerun()

    components.render_danger_zone("Factory Reset", "Restoring default settings will overwrite all active configurations.")
    if st.button("Restore Default Configuration", type="primary"):
        db_manager.seed_default_settings() # Re-injects defaults
        db_manager.log_admin_action(admin_id, "FACTORY_RESET", "system_settings", reason="Manual Admin Override")
        st.toast("Settings restored to factory defaults.", icon="⚠️")
        st.rerun()

elif page in ["👥 User Management", "🛡️ Audit & Security"]:
    if role not in ["ADMIN", "SUPER_ADMIN"]: st.stop()
    st.markdown(f"## {page}")
    st.warning("Module scheduled for Phase 6 Deployment.")
