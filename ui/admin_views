import streamlit as st
import time
import gre_platform_merged as db_manager

def render_question_bank():
    st.title("🛠️ Question Bank Management")
    st.caption("Content Lifecycle, Versioning, and Approvals")
    
    admin_id = st.session_state.get("user_id", "system")
    
    # Init routing state
    if "admin_q_mode" not in st.session_state:
        st.session_state["admin_q_mode"] = "list"
    if "admin_q_target" not in st.session_state:
        st.session_state["admin_q_target"] = None
        
    if st.session_state["admin_q_mode"] == "list":
        st.markdown("### Filter & Search")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            sec_filter = st.selectbox("Filter Section", ["All", "Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"])
        with c2:
            stat_filter = st.selectbox("Filter Status", ["All", "DRAFT", "PENDING_REVIEW", "APPROVED", "ARCHIVED"])
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ New Draft", type="primary", use_container_width=True):
                st.session_state["admin_q_mode"] = "create"
                st.rerun()
                
        questions = db_manager.get_all_questions_admin(sec_filter, stat_filter)
        
        if not questions:
            st.info("No questions found matching criteria.")
            return
            
        st.markdown(f"**Showing {len(questions)} items**")
        for q in questions:
            status_color = "green" if q['status'] == "APPROVED" else "orange" if q['status'] == "PENDING_REVIEW" else "gray"
            with st.expander(f"[{q['status']}] {q['question_id']} - {q['domain']} ({q['topic']})"):
                st.markdown(f"*{q['question_text'][:120]}...*")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit / Review Lifecycle", key=f"edit_{q['question_id']}"):
                        st.session_state["admin_q_mode"] = "edit"
                        st.session_state["admin_q_target"] = q['question_id']
                        st.rerun()
                with col2:
                    if q['status'] == "ARCHIVED":
                        st.warning("Archived. Edit to restore to DRAFT.")
                        
    elif st.session_state["admin_q_mode"] in ["edit", "create"]:
        mode = st.session_state["admin_q_mode"]
        q_id = st.session_state.get("admin_q_target")
        
        if st.button("⬅️ Back to Bank"):
            st.session_state["admin_q_mode"] = "list"
            st.rerun()
            
        st.divider()
        
        if mode == "edit":
            q_data = db_manager.get_question_by_id(q_id)
            st.subheader(f"Editing Question: {q_id}")
        else:
            q_data = {
                "question_id": f"Q-NEW-{db_manager._new_id('')[:6]}",
                "section": "Quantitative Reasoning",
                "domain": "", "topic": "", "subtopic": "",
                "question_type": "Multiple Choice",
                "difficulty_level": 3, "question_text": "",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "", "explanation": "",
                "estimated_time_seconds": 90, "status": "DRAFT"
            }
            st.subheader("Creating New Draft Question")
            
        with st.form("q_edit_form"):
            new_status = st.selectbox("Lifecycle Status", ["DRAFT", "PENDING_REVIEW", "APPROVED", "ARCHIVED"], index=["DRAFT", "PENDING_REVIEW", "APPROVED", "ARCHIVED"].index(q_data["status"]))
            
            c1, c2 = st.columns(2)
            section = c1.selectbox("Section", ["Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"], index=["Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"].index(q_data["section"]))
            q_type = c2.selectbox("Type", ["Multiple Choice", "Numeric Entry", "Quantitative Comparison", "Issue Task"], index=["Multiple Choice", "Numeric Entry", "Quantitative Comparison", "Issue Task"].index(q_data.get("question_type", "Multiple Choice")))
            
            c3, c4, c5 = st.columns(3)
            domain = c3.text_input("Domain", value=q_data.get("domain", ""))
            topic = c4.text_input("Topic", value=q_data.get("topic", ""))
            diff = c5.number_input("Difficulty (1-5)", min_value=1, max_value=5, value=int(q_data.get("difficulty_level", 3)))
            
            q_text = st.text_area("Question Text", value=q_data.get("question_text", ""), height=150)
            
            opts_str = "\n".join(q_data.get("options", [])) if q_data.get("options") else ""
            options_input = st.text_area("Options (One per line, leave blank if not applicable)", value=opts_str)
            
            correct = st.text_input("Correct Answer (Must exactly match one option if Multiple Choice)", value=q_data.get("correct_answer", ""))
            expl = st.text_area("Explanation", value=q_data.get("explanation", ""))
            
            st.divider()
            st.markdown("### Security & Version Control")
            reason = st.text_input("Reason for Change (Required for Audit Log)")
            confirm_key = st.checkbox("I confirm these changes are psychometrically sound and mathematically verified.")
            
            submitted = st.form_submit_button("Save Question Data", type="primary")
            
            if submitted:
                if not reason or not confirm_key:
                    st.error("🔒 Security Halt: You must provide an audit reason and tick the confirmation box.")
                else:
                    new_opts = [o.strip() for o in options_input.split("\n") if o.strip()] if options_input.strip() else None
                    
                    updated_payload = {
                        "question_id": q_data["question_id"],
                        "section": section, "domain": domain, "topic": topic, "subtopic": "",
                        "question_type": q_type, "difficulty_level": diff,
                        "question_text": q_text, "options": new_opts,
                        "correct_answer": correct, "explanation": expl,
                        "estimated_time_seconds": q_data.get("estimated_time_seconds", 90),
                        "status": new_status, "source": q_data.get("source", "Admin-Generated")
                    }
                    
                    try:
                        if mode == "create":
                            db_manager.insert_question(updated_payload)
                            db_manager.log_admin_action(admin_id, "CREATED_QUESTION", updated_payload["question_id"], reason=reason)
                        else:
                            db_manager.update_question(q_data["question_id"], updated_payload, admin_id, reason)
                            
                        st.success("✅ Question and version history saved successfully!")
                        st.session_state["admin_q_mode"] = "list"
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
