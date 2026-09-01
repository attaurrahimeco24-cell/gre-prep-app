import json
import streamlit as st
import gre_platform_merged as db
from modules import testing_engine, timer

def render_exam_simulation(test_id: str):
    payload = testing_engine.get_safe_active_section_payload(test_id)
    if not payload or st.session_state.get("section_time_expired"):
        if st.session_state.get("section_time_expired"):
            st.warning("⏱️ Section time expired! Submitting section automatically...")
            st.session_state.pop("section_time_expired", None)
            
        with db.db_transaction() as cur:
            cur.execute("UPDATE session_sections SET is_completed = 1 WHERE test_id = ? AND is_completed = 0", (test_id,))
            cur.execute("UPDATE tests SET status = 'completed' WHERE test_id = ?", (test_id,))
            
        st.success("🎉 Section completed and submitted successfully!")
        if st.button("Return to Workspace", type="primary"):
            st.session_state.pop("active_test_id", None)
            st.session_state["active_page"] = "🧭 Workspace"
            st.rerun()
        return

    st.markdown(f"## 📝 {payload['section_name']}")
    timer.render_isolated_timer(payload["start_epoch"], payload["duration_seconds"])
    st.divider()

    q_idx = st.session_state.setdefault("current_q_index", 0)
    questions = payload["questions"]
    if q_idx >= len(questions):
        q_idx = 0
        st.session_state["current_q_index"] = 0

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

    col1, col2 = st.columns([1, 1])
    with col1:
        if q_idx > 0 and st.button("⬅️ Previous Question"):
            st.session_state["current_q_index"] -= 1
            st.rerun()
    with col2:
        btn_label = "Next Question ➡️" if q_idx < len(questions) - 1 else "🏁 Submit Section"
        if st.button(btn_label, type="primary"):
            testing_engine.submit_answer_atomically(test_id, q["question_id"], selected_ans)
            if q_idx < len(questions) - 1:
                st.session_state["current_q_index"] += 1
                st.rerun()
            else:
                with db.db_transaction() as cur:
                    cur.execute("UPDATE session_sections SET is_completed = 1 WHERE sec_instance_id = ?", (payload["sec_instance_id"],))
                    cur.execute("UPDATE tests SET status = 'completed' WHERE test_id = ?", (test_id,))
                st.session_state.pop("current_q_index", None)
                st.success("Section submitted successfully!")
                st.rerun()
