import streamlit as st
from typing import Dict, Any, Optional
from modules import timer

def apply_gre_theme() -> None:
    st.markdown(
        """
        <style>
        /* =========================================================
           PREMIUM ADAPTIVE UI SYSTEM (Fixes Invisible Text Bug)
           ========================================================= */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* Adaptive Premium Cards */
        .saas-card {
            background: var(--background-color);
            border: 1px solid var(--secondary-background-color);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .saas-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }
        
        .metric-value {
            font-size: 2.25rem;
            font-weight: 800;
            color: var(--primary-color);
            line-height: 1.2;
            margin-top: 8px;
        }
        .metric-label {
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            opacity: 0.7;
        }

        /* Adaptive Buttons */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s !important;
        }
        
        /* Adaptive Badges (Uses transparency so it looks good in Dark/Light mode) */
        .badge {
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.025em;
            display: inline-block;
        }
        .badge-success { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-warning { background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-danger { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-neutral { background: rgba(100, 116, 139, 0.15); color: #64748B; border: 1px solid rgba(100, 116, 139, 0.3); }
        
        /* Adaptive Danger Zone */
        .danger-zone {
            border: 1px solid rgba(239, 68, 68, 0.5);
            background-color: rgba(239, 68, 68, 0.05);
            border-radius: 12px;
            padding: 24px;
            margin-top: 32px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_score_card(label: str, value: str, subtext: Optional[str] = None) -> None:
    st.markdown(
        f"""
        <div class="saas-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<div style="font-size:0.875rem; opacity:0.7; margin-top:8px; font-weight:500;">{subtext}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

def status_badge(status: str) -> str:
    s = status.upper()
    css_class = "badge-success" if s in ["APPROVED", "HEALTHY", "ACTIVE", "ON"] else \
                "badge-warning" if s in ["PENDING_REVIEW", "WARNING", "DRAFT", "PENDING"] else \
                "badge-danger" if s in ["FAILED", "ERROR", "DISABLED", "ARCHIVED", "OFF", "SUSPENDED"] else "badge-neutral"
    return f'<span class="badge {css_class}">{s}</span>'

def render_setting_row(title: str, description: str):
    st.markdown(
        f"""
        <div style="margin-bottom: 4px;">
            <div style="font-size: 1rem; font-weight: 600;">{title}</div>
            <div style="font-size: 0.875rem; opacity: 0.7; line-height: 1.4;">{description}</div>
        </div>
        """, unsafe_allow_html=True
    )

def render_danger_zone(title: str, description: str):
    st.markdown(
        f"""
        <div class="danger-zone">
            <h4 style="color: #EF4444; margin: 0 0 8px 0; font-weight: 700;">⚠️ {title}</h4>
            <p style="color: #EF4444; opacity: 0.9; margin: 0; font-size: 0.9rem;">{description}</p>
        </div>
        """, unsafe_allow_html=True
    )

def render_cbt_header(section_name: str, section_instance_id: str, duration_seconds: int) -> Dict[str, Any]:
    time_status = timer.get_section_time_status(section_instance_id, duration_seconds)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown(f"### 📝 {section_name.replace('_', ' ').title()}")
    with col2: st.markdown(f"**Status:** {status_badge(time_status['status'])}", unsafe_allow_html=True)
    with col3:
        timer_color = "#EF4444" if time_status['remaining_seconds'] < 300 else "var(--primary-color)"
        st.markdown(f"<div style='font-size: 24px; font-weight: 800; color: {timer_color} !important; text-align: right;'>⏱️ {time_status['formatted_time']}</div>", unsafe_allow_html=True)
    st.divider()
    return time_status
