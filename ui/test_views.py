import time
import streamlit as st
from modules import testing_engine, timer
from ui import components

def render_exam_simulation(test_id: str) -> None:
    sec_info = testing_engine.get_active_section_info(test_id)
    if not sec_info:
        st.success("Examination Completed!")
        if st.button("Return to Home", type="primary"):
            st.session_state["active_page"] = "Home"
            st.session_state["active_test_id"] = None
            st.rerun()
        return

    sec_instance_id = sec_info["section_instance_id"]
    
    if "current_section_payload" not in st.session_state or st.session_state.get("active_sec_instance_id") != sec_instance_id:
        payload = testing_engine.start_active_section(sec_instance_id)
        st.session_state["current_section_payload"] = payload
        st.session_state["active_sec_instance_id"] = sec_instance_id
        st.session_state["current_q_index"] = 0
        st.session_state["user_answers"] = {}
        st.session_state["q_start_time"] = time.time()

    payload = st.session_state["current_section_payload"]
    questions = payload["questions"]
    
    if not questions:
        st.error("No questions available for this section.")
        return
        
    q_index = st.session_state.get("current_q_index", 0)
    current_q = questions[q_index]

    time_status = components.render_cbt_header(payload["section_name"], sec_instance_id, payload["duration_seconds"])
    
    if time_status["is_expired"]:
        st.warning("Time expired for this section! Auto-submitting...")
        testing_engine.complete_section_and_adapt(test_id, sec_instance_id)
        st.session_state.pop("current_section_payload", None)
        st.rerun()

    with st.sidebar:
        st.markdown("### Question Palette")
        cols = st.columns(4)
        for idx, q in enumerate(questions):
            col_idx = idx % 4
            qid = q["question_id"]
            btn_type = "primary" if idx == q_index else "secondary"
            if cols[col_idx].button(str(idx + 1), key=f"nav_{qid}", type=btn_type):
                st.session_state["current_q_index"] = idx
                st.session_state["q_start_time"] = time.time()
                st.rerun()

    st.markdown(f"**Question {q_index + 1} of {len(questions)}**")
    st.markdown(f"#### {current_q['question_text']}")

    q_type = current_q.get("question_type", "Multiple Choice")
    q_id = current_q["question_id"]
    existing_ans = st.session_state["user_answers"].get(q_id, "")
    selected_ans = None

    # Fix: Route input types correctly based on the GRE question type
    if q_type == "Numeric Entry":
        selected_ans = st.text_input("Enter your numerical answer:", value=existing_ans)
    elif q_type == "Issue Task":
        selected_ans = st.text_area("Write your essay response here:", value=existing_ans, height=400)
    else:
        # Fallback to empty list if options is explicitly set to None in the DB
        options = current_q.get("options") or ["A", "B", "C", "D"]
        idx_val = options.index(existing_ans) if existing_ans in options else 0
        selected_ans = st.radio("Select Choice:", options, index=idx_val if existing_ans else None)

    st.divider()
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    
    if c1.button("Previous", disabled=(q_index == 0)):
        _save_current_answer(q_id, selected_ans, test_id, sec_instance_id)
        st.session_state["current_q_index"] -= 1
        st.rerun()
        
    if c2.button("Next", disabled=(q_index == len(questions) - 1)):
        _save_current_answer(q_id, selected_ans, test_id, sec_instance_id)
        st.session_state["current_q_index"] += 1
        st.rerun()
        
    if c3.button("Save"):
        _save_current_answer(q_id, selected_ans, test_id, sec_instance_id)
        st.toast("Answer saved!")
        
    if c4.button("Submit Section", type="primary"):
        _save_current_answer(q_id, selected_ans, test_id, sec_instance_id)
        testing_engine.complete_section_and_adapt(test_id, sec_instance_id)
        st.session_state.pop("current_section_payload", None)
        st.rerun()

def _save_current_answer(q_id: str, ans: Optional[str], test_id: str, sec_instance_id: str) -> None:
    if ans:
        st.session_state["user_answers"][q_id] = ans
        time_spent = timer.get_question_elapsed_time(st.session_state.get("q_start_time", time.time()))
        testing_engine.submit_answer_atomically(test_id, sec_instance_id, q_id, ans, time_spent)
        st.session_state["q_start_time"] = time.time()
