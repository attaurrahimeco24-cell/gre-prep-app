import streamlit as st
import pandas as pd
import time
import gre_platform_merged as db_manager
from modules import question_engine, email_service
from ui import components

def ensure_data_seeded(admin_id: str):
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
    ensure_data_seeded(admin_id)
    
    st.markdown("## 📚 Content Library")
    st.caption("Manage the psychometric question bank, review lifecycle, and version control.")
    
    if "admin_q_mode" not in st.session_state: st.session_state["admin_q_mode"] = "list"
    
    if st.session_state["admin_q_mode"] == "list":
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
            df = pd.DataFrame(questions)
            display_df = df[["question_id", "status", "section", "domain", "difficulty_level", "question_text"]].copy()
            display_df.rename(columns={
                "question_id": "ID", "status": "Status", "section": "Section", 
                "domain": "Domain", "difficulty_level": "Tier", "question_text": "Preview"
            }, inplace=True)
            display_df["Preview"] = display_df["Preview"].str.slice(0, 60) + "..."
            
            st.markdown(f"**Showing {len(questions)} verified assets**")
            
            st.dataframe(
                display_df, use_container_width=True, hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Tier": st.column_config.NumberColumn("Tier", format="⭐ %d", width="small"),
                    "Preview": st.column_config.TextColumn("Content Preview", width="large"),
                }
            )
            
            st.markdown("### Action Center")
            c_edit1, c_edit2 = st.columns([3, 1])
            with c_edit1: target_edit_id = st.text_input("Enter Question ID (e.g., Q-ALG-...)", label_visibility="collapsed")
            with c_edit2:
                if st.button("✏️ Edit Question", use_container_width=True):
                    if target_edit_id:
                        st.session_state["admin_q_mode"] = "edit"
                        st.session_state["admin_q_target"] = target_edit_id.strip()
                        st.rerun()

        components.render_danger_zone("Factory Content Wipe", "Destroys all custom edits and procedurally generates 2,000 fresh questions with geometric SVGs.")
        if st.button("🔄 Execute Factory Reset & Build 2,000 Questions", type="primary"):
            with st.spinner("Procedurally generating 2,000 questions..."):
                question_engine.seed_initial_question_bank(force_reset=True)
                db_manager.log_admin_action(admin_id, "FACTORY_RESET", "QUESTIONS", reason="Admin requested 2000 question build")
            st.success("✅ 2,000 Questions generated and committed!")
            time.sleep(1.5)
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
                "question_id": f"Q-NEW-{db_manager._new_id('')[:6]}", "section": "Quantitative Reasoning", "domain": "", "topic": "", "subtopic": "",
                "question_type": "Multiple Choice", "difficulty_level": 3, "question_text": "", "options": ["A", "B", "C", "D"], "correct_answer": "", "explanation": "",
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
            domain = col_d.text_input("Domain", value=q_data.get("domain", ""))
            topic = col_e.text_input("Topic", value=q_data.get("topic", ""))
            diff = col_f.number_input("Difficulty Tier (1-5)", min_value=1, max_value=5, value=int(q_data.get("difficulty_level", 3)))
            
            st.markdown("**Content Authoring**")
            q_text = st.text_area("Question Text / Passage", value=q_data.get("question_text", ""), height=150)
            opts_str = "\n".join(q_data.get("options", [])) if q_data.get("options") else ""
            options_input = st.text_area("Options (One per line)", value=opts_str, help="Leave blank for Numeric Entry or AWA")
            
            correct = st.text_input("Correct Answer (Must match an option exactly)", value=q_data.get("correct_answer", ""))
            expl = st.text_area("Detailed Explanation", value=q_data.get("explanation", ""))
            
            st.markdown("---")
            reason = st.text_input("Audit Reason (Required)")
            confirm_key = st.checkbox("I verify this content is psychometrically valid and structurally secure.")
            
            if st.form_submit_button("💾 Commit Changes to Production Database", type="primary"):
                if not reason or not confirm_key: st.error("🔒 Security Halt: Audit reason and verification required.")
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

