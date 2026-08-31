import streamlit as st
import pandas as pd
import plotly.express as px
import gre_platform_merged as db_manager
from ui import components

def render_analytics_dashboard() -> None:
    st.header("📊 Performance & Analytics Dashboard")
    st.markdown("Track your GRE mastery, identify weak points, and monitor your pacing.")

    # Fetch data efficiently in one block
    with db_manager.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM tests WHERE status = 'completed'")
        completed_tests = cur.fetchone()["c"]
        
        cur.execute("""
            SELECT topic, accuracy_pct, total_attempts, avg_speed_seconds, mastery_rating 
            FROM user_performance 
            ORDER BY accuracy_pct ASC
        """)
        perf_data = cur.fetchall()

    # Top Level Metric Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        components.render_score_card("Completed Exams", str(completed_tests), "Full & Section Tests")
    with c2:
        components.render_score_card("Topics Tracked", str(len(perf_data)), "Across Quant & Verbal")
    with c3:
        overall_acc = sum(r['accuracy_pct'] for r in perf_data) / len(perf_data) if perf_data else 0
        components.render_score_card("Overall Accuracy", f"{overall_acc:.1f}%", "All Time")

    st.divider()

    if not perf_data:
        st.info("💡 Complete a practice test to unlock deep analytics, interactive charts, and weakness tracking.")
        return

    # Convert to Pandas DataFrame for advanced visualization
    df = pd.DataFrame([dict(r) for r in perf_data])
    
    # Fill any missing mastery ratings safely
    if 'mastery_rating' not in df.columns or df['mastery_rating'].isnull().all():
        df['mastery_rating'] = 'weak'
    else:
        df['mastery_rating'] = df['mastery_rating'].fillna('weak')

    # 1. Interactive Bar Chart
    st.subheader("🎯 Accuracy by Topic")
    fig = px.bar(
        df, 
        x='topic', 
        y='accuracy_pct', 
        color='mastery_rating',
        color_discrete_map={
            "weak": "#dc3545",        # Red
            "developing": "#ffc107",  # Yellow
            "proficient": "#17a2b8",  # Blue
            "mastered": "#28a745"     # Green
        },
        labels={'topic': 'GRE Topic', 'accuracy_pct': 'Accuracy (%)', 'mastery_rating': 'Mastery Level'},
        height=400
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # 2. Advanced Data Table with Visual Progress Bars
    st.subheader("🚨 Critical Weaknesses Matrix")
    weak_df = df[df['accuracy_pct'] < 80].sort_values('accuracy_pct')
    
    if not weak_df.empty:
        st.dataframe(
            weak_df[['topic', 'accuracy_pct', 'total_attempts', 'avg_speed_seconds']],
            column_config={
                "topic": st.column_config.TextColumn("Topic", width="medium"),
                "accuracy_pct": st.column_config.ProgressColumn(
                    "Accuracy", 
                    help="Target: 80%+", 
                    format="%.1f%%", 
                    min_value=0, 
                    max_value=100
                ),
                "total_attempts": st.column_config.NumberColumn("Questions Attempted", alignment="center"),
                "avg_speed_seconds": st.column_config.NumberColumn("Avg Time (sec)", format="%d s", alignment="center")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("🎉 Great job! You have no topics currently below 80% accuracy.")
