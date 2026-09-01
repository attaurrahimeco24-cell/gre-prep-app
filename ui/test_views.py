import time
import json
import streamlit as st
import gre_platform_merged as db_manager
from modules import testing_engine

@st.fragment(run_every="1s")
def render_isolated_timer(start_epoch: float, duration: int):
    elapsed = int(time.time() - start_epoch)
    remaining = max(0, duration - elapsed)
    mins, secs = divmod(remaining, 60)
    st.markdown(f"### ⏱️ Time Remaining: `{mins:02d}:{secs:02d}`", unsafe_allow_html=True)
    if remaining == 0:
        st.warning("Section time expired!")

def render_exam_simulation(test_id: str):
    payload = testing_engine.get_active_section_payload(test_id)
    if not payload:
        st.success("🎉 Exam session completed successfully!")
        if st.button("Return to Workspace"):
            st.session_state.pop("active_test_id", None)
            st.session_state["active_page"] = "🧭 Workspace"
            st.rerun()
        return

    st.markdown(f"## 📝 {payload['section_name']}")
    render_isolated_timer(payload["start_epoch"], payload["duration_seconds"])
    st.divider()

    if "current_q_index" not in st.session_state:
        st.session_state["current_q_index"] = 0

    q_idx = st.session_state["current_q_index"]
    questions = payload["questions"]
    if q_idx >= len(questions):
        st.session_state["current_q_index"] = 0
        q_idx = 0

    q = questions[q_idx]
    st.markdown(f"**Question {q_idx + 1} of {len(questions)}** ({q['domain']} — {q['topic']})")
    
    if q["svg_payload"]:
        st.markdown(q["svg_payload"], unsafe_allow_html=True)
        
    if "Reading Comprehension" in q["domain"] or "Text Completion" in q["domain"]:
        st.markdown(f"<div class='reading-passage'>{q['question_text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"### {q['question_text']}")

    options = json.loads(q["options_json"])
    selected_ans = st.radio("Select your answer:", options, key=f"ans_{q['question_id']}")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if q_idx > 0 and st.button("⬅️ Previous"):
            st.session_state["current_q_index"] -= 1
            st.rerun()
    with col2:
        if q_idx < len(questions) - 1 and st.button("Next ➡️"):
            with db_manager.db_transaction() as cur:
                resp_id = db_manager._new_id("RES")
                cur.execute("INSERT OR REPLACE INTO test_responses (response_id, test_id, question_id, user_answer, result) VALUES (?, ?, ?, ?, ?)",
                            (resp_id, test_id, q["question_id"], selected_ans, "correct"))
            st.session_state["current_q_index"] += 1
            st.rerun()
        elif q_idx == len(questions) - 1 and st.button("🏁 Submit Section", type="primary"):
            with db_manager.db_transaction() as cur:
                cur.execute("UPDATE session_sections SET is_completed = 1 WHERE sec_instance_id = ?", (payload["sec_instance_id"],))
                cur.execute("UPDATE tests SET status = 'completed' WHERE test_id = ?", (test_id,))
            st.session_state.pop("current_q_index", None)
            st.success("Section submitted successfully!")
            st.rerun()
