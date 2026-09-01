import streamlit as st

def apply_gre_theme():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        :root {
            --primary-color: #4F46E5;
            --primary-hover: #4338CA;
            --surface: #FFFFFF;
            --background: #F8FAFC;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --border: #E2E8F0;
            --success-bg: #D1FAE5;
            --success-text: #065F46;
            --warning-bg: #FEF3C7;
            --warning-text: #92400E;
            --danger-bg: #FEE2E2;
            --danger-text: #991B1B;
            --info-bg: #E0E7FF;
            --info-text: #3730A3;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: var(--text-main);
        }

        .reading-passage {
            font-size: 1.125rem;
            line-height: 1.75;
            color: var(--text-main);
            background-color: var(--surface);
            padding: 24px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
        }

        .badge {
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-block;
        }
        .badge-success { background: var(--success-bg); color: var(--success-text); }
        .badge-warning { background: var(--warning-bg); color: var(--warning-text); }
        .badge-danger { background: var(--danger-bg); color: var(--danger-text); }
        .badge-info { background: var(--info-bg); color: var(--info-text); }

        .score-card {
            background: var(--surface);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .score-card h3 { 
            margin: 0; 
            color: var(--text-muted); 
            font-size: 0.85rem; 
            text-transform: uppercase; 
            letter-spacing: 0.08em; 
            font-weight: 600;
        }
        .score-card h1 { 
            margin: 8px 0 0 0; 
            color: var(--primary-color); 
            font-size: 2.25rem; 
            font-weight: 800; 
        }

        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
        }
        </style>
    """, unsafe_allow_html=True)

def status_badge(status: str) -> str:
    color_map = {
        "ACTIVE": "success", "APPROVED": "success", "HEALTHY": "success", "OPERATIONAL": "success", "VERIFIED": "success", "WAL_MODE_ACTIVE": "success", "ARGON2ID_SECURED": "success",
        "PENDING_REVIEW": "warning", "SUSPENDED": "warning", "PENDING": "warning",
        "ARCHIVED": "info", "DRAFT": "info"
    }
    b_class = color_map.get(status.upper(), "info")
    return f'<span class="badge badge-{b_class}" role="status">{status}</span>'

def render_score_card(title: str, value: str):
    st.markdown(f'<div class="score-card"><h3>{title}</h3><h1>{value}</h1></div>', unsafe_allow_html=True)

def render_setting_row(title: str, description: str):
    st.markdown(f"**{title}**<br><span style='color:var(--text-muted);font-size:0.9rem;'>{description}</span>", unsafe_allow_html=True)

def render_danger_zone(title: str, description: str):
    st.markdown("---")
    st.markdown(f"### 🚨 Danger Zone")
    st.error(f"**{title}:** {description}")
