import streamlit as st

def apply_gre_theme():
    st.markdown("""
        <style>
        :root {
            --primary-color: #4F46E5;
            --surface: #FFFFFF;
            --background: #F8FAFC;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --border: #E2E8F0;
        }
        
        .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-success { background: #D1FAE5; color: #065F46; }
        .badge-warning { background: #FEF3C7; color: #92400E; }
        .badge-danger { background: #FEE2E2; color: #991B1B; }
        .badge-info { background: #E0E7FF; color: #3730A3; }
        
        .score-card {
            background: var(--surface);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            text-align: center;
        }
        .score-card h3 { margin: 0; color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .score-card h1 { margin: 8px 0 0 0; color: var(--primary-color); font-size: 2.5rem; font-weight: 800; }
        </style>
    """, unsafe_allow_html=True)

def status_badge(status: str) -> str:
    color_map = {
        "ACTIVE": "success", "APPROVED": "success", "HEALTHY": "success", "OPERATIONAL": "success", "VERIFIED": "success",
        "PENDING_REVIEW": "warning", "SUSPENDED": "warning", "PENDING": "warning",
        "ARCHIVED": "info", "DRAFT": "info"
    }
    b_class = color_map.get(status.upper(), "info")
    return f'<span class="badge badge-{b_class}">{status}</span>'

def render_score_card(title: str, value: str):
    st.markdown(f'<div class="score-card"><h3>{title}</h3><h1>{value}</h1></div>', unsafe_allow_html=True)

def render_setting_row(title: str, description: str):
    st.markdown(f"**{title}**<br><span style='color:var(--text-muted);font-size:0.9rem;'>{description}</span>", unsafe_allow_html=True)

def render_danger_zone(title: str, description: str):
    st.markdown("---")
    st.markdown(f"### 🚨 Danger Zone")
    st.error(f"**{title}:** {description}")
