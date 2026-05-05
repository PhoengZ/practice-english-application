import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# Ensure we can import from src when running from any directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.db_manager import DB_PATH

st.set_page_config(page_title="English Progress Dashboard", layout="wide")

@st.cache_data(ttl=600)
def get_data():
    """Fetches data from the database with caching."""
    try:
        if not os.path.exists(DB_PATH):
            return pd.DataFrame(), pd.DataFrame()
            
        with sqlite3.connect(DB_PATH) as conn:
            words_df = pd.read_sql_query("SELECT * FROM words", conn)
            activity_df = pd.read_sql_query("SELECT * FROM activity_log ORDER BY date", conn)
        return words_df, activity_df
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return pd.DataFrame(), pd.DataFrame()

st.title("📈 English Improvement Dashboard")
st.markdown("Track your learning progress and identify areas for improvement.")

words_df, activity_df = get_data()

if words_df.empty and activity_df.empty:
    st.warning("Database is empty or not found. Please ingest some words and start practicing!")
    st.stop()

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Words in DB", len(words_df))
with col2:
    total_practiced = words_df['times_tested'].sum()
    st.metric("Total Practice Count", int(total_practiced))
with col3:
    if total_practiced > 0:
        overall_acc = (words_df['times_correct'].sum() / total_practiced) * 100
    else:
        overall_acc = 0
    st.metric("Overall Accuracy", f"{overall_acc:.1f}%")

# Main Dashboard Layout
tab1, tab2, tab3 = st.tabs(["Daily Trends", "Word Analysis", "Learning Pattern Analysis"])

