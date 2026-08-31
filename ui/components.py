import streamlit as st
from typing import Dict, Any, Optional
from modules import timer

def apply_gre_theme() -> None:
    st.markdown(
        """
        <style>
        /* Modern, high-contrast theme reset */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
            background-color: #F8FAFC !important; 
            color: #0F172A !important; 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; 
        }

        /* Global typography enforcement */
        h1, h2, h3, h4, h5, h6, p, span, div, label, li, strong, button {
            color: #0F172A !important;
        }

        /* Custom CBT Metric Card */
        .metric-card-box {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-left: 5px solid #2563EB !important;
            padding: 18px 20px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
            margin-bottom: 12px !important;
        }
        .metric-card-label {
            font-size: 13px !important;
            font-weight: 700 !important;
            color: #64748B !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 4px !important;
        }
        .metric-card-value {
            font-size: 32px !important;
            font-weight: 800 !important;
            color: #1E293B !important;
            line-height: 1.1 !important;
        }
        .metric-card-sub {
            font-size: 12px !important;
            color: #94A3B8 !important;
            margin-top: 6px !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }

        /* Styled Action Buttons */
        .stButton > button {
            border-radius: 6px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.2s ease !important;
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
