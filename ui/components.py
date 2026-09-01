import streamlit as st

def apply_gre_design_system():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            color: #0F172A;
        }

        .reading-passage {
            font-size: 1.125rem;
            line-height: 1.75;
            color: #0F172A;
            background-color: #F8FAFC;
            padding: 24px;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
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
        .badge-success { background: #D1FAE5; color: #065F46; }
        .badge-warning { background: #FEF3C7; color: #92400E; }
        .badge-danger { background: #FEE2E2; color: #991B1B; }
        .badge-info { background: #E0E7FF; color: #3730A3; }

        .score-card {
            background: #FFFFFF;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .score-card h3 { 
            margin: 0; 
            color: #64748B; 
            font-size: 0.85rem; 
            text-transform: uppercase; 
            letter-spacing: 0.08em; 
            font-weight: 600;
        }
        .score-card h1 { 
            margin: 8px 0 0 0; 
            color: #4F46E5; 
            font-size: 2.25rem; 
            font-weight: 800; 
        }

        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_status_badge(status: str) -> str:
    color_map = {
        "ACTIVE": "success", "APPROVED": "success", "HEALTHY": "success", "OPERATIONAL": "success", "VERIFIED": "success", "STUDENT": "success",
        "PENDING_REVIEW": "warning", "SUSPENDED": "warning", "PENDING": "warning",
        "ARCHIVED": "info", "ADMIN": "danger", "SUPER_ADMIN": "danger"
    }
    b_class = color_map.get(status.upper(), "info")
    return f'<span class="badge badge-{b_class}" role="status">{status}</span>'

def render_score_card(title: str, value: str):
    st.markdown(f'<div class="score-card"><h3>{title}</h3><h1>{value}</h1></div>', unsafe_allow_html=True)
