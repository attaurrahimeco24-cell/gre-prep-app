import streamlit as st
import pandas as pd
import plotly.express as px
import gre_platform_merged as db_manager
from ui import components

def render_analytics_dashboard() -> None:
    st.title("📈 Performance Analytics & Mastery Hub")
    st.caption("Real-time telemetry on accuracy, timing efficiency, and domain-level weaknesses.")

    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM tests WHERE status = 'completed'")
        completed_tests = cur.fetchone()["c"]
        
        cur.execute("""
            SELECT topic, accuracy_pct, total_attempts, avg_speed_seconds, mastery_rating 
            FROM user_performance 
            ORDER BY accuracy_pct ASC
        """)
        perf_data = [dict(r) for r in cur.fetchall()]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        components.render_score_card("Completed Exams", str(completed_tests), "Full & Section Drills")
    with m2:
        components.render_score_card("Topics Tracked", str(len(perf_data)), "Quant & Verbal Domains")
    with m3:
        avg_acc = (sum(r['accuracy_pct'] for r in perf_data) / len(perf_data)) if perf_data else 0.0
        components.render_score_card("Overall Accuracy", f"{avg_acc:.1f}%", "Historical Average")
    with m4:
        avg_speed = (sum(r['avg_speed_seconds'] for r in perf_data if r['avg_speed_seconds']) / len(perf_data)) if perf_data else 0.0
        components.render_score_card("Pacing Avg", f"{int(avg_speed)}s", "Target: <90s per Q")

    st.divider()

    if not perf_data:
        st.info("💡 **No diagnostic data recorded yet.** Complete practice questions or full simulations to populate metrics.")
        return

    df = pd.DataFrame(perf_data)
    df['mastery_rating'] = df['mastery_rating'].fillna('weak')

    col_chart, col_matrix = st.columns([1.2, 1])

    with col_chart:
        st.subheader("🎯 Topic Performance Breakdown")
        fig = px.bar(
            df,
            x='topic',
            y='accuracy_pct',
            color='mastery_rating',
            color_discrete_map={
                "weak": "#EF4444",
                "developing": "#F59E0B",
                "proficient": "#3B82F6",
                "mastered": "#10B981"
            },
            labels={'topic': 'GRE Subtopic', 'accuracy_pct': 'Accuracy (%)', 'mastery_rating': 'Status'},
            height=380
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0F172A"),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_matrix:
        st.subheader("🚨 Focus Area Priority List")
        weak_df = df.sort_values('accuracy_pct')
        st.dataframe(
            weak_df[['topic', 'accuracy_pct', 'total_attempts', 'avg_speed_seconds']],
            column_config={
                "topic": "Topic Name",
                "accuracy_pct": st.column_config.ProgressColumn("Accuracy", format="%.1f%%", min_value=0, max_value=100),
                "total_attempts": st.column_config.NumberColumn("Attempts"),
                "avg_speed_seconds": st.column_config.NumberColumn("Avg Speed", format="%ds")
            },
            hide_index=True,
            use_container_width=True
        )
