import streamlit as st
from typing import Dict, Any, Optional
from modules import timer

def apply_gre_theme() -> None:
    st.markdown(
        """
        <style>
        /* Force high contrast light background and dark text */
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
            background-color: #F8FAFC !important; 
            color: #0F172A !important; 
            font-family: 'Inter', -apple-system, sans-serif !important; 
        }

        /* Force dark font on all text elements, inputs, radios, and labels */
        h1, h2, h3, h4, h5, h6, p, span, div, label, li, strong, small,
        .stRadio label, .stTextInput label, .stTextArea label, [data-testid="stMarkdownContainer"] p {
            color: #0F172A !important;
        }

        /* Custom CBT Metric Card */
        .metric-card-box {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-left: 5px solid #2563EB !important;
            padding: 16px 20px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            margin-bottom: 12px !important;
        }
        .metric-card-label {
            font-size: 13px !important;
            font-weight: 700 !important;
            color: #475569 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        .metric-card-value {
            font-size: 30px !important;
            font-weight: 800 !important;
            color: #1E293B !important;
            margin-top: 4px !important;
        }
        .metric-card-sub {
            font-size: 12px !important;
            color: #64748B !important;
            margin-top: 4px !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }

        /* Button Enhancements */
        .stButton > button {
            border-radius: 6px !important;
            font-weight: 600 !important;
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_score_card(label: str, value: str, subtext: Optional[str] = None) -> None:
    sub_html = f"<div class='metric-card-sub'>{subtext}</div>" if subtext else ""
    st.markdown(
        f"""
        <div class="metric-card-box">
            <div class="metric-card-label">{label}</div>
            <div class="metric-card-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_cbt_header(section_name: str, section_instance_id: str, duration_seconds: int) -> Dict[str, Any]:
    time_status = timer.get_section_time_status(section_instance_id, duration_seconds)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### 📝 {section_name.replace('_', ' ').title()}")
    with col2:
        st.markdown(f"**Status:** `{time_status['status'].upper()}`")
    with col3:
        timer_color = "#DC2626" if time_status['remaining_seconds'] < 300 else "#2563EB"
        st.markdown(
            f"<div style='font-size: 24px; font-weight: 800; color: {timer_color} !important; text-align: right;'>"
            f"⏱️ {time_status['formatted_time']}</div>",
            unsafe_allow_html=True
        )
    st.divider()
    return time_status
