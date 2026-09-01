import time
import streamlit as st

@st.fragment(run_every="1s")
def render_isolated_timer(start_epoch: float, duration_seconds: int):
    """
    Renders an isolated countdown timer widget using Streamlit fragments.
    Updates every 1 second without triggering a full-page parent rerun.
    """
    elapsed = int(time.time() - start_epoch)
    remaining = max(0, duration_seconds - elapsed)
    mins, secs = divmod(remaining, 60)
    
    st.markdown(
        f"""
        <div style="background: #FFFFFF; padding: 12px 20px; border-radius: 8px; border: 1px solid #E2E8F0; display: inline-block; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #4F46E5;">
                ⏱️ Time Remaining: {mins:02d}:{secs:02d}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if remaining == 0:
        st.session_state["section_time_expired"] = True
