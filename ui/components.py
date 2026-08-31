import streamlit as st
from typing import Dict, Any, Optional
from modules import timer

def apply_gre_theme() -> None:
    st.markdown(
        """
        <style>
        /* =========================================================
           PREMIUM SAAS DESIGN SYSTEM 
           ========================================================= */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --primary: #4F46E5; /* Indigo 600 */
            --primary-hover: #4338CA;
            --surface: #FFFFFF;
            --background: #F8FAFC; /* Slate 50 */
            --border: #E2E8F0;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
        }

        /* Global Typography & Background */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: var(--background) !important;
            color: var(--text-main) !important;
        }

        /* Top Header Cleanup */
        header[data-testid="stHeader"] {
            background-color: rgba(248, 250, 252, 0.8) !important;
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
        }

        /* Sidebar - Sleek Dark Mode */
        section[data-testid="stSidebar"] {
            background-color: #0F172A !important; /* Slate 900 */
            border-right: 1px solid #1E293B !important;
        }
        section[data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }
        
        /* Premium Cards */
        .saas-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .saas-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
        }
        
        /* Dashboard Metrics */
        .metric-value {
            font-size: 2.25rem;
            font-weight: 800;
            color: var(--primary);
            line-height: 1.2;
            margin-top: 8px;
        }
        .metric-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Streamlit Widget Overrides for Premium Feel */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s !important;
        }
        .stButton > button[kind="primary"] {
            background-color: var(--primary) !important;
            color: white !important;
            border: none !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--primary-hover) !important;
            transform: translateY(-1px);
        }
        
        /* Settings Inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            border-radius: 8px !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        }

        /* DataFrames / Tables */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }

        /* Badges */
        .badge {
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.025em;
            display: inline-block;
        }
        .badge-success { background: #D1FAE5; color: #065F46; }
        .badge-warning { background: #FEF3C7; color: #92400E; }
        .badge-danger { background: #FEE2E2; color: #991B1B; }
        .badge-neutral { background: #F1F5F9; color: #475569; }
        
        /* Danger Zone */
        .danger-zone {
            border: 1px solid #F87171;
            background-color: #FEF2F2;
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
            {f'<div style="font-size:0.875rem; color:var(--text-muted); margin-top:8px; font-weight:500;">{subtext}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

def status_badge(status: str) -> str:
    s = status.upper()
    css_class = "badge-success" if s in ["APPROVED", "HEALTHY", "ACTIVE", "ON"] else \
                "badge-warning" if s in ["PENDING_REVIEW", "WARNING", "DRAFT"] else \
                "badge-danger" if s in ["FAILED", "ERROR", "DISABLED", "ARCHIVED", "OFF"] else "badge-neutral"
    return f'<span class="badge {css_class}">{s}</span>'

def render_setting_row(title: str, description: str):
    st.markdown(
        f"""
        <div style="margin-bottom: 4px;">
            <div style="font-size: 1rem; font-weight: 600; color: var(--text-main);">{title}</div>
            <div style="font-size: 0.875rem; color: var(--text-muted); line-height: 1.4;">{description}</div>
        </div>
        """, unsafe_allow_html=True
    )

def render_danger_zone(title: str, description: str):
    st.markdown(
        f"""
        <div class="danger-zone">
            <h4 style="color: #991B1B; margin: 0 0 8px 0; font-weight: 700;">⚠️ {title}</h4>
            <p style="color: #991B1B; margin: 0; font-size: 0.9rem;">{description}</p>
        </div>
        """, unsafe_allow_html=True
    )

def render_cbt_header(section_name: str, section_instance_id: str, duration_seconds: int) -> Dict[str, Any]:
    time_status = timer.get_section_time_status(section_instance_id, duration_seconds)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown(f"### 📝 {section_name.replace('_', ' ').title()}")
    with col2: st.markdown(f"**Status:** `{time_status['status'].upper()}`")
    with col3:
        timer_color = "#DC2626" if time_status['remaining_seconds'] < 300 else "#4F46E5"
        st.markdown(f"<div style='font-size: 24px; font-weight: 800; color: {timer_color} !important; text-align: right;'>⏱️ {time_status['formatted_time']}</div>", unsafe_allow_html=True)
    st.divider()
    return time_status
