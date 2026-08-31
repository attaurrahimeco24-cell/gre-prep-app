import streamlit as st
from typing import Dict, Any, Optional
from modules import timer

def apply_gre_theme() -> None:
    st.markdown(
        """
        <style>
        /* =========================================================
           SAAS DESIGN SYSTEM TOKENS (PHASE 2)
           ========================================================= */
        :root {
            --admin-primary: #2563EB;
            --admin-primary-hover: #1D4ED8;
            --admin-success: #059669;
            --admin-success-bg: #D1FAE5;
            --admin-warning: #D97706;
            --admin-warning-bg: #FEF3C7;
            --admin-danger: #DC2626;
            --admin-danger-bg: #FEE2E2;
            --admin-info: #3B82F6;
            --admin-neutral: #64748B;
            --admin-neutral-bg: #F1F5F9;
            
            --text-main: #0F172A;
            --text-muted: #475569;
            --bg-main: #F8FAFC;
            --bg-card: #FFFFFF;
            --border-light: #E2E8F0;
        }

        /* Base App Overrides */
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
            background-color: var(--bg-main) !important; 
            color: var(--text-main) !important; 
            font-family: 'Inter', -apple-system, sans-serif !important; 
        }

        h1, h2, h3, h4, h5, h6, p, span, div, label, li, strong, small,
        .stRadio label, .stTextInput label, .stTextArea label, [data-testid="stMarkdownContainer"] p {
            color: var(--text-main) !important;
        }

        /* CBT Metric Card (Student Facing) */
        .metric-card-box {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-light) !important;
            border-left: 5px solid var(--admin-primary) !important;
            padding: 16px 20px !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02) !important;
            margin-bottom: 12px !important;
        }
        .metric-card-label {
            font-size: 12px !important;
            font-weight: 700 !important;
            color: var(--text-muted) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        .metric-card-value {
            font-size: 28px !important;
            font-weight: 800 !important;
            color: var(--text-main) !important;
            margin-top: 4px !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-card) !important;
            border-right: 1px solid var(--border-light) !important;
        }

        /* Button Enhancements */
        .stButton > button {
            border-radius: 6px !important;
            font-weight: 600 !important;
            background-color: var(--bg-card) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-light) !important;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            border-color: var(--admin-neutral) !important;
        }
        .stButton > button[kind="primary"] {
            background-color: var(--admin-primary) !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--admin-primary-hover) !important;
        }

        /* Danger Zone Styles */
        .danger-zone {
            border: 1px solid var(--admin-danger);
            border-radius: 8px;
            padding: 20px;
            background-color: var(--admin-danger-bg);
            margin-top: 20px;
        }
        
        /* Status Badges */
        .badge {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            display: inline-block;
        }
        .badge-success { background-color: var(--admin-success-bg); color: var(--admin-success); }
        .badge-warning { background-color: var(--admin-warning-bg); color: var(--admin-warning); }
        .badge-danger { background-color: var(--admin-danger-bg); color: var(--admin-danger); }
        .badge-neutral { background-color: var(--admin-neutral-bg); color: var(--admin-neutral); }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_score_card(label: str, value: str, subtext: Optional[str] = None) -> None:
    st.markdown(
        f"""
        <div class="metric-card-box">
            <div class="metric-card-label">{label}</div>
            <div class="metric-card-value">{value}</div>
            {f'<div style="font-size:12px; color:var(--text-muted); margin-top:4px;">{subtext}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

def status_badge(status: str) -> str:
    """Returns an HTML string for a semantic status badge."""
    s = status.upper()
    if s in ["APPROVED", "HEALTHY", "ACTIVE", "OPERATIONAL", "ON"]:
        css_class = "badge-success"
    elif s in ["PENDING_REVIEW", "WARNING", "DRAFT", "PENDING"]:
        css_class = "badge-warning"
    elif s in ["FAILED", "ERROR", "DISABLED", "ARCHIVED", "OFF"]:
        css_class = "badge-danger"
    else:
        css_class = "badge-neutral"
    
    return f'<span class="badge {css_class}">{s}</span>'

def render_setting_row(title: str, description: str):
    """Renders the standard SaaS setting title and description for column layouts."""
    st.markdown(
        f"""
        <div style="margin-bottom: 8px;">
            <strong style="font-size: 1.05rem; color: var(--text-main);">{title}</strong><br>
            <span style="font-size: 0.85rem; color: var(--text-muted);">{description}</span>
        </div>
        """, 
        unsafe_allow_html=True
    )

def render_danger_zone(title: str, description: str):
    """Renders a visually distinct danger zone container."""
    st.markdown(
        f"""
        <div class="danger-zone">
            <strong style="color: var(--admin-danger); font-size: 1.1rem;">⚠️ {title}</strong>
            <p style="color: #7F1D1D; font-size: 0.9rem; margin-top: 4px; margin-bottom: 0;">{description}</p>
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
