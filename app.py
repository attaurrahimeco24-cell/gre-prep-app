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

# --- STATE MANAGEMENT UTILITIES ---
def clear_test_state():
    """Wipes all ephemeral test data from memory to prevent test-bleeding."""
    keys_to_clear = [
        "active_test_id", "current_section_payload", "active_sec_instance_id", 
        "current_q_index", "user_answers", "q_start_time", "marked_for_review"
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Home"
if "active_test_id" not in st.session_state:
    st.session_state["active_test_id"] = None

st.sidebar.title("🎓 GRE AI Prep Platform")

# --- Control Panel for Reseeding ---
with st.sidebar.expander("⚙️ Admin Settings", expanded=False):
    if st.button("🔄 Force Reset & Re-seed", use_container_width=True):
        question_engine.seed_initial_question_bank(force_reset=True)
        clear_test_state()
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
    # --- HERO SECTION ---
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="font-size: 3.5rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; margin-bottom: 0.5rem;">
                Elevate Your Future.
            </h1>
            <p style="font-size: 1.25rem; color: #475569; max-width: 700px; margin: 0 auto; line-height: 1.6;">
                Master the modern, shortened GRE with adaptive AI algorithms, high-fidelity simulations, and deep diagnostic telemetry.
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    # --- ECONOMIST QUOTATION BLOCK ---
    st.markdown(
        """
        <div style="background-color: #FFFFFF; border-left: 5px solid #2563EB; padding: 24px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin: 2rem auto; max-width: 800px;">
            <p style="font-size: 1.1rem; color: #334155; font-style: italic; margin-bottom: 12px; line-height: 1.7;">
                "Human capital is by far the most important form of capital in creating wealth and growth. The most valuable of all capital is that invested in human beings."
            </p>
            <p style="font-size: 0.95rem; font-weight: 700; color: #0F172A; margin: 0;">
                — Gary S. Becker
            </p>
            <p style="font-size: 0.85rem; color: #64748B; margin: 0;">
                Nobel Laureate in Economic Sciences, Pioneer of Human Capital Theory
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    st.divider()

    # --- FEATURE HIGHLIGHTS ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown("### 🧠 Adaptive Engine")
        st.markdown("<p style='color: #475569;'>Dynamic difficulty scaling based on your section performance, mirroring the exact ETS algorithm to ensure realistic score projections.</p>", unsafe_allow_html=True)
    with col_f2:
        st.markdown("### ⏱️ Realistic Pacing")
        st.markdown("<p style='color: #475569;'>Strict CBT (Computer-Based Test) timers, interface constraints, and flow logic designed to build your cognitive stamina for test day.</p>", unsafe_allow_html=True)
    with col_f3:
        st.markdown("### 📊 Micro-Analytics")
        st.markdown("<p style='color: #475569;'>Track topic-level mastery, measure speed-vs-accuracy trade-offs, and eliminate behavioral traps before you sit for the real exam.</p>", unsafe_allow_html=True)
    
    st.divider()

    # --- CENTERED ACTION BUTTONS ---
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Full GRE Simulation", type="primary", use_container_width=True):
            clear_test_state() # Ensure memory is wiped before starting
            test_data = testing_engine.initialize_test_session("full_length")
            st.session_state["active_test_id"] = test_data["test_id"]
            st.session_state["active_page"] = "Full GRE Simulation"
            st.rerun()
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if st.button("📊 Open Analytics Dashboard", use_container_width=True):
            st.session_state["active_page"] = "Analytics Dashboard"
            st.rerun()

elif page == "Full GRE Simulation":
    if not st.session_state["active_test_id"]:
        st.warning("No active exam found. Return home to initialize a new test session.")
        if st.button("Initialize Exam", type="primary"):
            clear_test_state()
            test_data = testing_engine.initialize_test_session("full_length")
            st.session_state["active_test_id"] = test_data["test_id"]
            st.rerun()
    else:
        test_views.render_exam_simulation(st.session_state["active_test_id"])

elif page == "Analytics Dashboard":
    dashboard_views.render_analytics_dashboard()