def render_user_management():
    st.markdown("## 🧑‍🎓 User Access Management")
    st.caption("Control platform access, roles, and verification statuses.")
    
    admin_id = st.session_state.get("user_id", "system")
    admin_role = st.session_state.get("user_role", "ADMIN")
    
    users = db_manager.get_all_users()
    if not users:
        st.info("No registered users found.")
        return
        
    for u in users:
        status_text = "ACTIVE" if u['is_active'] else "SUSPENDED"
        badge = components.status_badge(status_text)
        ver_badge = '<span class="badge badge-success">VERIFIED</span>' if u['is_verified'] else '<span class="badge badge-warning">PENDING</span>'
        
        with st.expander(f"👤 {u['username']} ({u['email']})"):
            st.markdown(f"**Role:** `{u['role']}` | **Account Status:** {badge} | **Email Status:** {ver_badge}", unsafe_allow_html=True)
            
            if u['user_id'] == admin_id:
                st.warning("🔒 You cannot modify your own access privileges.")
                continue
            if u['role'] in ['ADMIN', 'SUPER_ADMIN'] and admin_role != 'SUPER_ADMIN':
                st.error("🔒 Only a SUPER_ADMIN can modify other administrators.")
                continue
                
            with st.form(key=f"form_user_{u['user_id']}"):
                c1, c2, c3 = st.columns(3)
                with c1: new_role = st.selectbox("Role", ["STUDENT", "ADMIN", "SUPER_ADMIN"], index=["STUDENT", "ADMIN", "SUPER_ADMIN"].index(u['role']))
                with c2: new_status = st.selectbox("Account Status", ["ACTIVE", "SUSPENDED"], index=0 if u['is_active'] else 1)
                with c3: new_ver = st.selectbox("Manual Verification", ["VERIFIED", "PENDING"], index=0 if u['is_verified'] else 1, disabled=bool(u['is_verified']))
                
                reason = st.text_input("Reason for Access Change (Required for Audit Log)")
                
                if st.form_submit_button("Update User Profile", type="primary"):
                    if not reason: st.error("An audit reason is required to change user privileges.")
                    else:
                        is_act_int = 1 if new_status == "ACTIVE" else 0
                        db_manager.update_user_access(u['user_id'], new_role, is_act_int, admin_id, reason)
                        if new_ver == "VERIFIED" and not u['is_verified']:
                            db_manager.manually_verify_user(u['user_id'], admin_id, reason)
                        st.success(f"Successfully updated profile for {u['username']}.")
                        time.sleep(1)
                        st.rerun()

def render_email_settings():
    st.markdown("## ✉️ SMTP Gateway")
    st.caption("Securely configure transactional email delivery for student verification and alerts.")
    
    admin_id = st.session_state.get("user_id", "system")
    current_settings = db_manager.get_all_settings()
    
    with st.form("smtp_form"):
        st.markdown("### SMTP Provider Credentials")
        components.render_setting_row("Host & Port", "Your SMTP server endpoint and connection port (e.g., smtp.sendgrid.net).")
        c1, c2 = st.columns([3, 1])
        with c1: host = st.text_input("SMTP Host", value=current_settings.get("smtp_host", ""))
        with c2: port = st.text_input("SMTP Port", value=current_settings.get("smtp_port", "587"))
        
        components.render_setting_row("Authentication", "Credentials to connect to the SMTP server.")
        c3, c4 = st.columns(2)
        with c3: user = st.text_input("SMTP Username", value=current_settings.get("smtp_user", ""))
        with c4: pwd = st.text_input("SMTP Password", type="password", value=current_settings.get("smtp_password", ""))
        
        components.render_setting_row("Sender Identity", "How the email will appear in the student's inbox.")
        c5, c6 = st.columns(2)
        with c5: s_name = st.text_input("Sender Display Name", value=current_settings.get("smtp_sender_name", "GRE Platform"))
        with c6: req_ver = st.selectbox("Require Verification?", ["true", "false"], index=0 if current_settings.get("require_email_verification", "true") == "true" else 1)

        st.divider()
        reason = st.text_input("Audit Reason (Required)")
        if st.form_submit_button("💾 Securely Save SMTP Configuration", type="primary"):
            if not reason: st.error("🔒 Security Halt: Audit reason required.")
            else:
                updates = {
                    "smtp_host": host, "smtp_port": port, "smtp_user": user, 
                    "smtp_password": pwd, "smtp_sender_name": s_name, 
                    "require_email_verification": req_ver
                }
                db_manager.update_settings(updates, admin_id, reason)
                st.success("✅ SMTP configurations updated successfully.")
                time.sleep(1)
                st.rerun()
                
    st.markdown("### 🧪 Connection Diagnostics")
    with st.form("test_email_form"):
        test_address = st.text_input("Recipient Email Address")
        if st.form_submit_button("Send Diagnostic Test Email"):
            if test_address:
                with st.spinner("Initiating SMTP connection..."):
                    success = email_service.send_verification_email(admin_id, test_address, "Admin Tester")
                if success.get("status") == "sent": st.success(f"✅ Test email successfully dispatched to {test_address}.")
                elif success.get("status") == "simulated": st.warning("⚠️ SMTP NOT CONFIGURED. Dev-mode simulation active.")
                else: st.error("❌ SMTP connection failed. Check your credentials and server logs.")
            else: st.warning("Please enter a destination email address.")

def render_audit_logs():
    st.markdown("## 🔐 System Audit Ledger")
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
    
    st.dataframe(df[["Timestamp", "Admin", "Action", "Target Object", "Audit Reason"]], use_container_width=True, hide_index=True)