with tab1:
    st.subheader("Daily Accuracy & Activity Trend")
    if not activity_df.empty:
        # Avoid division by zero
        activity_df['accuracy'] = activity_df.apply(
            lambda x: (x['correct_answers'] / x['words_practiced'] * 100) if x['words_practiced'] > 0 else 0, 
            axis=1
        )
        
        # Plotly Interactive Line Chart
        fig = px.line(activity_df, x='date', y='accuracy', 
                      title='Daily Accuracy (%)',
                      labels={'accuracy': 'Accuracy (%)', 'date': 'Date'},
                      markers=True)
        fig.update_layout(yaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)
        
        # Bar chart for words practiced
        fig2 = px.bar(activity_df, x='date', y='words_practiced',
                      title='Words Practiced Per Day',
                      labels={'words_practiced': 'Count', 'date': 'Date'},
                      color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Start practicing to see your progress chart!")

with tab2:
    st.subheader("Word Performance Analysis")
    # Filter for words tested at least once
    tested_words = words_df[words_df['times_tested'] > 0].copy()
    if not tested_words.empty:
        tested_words['accuracy'] = (tested_words['times_correct'] / tested_words['times_tested']) * 100
        
        # Worst 10 words (Interactive Bar Chart)
        worst_words = tested_words.sort_values(by=['accuracy', 'times_tested'], ascending=[True, False]).head(10)
        
        fig3 = px.bar(worst_words, x='accuracy', y='english_word',
                      orientation='h',
                      title='Top 10 Words Needing Focus (Lowest Accuracy)',
                      labels={'accuracy': 'Accuracy (%)', 'english_word': 'Word'},
                      color='accuracy',
                      color_continuous_scale='Reds_r',
                      text=worst_words['thai_translation'])
        fig3.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown("### Detailed Word Statistics")
        st.dataframe(tested_words[['english_word', 'word_type', 'word_level', 'thai_translation', 'times_tested', 'times_correct', 'accuracy']]
                     .sort_values(by='accuracy')
                     .style.format({'accuracy': '{:.1f}%'}))
    else:
        st.info("Practiced words will appear here once you start your first session.")

with tab3:
    st.subheader("🕵️ Learning Pattern Analysis (Advanced Insights)")
    st.markdown("""
    หน้านี้ใช้อัลกอริทึมในการวิเคราะห์รูปแบบความผิดพลาด เพื่อค้นหา 'คำที่เป็นอุปสรรค' ต่อการเรียนรู้ของคุณ 
    (This page uses algorithms to analyze mistake patterns to find 'obstacle words' in your learning.)
    """)
    
    tested_words = words_df[words_df['times_tested'] > 0].copy()
    if not tested_words.empty:
        tested_words['accuracy'] = (tested_words['times_correct'] / tested_words['times_tested']) * 100
        tested_words['mistake_count'] = tested_words['times_tested'] - tested_words['times_correct']
        
        # --- Algorithm 1: DBSCAN Clustering ---
        st.markdown("### 1. DBSCAN Clustering: การจัดกลุ่มระดับความยาก (Grouping Difficulty Levels)")
        st.info("""
        **DBSCAN** ถูกใช้เพื่อจัดกลุ่มคำตามความถี่ในการทดสอบและความแม่นยำ ช่วยให้แยกแยะได้ว่าคำไหนเป็นคำที่ยากจริงๆ หรือคำที่สุ่มผิด
        """)
        
        # Prepare data for clustering
        if len(tested_words) >= 5:
            X = tested_words[['times_tested', 'accuracy']].values
            X_scaled = StandardScaler().fit_transform(X)
            
            # Apply DBSCAN
            db = DBSCAN(eps=0.5, min_samples=3).fit(X_scaled)
            tested_words['cluster'] = db.labels_
        else:
            # Fallback if not enough data for clustering
            tested_words['cluster'] = 0
        
        # Map clusters to meaningful names based on cluster-wide statistics
        cluster_stats = {}
        if 'cluster' in tested_words and (tested_words['cluster'] != -1).any():
            stats_df = tested_words[tested_words['cluster'] != -1].groupby('cluster').agg({
                'accuracy': 'mean',
                'times_tested': 'mean'
            })
            for c, row in stats_df.iterrows():
                avg_acc = row['accuracy']
                avg_count = row['times_tested']
                
                if avg_acc < 50 and avg_count > 5:
                    label = f"Group {c}: Consistent Struggles (กลุ่มที่ยากต่อเนื่อง)"
                elif avg_acc > 80:
                    label = f"Group {c}: Mastered (กลุ่มที่เชี่ยวชาญแล้ว)"
                else:
                    label = f"Group {c}: Learning Process (กลุ่มที่กำลังเรียนรู้)"
                cluster_stats[c] = label

        def map_cluster(c):
            if c == -1:
                return "Outlier (คำที่ผิดปกติ)"
            return cluster_stats.get(c, "Learning Process (กำลังเรียนรู้)")
            
        tested_words['cluster_desc'] = tested_words['cluster'].apply(map_cluster)
        
        fig_cluster = px.scatter(tested_words, x='times_tested', y='accuracy', 
                                color='cluster_desc',
                                hover_data=['english_word', 'thai_translation'],
                                title="Word Difficulty Clusters (DBSCAN)",
                                labels={'times_tested': 'Times Tested', 'accuracy': 'Accuracy (%)', 'cluster_desc': 'Status'})
        st.plotly_chart(fig_cluster, use_container_width=True)
        
        # --- Algorithm 2: Mistake Density Heatmap ---
        st.markdown("### 2. Mistake Density Heatmap: ความหนาแน่นของข้อผิดพลาด (Heatmap)")
        st.info("""
        แสดงให้เห็นว่าข้อผิดพลาดส่วนใหญ่กระจุกตัวอยู่ที่คำประเภทไหนและระดับไหน ยิ่งสีเข้มแปลว่าคุณผิดในกลุ่มนั้นบ่อยที่สุด
        """)
        
        # Prepare data for heatmap
        mistake_data = tested_words[tested_words['mistake_count'] > 0].copy()
        if not mistake_data.empty:
            pivot_mistakes = mistake_data.groupby(['word_type', 'word_level'])['mistake_count'].sum().reset_index()
            
            fig_heat = px.density_heatmap(pivot_mistakes, x="word_level", y="word_type", z="mistake_count",
                                         color_continuous_scale="YlOrRd",
                                         title="Heatmap of Total Mistakes by Type and Level",
                                         labels={'mistake_count': 'Total Mistakes', 'word_level': 'Level', 'word_type': 'Type'},
                                         text_auto=True)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.write("No mistakes recorded yet to generate heatmap.")
            
        # Summary & Recommendations
        st.markdown("### 💡 บทสรุปและคำแนะนำ (Summary & Recommendations)")
        
        if tested_words['mistake_count'].sum() > 0:
            top_mistake_type = tested_words.groupby('word_type')['mistake_count'].sum().idxmax()
            top_mistake_level = tested_words.groupby('word_level')['mistake_count'].sum().idxmax()
            
            st.success(f"""
            - **จุดที่ต้องระวังที่สุด (Biggest Weakness):** คำประเภท **{top_mistake_type}** ที่ระดับ **{top_mistake_level}**
            - **คำแนะนำ (Recommendation):** ควรเน้นฝึกฝนคำในกลุ่มนี้เป็นพิเศษผ่านระบบ Practice โดยใช้โหมดเน้นย้ำ
            """)
        else:
            st.success("""
            - **ยอดเยี่ยมมาก! (Excellent!):** คุณยังไม่มีข้อผิดพลาดที่บันทึกไว้ในระบบ
            - **คำแนะนำ (Recommendation):** เรียนรู้คำศัพท์ใหม่ๆ ต่อไปเพื่อเพิ่มพูนความรู้
            """)
        
    else:
        st.warning("ไม่มีข้อมูลการฝึกฝนเพียงพอสำหรับการวิเคราะห์ (Insufficient practice data for analysis.)")

# Sidebar Controls
with st.sidebar:
    st.header("Settings & Data")
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.write("Current Logical Day:", pd.to_datetime('today').strftime('%Y-%m-%d'))
    
    if st.checkbox("Show Raw Word Data"):
        st.write(words_df)

