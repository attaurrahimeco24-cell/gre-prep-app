import streamlit as st
import pandas as pd
import time
import gre_platform_merged as db_manager
from ui import components

def render_question_bank():
    st.markdown("## 📝 Question Bank Management")
    st.caption("Content Lifecycle, Versioning, and Approvals")
    
    admin_id = st.session_state.get("user_id", "system")
    
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

def render_user_management():
    st.markdown("## 👥 User Management")
    st.caption("Control platform access, roles, and account statuses.")
    
    admin_id = st.session_state.get("user_id", "system")
    admin_role = st.session_state.get("user_role", "ADMIN")
    
    users = db_manager.get_all_users()
    
    if not users:
        st.info("No registered users found.")
        return
        
    for u in users:
        status_text = "ACTIVE" if u['is_active'] else "SUSPENDED"
        badge = components.status_badge(status_text)
        
        with st.expander(f"👤 {u['username']} ({u['email']})"):
            st.markdown(f"**Current Role:** `{u['role']}` | **Status:** {badge} | **Joined:** {u['created_at'][:10]}", unsafe_allow_html=True)
            
            # Security Rule: Don't let an admin lock themselves out
            if u['user_id'] == admin_id:
                st.warning("🔒 You cannot modify your own access privileges.")
                continue
                
            # Security Rule: Only SUPER_ADMIN can modify other Admins
            if u['role'] in ['ADMIN', 'SUPER_ADMIN'] and admin_role != 'SUPER_ADMIN':
                st.error("🔒 Only a SUPER_ADMIN can modify other administrators.")
                continue
                
            with st.form(key=f"form_user_{u['user_id']}"):
                c1, c2 = st.columns(2)
                with c1:
                    new_role = st.selectbox("Role", ["STUDENT", "ADMIN", "SUPER_ADMIN"], index=["STUDENT", "ADMIN", "SUPER_ADMIN"].index(u['role']))
                with c2:
                    new_status = st.selectbox("Account Status", ["ACTIVE", "SUSPENDED"], index=0 if u['is_active'] else 1)
                
                reason = st.text_input("Reason for Access Change (Required)")
                if st.form_submit_button("Update User Access", type="primary"):
                    if not reason:
                        st.error("An audit reason is required to change access privileges.")
                    else:
                        is_act_int = 1 if new_status == "ACTIVE" else 0
                        db_manager.update_user_access(u['user_id'], new_role, is_act_int, admin_id, reason)
                        st.success(f"Successfully updated access for {u['username']}.")
                        time.sleep(1)
                        st.rerun()

def render_audit_logs():
    st.markdown("## 🛡️ System Audit Logs")
    st.caption("Immutable cryptographic ledger of all administrative actions.")
    
    logs = db_manager.get_audit_logs(limit=200)
    
    if not logs:
        st.info("No administrative actions have been logged yet.")
        return
        
    df = pd.DataFrame(logs)
    
    # Format the dataframe for cleaner SaaS presentation
    df = df.rename(columns={
        "timestamp": "Timestamp",
        "admin_username": "Admin",
        "action": "Action",
        "target_object": "Target Object",
        "reason": "Audit Reason"
    })
    
    # Display as a full-width interactive dataframe
    st.dataframe(
        df[["Timestamp", "Admin", "Action", "Target Object", "Audit Reason"]],
        use_container_width=True,
        hide_index=True
    )
    st.caption("Displaying the last 200 security events. These records are read-only and cannot be altered.")
