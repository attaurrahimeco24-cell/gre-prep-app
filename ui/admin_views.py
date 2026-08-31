import streamlit as st
import pandas as pd
import time
import gre_platform_merged as db_manager
from modules import question_engine
from ui import components

def ensure_data_seeded(admin_id: str):
    """FAILSAFE: If the database is empty, force an automatic reseed so the UI is never broken."""
    if db_manager.count_questions() == 0:
        with st.spinner("Initializing Premium Content Database..."):
            question_engine.seed_initial_question_bank(force_reset=True)
            db_manager.seed_default_settings()
            db_manager.sync_settings_to_globals()
            db_manager.log_admin_action(admin_id, "SYSTEM_AUTO_SEED", "ALL", reason="Failsafe Recovery")
        st.success("✅ System successfully synchronized with core database.")
        time.sleep(1)
        st.rerun()

def render_question_bank():
    admin_id = st.session_state.get("user_id", "system")
    ensure_data_seeded(admin_id) # Call failsafe
    
    st.markdown("## 📝 Content Architecture")
    st.caption("Manage the psychometric question bank, review lifecycle, and version control.")
    
    if "admin_q_mode" not in st.session_state:
        st.session_state["admin_q_mode"] = "list"
    
    if st.session_state["admin_q_mode"] == "list":
        # --- PREMIUM DATA GRID ---
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1: sec_filter = st.selectbox("Section", ["All", "Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"])
        with c2: stat_filter = st.selectbox("Lifecycle Status", ["All", "DRAFT", "PENDING_REVIEW", "APPROVED", "ARCHIVED"])
        with c4: 
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("➕ Create New Question", type="primary", use_container_width=True):
                st.session_state["admin_q_mode"] = "create"
                st.rerun()
                
        questions = db_manager.get_all_questions_admin(sec_filter, stat_filter)
        
        if not questions:
            st.info("No content matches your filters.")
        else:
            # Convert to Pandas for Beautiful Table
            df = pd.DataFrame(questions)
            display_df = df[["question_id", "status", "section", "domain", "difficulty_level", "question_text"]].copy()
            display_df.rename(columns={
                "question_id": "ID", "status": "Status", "section": "Section", 
                "domain": "Domain", "difficulty_level": "Tier", "question_text": "Preview"
            }, inplace=True)
            display_df["Preview"] = display_df["Preview"].str.slice(0, 60) + "..."
            
            st.markdown(f"**Showing {len(questions)} verified assets**")
            
            # Interactive Grid
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Tier": st.column_config.NumberColumn("Tier", format="⭐ %d", width="small"),
                    "Preview": st.column_config.TextColumn("Content Preview", width="large"),
                }
            )
            
            st.markdown("### Action Center")
            st.caption("Enter a Question ID to edit its content or change its approval status.")
            c_edit1, c_edit2 = st.columns([3, 1])
            with c_edit1:
                target_edit_id = st.text_input("Enter Question ID (e.g., Q-ALG-01)", label_visibility="collapsed")
            with c_edit2:
                if st.button("✏️ Edit Question", use_container_width=True):
                    if target_edit_id:
                        st.session_state["admin_q_mode"] = "edit"
                        st.session_state["admin_q_target"] = target_edit_id.strip()
                        st.rerun()

        components.render_danger_zone("Factory Content Wipe", "Destroys all custom edits and resets the database strictly to the 62 original seed questions.")
        if st.button("🔄 Execute Factory Reset", type="primary"):
            with st.spinner("Purging and rebuilding database..."):
                question_engine.seed_initial_question_bank(force_reset=True)
                db_manager.log_admin_action(admin_id, "FACTORY_RESET", "QUESTIONS", reason="Admin requested complete data wipe")
            st.success("✅ System reset complete.")
            time.sleep(1)
            st.rerun()
                        
    elif st.session_state["admin_q_mode"] in ["edit", "create"]:
        mode = st.session_state["admin_q_mode"]
        q_id = st.session_state.get("admin_q_target")
        
        if st.button("⬅️ Return to Content Grid"):
            st.session_state["admin_q_mode"] = "list"
            st.rerun()
            
        st.markdown("---")
        
        q_data = None
        if mode == "edit":
            q_data = db_manager.get_question_by_id(q_id)
            if not q_data:
                st.error("Question ID not found.")
                st.stop()
            st.markdown(f"### Editing Asset: `{q_id}`")
        else:
            q_data = {
                "question_id": f"Q-NEW-{db_manager._new_id('')[:6]}",
                "section": "Quantitative Reasoning", "domain": "", "topic": "", "subtopic": "",
                "question_type": "Multiple Choice", "difficulty_level": 3, "question_text": "",
                "options": ["A", "B", "C", "D"], "correct_answer": "", "explanation": "",
                "estimated_time_seconds": 90, "status": "DRAFT"
            }
            st.markdown("### Drafting New Content")
            
        with st.form("q_edit_form"):
            st.markdown("**Classification & Routing**")
            col_a, col_b, col_c = st.columns(3)
            new_status = col_a.selectbox("Lifecycle Status", ["DRAFT", "PENDING_REVIEW", "APPROVED", "ARCHIVED"], index=["DRAFT", "PENDING_REVIEW", "APPROVED", "ARCHIVED"].index(q_data["status"]))
            section = col_b.selectbox("Section", ["Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"], index=["Quantitative Reasoning", "Verbal Reasoning", "Analytical Writing"].index(q_data["section"]))
            q_type = col_c.selectbox("Type", ["Multiple Choice", "Numeric Entry", "Quantitative Comparison", "Issue Task"], index=["Multiple Choice", "Numeric Entry", "Quantitative Comparison", "Issue Task"].index(q_data.get("question_type", "Multiple Choice")))
            
            col_d, col_e, col_f = st.columns(3)
            domain = col_d.text_input("Domain (e.g., Algebra, Text Completion)", value=q_data.get("domain", ""))
            topic = col_e.text_input("Topic", value=q_data.get("topic", ""))
            diff = col_f.number_input("Difficulty Tier (1-5)", min_value=1, max_value=5, value=int(q_data.get("difficulty_level", 3)))
            
            st.markdown("**Content Authoring**")
            q_text = st.text_area("Question Text / Passage", value=q_data.get("question_text", ""), height=150)
            opts_str = "\n".join(q_data.get("options", [])) if q_data.get("options") else ""
            options_input = st.text_area("Options (One per line)", value=opts_str, help="Leave blank for Numeric Entry or AWA")
            
            correct = st.text_input("Correct Answer (Must match an option exactly)", value=q_data.get("correct_answer", ""))
            expl = st.text_area("Detailed Explanation", value=q_data.get("explanation", ""))
            
            st.markdown("---")
            st.markdown("#### Security Verification")
            reason = st.text_input("Audit Reason (Required)")
            confirm_key = st.checkbox("I verify this content is psychometrically valid and structurally secure.")
            
            if st.form_submit_button("💾 Commit Changes to Production Database", type="primary"):
                if not reason or not confirm_key:
                    st.error("🔒 Security Halt: Audit reason and checkbox verification are required.")
                else:
                    new_opts = [o.strip() for o in options_input.split("\n") if o.strip()] if options_input.strip() else None
                    updated_payload = {
                        "question_id": q_data["question_id"], "section": section, "domain": domain, "topic": topic, "subtopic": "",
                        "question_type": q_type, "difficulty_level": diff, "question_text": q_text, "options": new_opts,
                        "correct_answer": correct, "explanation": expl, "estimated_time_seconds": q_data.get("estimated_time_seconds", 90),
                        "status": new_status, "source": q_data.get("source", "Admin-Generated")
                    }
                    try:
                        if mode == "create":
                            db_manager.insert_question(updated_payload)
                            db_manager.log_admin_action(admin_id, "CREATED_QUESTION", updated_payload["question_id"], reason=reason)
                        else:
                            db_manager.update_question(q_data["question_id"], updated_payload, admin_id, reason)
                        st.success("✅ Asset committed successfully!")
                        st.session_state["admin_q_mode"] = "list"
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to commit: {e}")

# ... (render_user_management and render_audit_logs remain functionally identical but benefit from the new CSS) ...
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
            
            if u['user_id'] == admin_id:
                st.warning("🔒 You cannot modify your own access privileges.")
                continue
                
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
    df = df.rename(columns={
        "timestamp": "Timestamp", "admin_username": "Admin", "action": "Action",
        "target_object": "Target Object", "reason": "Audit Reason"
    })
    
    st.dataframe(
        df[["Timestamp", "Admin", "Action", "Target Object", "Audit Reason"]],
        use_container_width=True, hide_index=True
    )
