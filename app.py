import os
import sys

# Tell the server to look in the root folder for modules
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

st.sidebar.title("GRE AI Prep")
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Full GRE Simulation", "Analytics Dashboard"],
    index=["Home", "Full GRE Simulation", "Analytics Dashboard"].index(st.session_state["active_page"])
)
st.session_state["active_page"] = page

if page == "Home":
    st.title("GRE Testing Engine")
    st.markdown("This platform simulates the 2026 shorter GRE General Test format.")
    
    if st.button("Start Full GRE Simulation", type="primary"):
        test_data = testing_engine.initialize_test_session("full_length")
        st.session_state["active_test_id"] = test_data["test_id"]
        st.session_state["active_page"] = "Full GRE Simulation"
        st.rerun()

elif page == "Full GRE Simulation":
    if not st.session_state["active_test_id"]:
        st.warning("No active test. Return to Home to start.")
    else:
        test_views.render_exam_simulation(st.session_state["active_test_id"])

elif page == "Analytics Dashboard":
    dashboard_views.render_analytics_dashboard()
