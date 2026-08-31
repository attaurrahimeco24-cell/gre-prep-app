import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import gre_platform_merged as db_manager
from modules import question_engine, testing_engine
from ui import components, test_views, dashboard_views

st.set_page_config(page_title="GRE AI Prep Platform", layout="wide", initial_sidebar_state="expanded")
components.apply_gre_theme()

@st.cache_resource
def setup_database():
    db_manager.initialize_database()
    question_engine.seed_initial_question_bank()

setup_database()

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Home"
if "active_test_id" not in st.session_state:
    st.session_state["active_test_id"] = None

st.sidebar.title("🎓 GRE AI Prep Platform")

# --- Control Panel for Reseeding ---
with st.sidebar.expander("⚙️ Admin Settings", expanded=False):
    if st.button("🔄 Force Reset & Re-seed Questions", use_container_width=True):
        question_engine.seed_initial_question_bank(force_reset=True)
        st.session_state["active_test_id"] = None
        st.session_state["active_page"] = "Home"
        st.toast("Database reset! New question bank loaded.", icon="✅")
        st.rerun()

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Full GRE Simulation", "Analytics Dashboard"],
    index=["Home", "Full GRE Simulation", "Analytics Dashboard"].index(st.session_state["active_page"])
)
st.session_state["active_page"] = page

if page == "Home":
    st.title("GRE Exam Engine & Testing Center")
    st.markdown("Simulating the official 2026 shorter GRE General Test format.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Full GRE Simulation", type="primary", use_container_width=True):
            test_data = testing_engine.initialize_test_session("full_length")
            st.session_state["active_test_id"] = test_data["test_id"]
            st.session_state["active_page"] = "Full GRE Simulation"
            st.rerun()
    with col2:
        if st.button("📊 Open Analytics Dashboard", use_container_width=True):
            st.session_state["active_page"] = "Analytics Dashboard"
            st.rerun()

elif page == "Full GRE Simulation":
    if not st.session_state["active_test_id"]:
        st.warning("No active exam found. Click below to initialize a test session.")
        if st.button("Initialize Exam", type="primary"):
            test_data = testing_engine.initialize_test_session("full_length")
            st.session_state["active_test_id"] = test_data["test_id"]
            st.rerun()
    else:
        test_views.render_exam_simulation(st.session_state["active_test_id"])

elif page == "Analytics Dashboard":
    dashboard_views.render_analytics_dashboard()
