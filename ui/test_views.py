import streamlit as st
import time
from modules import testing_engine

# ⚡ PHASE 5 PERFORMANCE UPGRADE: Isolate the timer so it doesn't cause full-page reruns
@st.fragment(run_every="1s")
def render_timer_fragment(start_time: float, duration_seconds: int, test_id: str, section_instance_id: str):
    """A self-contained DOM fragment that ticks every 1 second without lagging the app."""
    elapsed = time.time() - start_time
    remaining = int(duration_seconds - elapsed)
    
    if remaining <= 0:
        st.error("⏱️ Time is up! Auto-submitting section...")
        testing_engine.complete_section_and_adapt(test_id, section_instance_id)
        st.session_state.pop("active_sec_instance_id", None)
        st.session_state.pop("current_section_payload", None)
        st.rerun()
        return
        
    mins, secs = divmod(remaining, 60)
    
    # Premium UI styling for the timer
    st.markdown(
        f"""
        <div style="background: var(--surface, #FFFFFF); border: 1px solid var(--border, #E2E8F0); 
                    padding: 8px 16px; border-radius: 8px; display: inline-flex; align-items: center; gap: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05); font-family: monospace; font-size: 1.25rem; font-weight: bold;">
            <span>⏱️</span>
            <span style="color: {'#EF4444' if remaining < 300 else 'inherit'};">
                {mins:02d}:{secs:02d}
            </span>
        </div>
        """, unsafe_allow_html=True
    )

def render_exam_simulation(test_id: str):
    st.markdown("## 🎓 GRE Exam Simulation")
    
    sec_info = testing_engine.get_active_section_info(test_id)
    if not sec_info:
        st.success("✅ Test Complete! Your results are being calculated.")
        if st.button("View Analytics Dashboard", type="primary"):
            st.session_state["active_page"] = "📈 Performance Analytics"
            st.session_state.pop("active_test_id", None)
            st.rerun()
        return

    sec_instance_id = sec_info["section_instance_id"]
    
    # INITIALIZE SECTION
    if sec_info["status"] == "pending":
        st.info(f"**Next Section:** {sec_info['section_key']}")
        st.write(f"You will have **{sec_info['time_allotted_seconds'] // 60} minutes** to complete this section.")
        if st.button("Start Section", type="primary", use_container_width=True):
            payload = testing_engine.start_active_section(sec_instance_id)
            st.session_state["active_sec_instance_id"] = sec_instance_id
            st.session_state["current_section_payload"] = payload
            st.session_state["current_q_index"] = 0
            st.session_state["user_answers"] = {}
            st.session_state["q_start_time"] = time.time()
            st.rerun()
        return

    # EXAM IN PROGRESS
    payload = st.session_state.get("current_section_payload")
    if not payload:
        st.error("Critical Error: Section payload lost. Please contact support.")
        st.stop()

    questions = payload["questions"]
    q_idx = st.session_state.get("current_q_index", 0)
    
    # ---------------------------------------------------------
    # EXAM HEADER (Timer runs inside this fragment)
    # ---------------------------------------------------------
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"**Section:** {payload['section_name']} | **Question:** {q_idx + 1} of {len(questions)}")
    with c2:
        # Calls the isolated timer component
        render_timer_fragment(payload["start_timestamp"], payload["duration_seconds"], test_id, sec_instance_id)

    st.progress((q_idx + 1) / len(questions))
    st.divider()
    
    # ---------------------------------------------------------
    # QUESTION RENDERER
    # ---------------------------------------------------------
    current_q = questions[q_idx]
    
    st.markdown(f"<div style='font-size: 1.1rem; line-height: 1.6;'>{current_q['question_text']}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Capture user input based on question type
    user_ans = st.session_state["user_answers"].get(current_q["question_id"], "")
    new_ans = user_ans
    
    if current_q["question_type"] == "Multiple Choice":
        opts = current_q.get("options", [])
        idx = opts.index(user_ans) if user_ans in opts else None
        new_ans = st.radio("Select an answer:", opts, index=idx, key=f"q_{current_q['question_id']}")
    elif current_q["question_type"] == "Numeric Entry":
        new_ans = st.text_input("Enter your numerical answer:", value=user_ans, key=f"q_{current_q['question_id']}")
    else:
        new_ans = st.text_area("Your Response:", value=user_ans, height=200, key=f"q_{current_q['question_id']}")

    st.divider()

    # ---------------------------------------------------------
    # NAVIGATION & ATOMIC SUBMISSION
    # ---------------------------------------------------------
    nav1, nav2, nav3 = st.columns([1, 1, 1])
    
    with nav1:
        if q_idx > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                # Save time spent and answer
                time_spent = int(time.time() - st.session_state["q_start_time"])
                testing_engine.submit_answer_atomically(test_id, sec_instance_id, current_q["question_id"], new_ans, time_spent)
                st.session_state["user_answers"][current_q["question_id"]] = new_ans
                st.session_state["current_q_index"] -= 1
                st.session_state["q_start_time"] = time.time()
                st.rerun()

    with nav3:
        if q_idx < len(questions) - 1:
            if st.button("Next ➡️", type="primary", use_container_width=True):
                time_spent = int(time.time() - st.session_state["q_start_time"])
                testing_engine.submit_answer_atomically(test_id, sec_instance_id, current_q["question_id"], new_ans, time_spent)
                st.session_state["user_answers"][current_q["question_id"]] = new_ans
                st.session_state["current_q_index"] += 1
                st.session_state["q_start_time"] = time.time()
                st.rerun()
        else:
            if st.button("Submit Section", type="primary", use_container_width=True):
                time_spent = int(time.time() - st.session_state["q_start_time"])
                testing_engine.submit_answer_atomically(test_id, sec_instance_id, current_q["question_id"], new_ans, time_spent)
                st.session_state["user_answers"][current_q["question_id"]] = new_ans
                
                with st.spinner("Calculating Psychometric Adaptivity..."):
                    testing_engine.complete_section_and_adapt(test_id, sec_instance_id)
                st.session_state.pop("active_sec_instance_id", None)
                st.session_state.pop("current_section_payload", None)
                st.success("Section Submitted Successfully.")
                time.sleep(1)
                st.rerun()
