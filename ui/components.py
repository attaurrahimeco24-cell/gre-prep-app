import streamlit as st
from typing import Dict, Any, Optional
from modules import timer

def apply_gre_theme() -> None:
    st.markdown(
        """
        <style>
        /* Force light background and dark text */
        .stApp, .stApp > header, .stApp [data-testid="stAppViewContainer"] { 
            background-color: #f8f9fa !important; 
            color: #212529 !important; 
            font-family: 'Segoe UI', sans-serif; 
        }
        h1, h2, h3, h4, h5, h6, p, span, div, label, li {
            color: #212529 !important;
        }
        .metric-card {
            background-color: #ffffff; border: 1px solid #e0e0e0;
            border-left: 5px solid #1e3d59; padding: 15px; border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px;
        }
        .metric-value { font-size: 28px; font-weight: bold; color: #1e3d59 !important; }
        .metric-label { font-size: 14px; color: #666666 !important; text-transform: uppercase; }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_score_card(label: str, value: str, subtext: Optional[str] = None) -> None:
    sub_html = f"<div style='font-size: 12px; color: #888888 !important;'>{subtext}</div>" if subtext else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_cbt_header(section_name: str, section_instance_id: str, duration_seconds: int) -> Dict[str, Any]:
    time_status = timer.get_section_time_status(section_instance_id, duration_seconds)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### {section_name.replace('_', ' ').title()}")
    with col2:
        st.markdown(f"**Status:** {time_status['status'].upper()}")
    with col3:
        timer_color = "#dc3545" if time_status['remaining_seconds'] < 300 else "#1e3d59"
        st.markdown(
            f"<div style='font-size: 22px; font-weight: bold; color: {timer_color} !important; text-align: right;'>"
            f"{time_status['formatted_time']}</div>",
            unsafe_allow_html=True
        )
    st.divider()
    return time_status
