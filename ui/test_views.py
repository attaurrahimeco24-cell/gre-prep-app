import time
import streamlit as st
from modules import testing_engine, timer
from ui import components

# Isolate the timer so it ticks every 1 second WITHOUT re-rendering the rest of the test UI
@st.fragment(run_every="1s")
def live_timer_fragment(section_name: str, sec_instance_id: str, duration_seconds: int, test_id: str):
    time_status = components.render_cbt_header(section_name, sec_instance_id, duration_seconds)
    
    if time_status["is_expired"]:
        st.warning("⏱️ Time expired for this section! Auto-submitting...")
        testing_engine.complete_section_and_adapt(test_id, sec_instance_id)
        st.session_state.pop("current_section_payload", None)
        time.sleep(1.5)
        st.rerun()

def render_exam_simulation(test_id: str) -> None:
    sec_info = testing_engine.get_active_section_info(test_id)
    
    if not sec_info:
        st.balloons()
        st.success("🎉 Examination Completed! All sections have been successfully submitted.")
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📊 View Final Analytics", type="primary", use_container_width=True):
                st.session_state["active_page"] = "Analytics Dashboard"
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
        st.error("No questions available for this section. Please skip to the next section.")
        if st.button("⏭️ Skip Empty Section", type="primary"):
            testing_engine.complete_section_and_adapt(test_id, sec_instance_id)
            st.session_state.pop("current_section_payload", None)
            st.rerun()
        return

    # 1. Render the auto-ticking timer fragment
    live_timer_fragment(payload["section_name"], sec_instance_id, payload["duration_seconds"], test_id)
        
    q_index = st.session_state.get("current_q_index", 0)
    current_q = questions[q_index]
    q_id = current_q["question_id"]
    q_type = current_q.get("question_type", "Multiple Choice")

    with st.sidebar:
        st.markdown("### 🔢 Question Palette")
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
    st.markdown(f"<div style='font-size: 1.15rem; font-weight: 500; padding: 10px 0 20px 0; color: #0F172A;'>{current_q['question_text']}</div>", unsafe_allow_html=True)

    existing_ans = st.session_state["user_answers"].get(q_id, "")
    widget_key = f"input_{q_id}"

    def autosave_answer():
        val = st.session_state[widget_key]
        if val is not None:
            st.session_state["user_answers"][q_id] = val 
            time_spent = timer.get_question_elapsed_time(st.session_state.get("q_start_time", time.time()))
            testing_engine.submit_answer_atomically(test_id, sec_instance_id, q_id, str(val), time_spent) 
            st.session_state["q_start_time"] = time.time()

    if q_type == "Numeric Entry":
        st.text_input("Enter your numerical answer:", value=existing_ans, key=widget_key, on_change=autosave_answer)
    elif q_type == "Issue Task":
        st.text_area("Write your essay response here:", value=existing_ans, height=350, key=widget_key, on_change=autosave_answer)
    else:
        options = current_q.get("options") or ["A", "B", "C", "D", "E"]
        try:
            idx_val = options.index(existing_ans) if existing_ans else None
        except ValueError:
            idx_val = None
            
        st.radio("Select your choice:", options, index=idx_val, key=widget_key, on_change=autosave_answer)

    st.divider()
    
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    
    if c1.button("⬅️ Previous", disabled=(q_index == 0), use_container_width=True):
        st.session_state["current_q_index"] -= 1
        st.session_state["q_start_time"] = time.time()
        st.rerun()
        
    if c2.button("Next ➡️", disabled=(q_index == len(questions) - 1), use_container_width=True):
        st.session_state["current_q_index"] += 1
        st.session_state["q_start_time"] = time.time()
        st.rerun()
        
    if c3.button("💾 Save", use_container_width=True):
        if widget_key in st.session_state:
            autosave_answer()
        st.toast("Answer saved securely!", icon="✅")
        
    if c4.button("✅ Submit Section", type="primary", use_container_width=True):
        testing_engine.complete_section_and_adapt(test_id, sec_instance_id)
        st.session_state.pop("current_section_payload", None)
        st.rerun()
