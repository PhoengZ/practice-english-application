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
import seaborn as sns
import matplotlib.pyplot as plt

# Ensure we can import from src when running from any directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.db_manager import DB_PATH

st.set_page_config(page_title="English Progress Dashboard", layout="wide")

def get_data():
    conn = sqlite3.connect(DB_PATH)
    words_df = pd.read_sql_query("SELECT * FROM words", conn)
    activity_df = pd.read_sql_query("SELECT * FROM activity_log ORDER BY date", conn)
    conn.close()
    return words_df, activity_df

st.title("📈 English Improvement Dashboard")
st.markdown("Track your learning progress and identify areas for improvement.")

words_df, activity_df = get_data()

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
tab1, tab2, tab3 = st.tabs(["Daily Trends", "Word Analysis", "Mistake Pattern (Fraud Detection)"])

with tab1:
    st.subheader("Daily Accuracy & Activity Trend")
    if not activity_df.empty:
        activity_df['accuracy'] = (activity_df['correct_answers'] / activity_df['words_practiced']) * 100
        
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
    if not words_df.empty:
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
            st.write("Practiced words will appear here.")
    else:
        st.write("Database is empty.")

with tab3:
    st.subheader("🕵️ Mistake Pattern Analysis (Fraud Detection)")
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
        **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** 
        ถูกใช้เพื่อจัดกลุ่มคำตามความถี่ในการทดสอบและความแม่นยำ ช่วยให้แยกแยะได้ว่าคำไหนเป็นคำที่ยากจริงๆ หรือคำที่สุ่มผิด
        (Used to group words by frequency and accuracy, helping distinguish truly difficult words from random errors.)
        """)
        
        # Prepare data for clustering
        if len(tested_words) >= 5:
            X = tested_words[['times_tested', 'accuracy']].values
            X_scaled = StandardScaler().fit_transform(X)
            
            # Apply DBSCAN
            db = DBSCAN(eps=0.5, min_samples=5).fit(X_scaled)
            tested_words['cluster'] = db.labels_
        else:
            # Fallback if not enough data for clustering
            tested_words['cluster'] = 0
        
        # Map clusters to meaningful names
        def map_cluster(c, acc, count):
            if c == -1: return "Outlier (คำที่ผิดปกติ)"
            if acc < 50 and count > 10: return "Consistent Struggles (ยากต่อเนื่อง)"
            if acc > 80: return "Mastered (เชี่ยวชาญแล้ว)"
            return "Learning Process (กำลังเรียนรู้)"
            
        tested_words['cluster_desc'] = tested_words.apply(lambda x: map_cluster(x['cluster'], x['accuracy'], x['times_tested']), axis=1)
        
        fig_cluster = px.scatter(tested_words, x='times_tested', y='accuracy', 
                                color='cluster_desc',
                                hover_data=['english_word', 'thai_translation'],
                                title="Word Difficulty Clusters (DBSCAN)",
                                labels={'times_tested': 'Times Tested', 'accuracy': 'Accuracy (%)', 'cluster_desc': 'Status'})
        st.plotly_chart(fig_cluster, use_container_width=True)
        
        # --- Algorithm 2: KDE Heatmap ---
        st.markdown("### 2. Kernel Density Estimation (KDE): ความหนาแน่นของข้อผิดพลาด (Mistake Density)")
        st.info("""
        **KDE (Kernel Density Estimation)** ช่วยแสดงให้เห็นว่าข้อผิดพลาดส่วนใหญ่กระจุกตัวอยู่ที่คำประเภทไหนและระดับไหน 
        ยิ่งสีเข้มแปลว่าคุณผิดในกลุ่มนั้นบ่อยที่สุด
        (Shows where most mistakes are concentrated by word type and level. Darker areas mean more frequent errors.)
        """)
        
        # Prepare data for heatmap
        mistake_data = tested_words[tested_words['mistake_count'] > 0].copy()
        if not mistake_data.empty:
            pivot_mistakes = mistake_data.groupby(['word_type', 'word_level'])['mistake_count'].sum().unstack(fill_value=0)
            
            fig_kde, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(pivot_mistakes, annot=True, fmt="d", cmap="YlOrRd", ax=ax)
            ax.set_title("Heatmap of Total Mistakes by Type and Level")
            ax.set_xlabel("Word Level")
            ax.set_ylabel("Word Type")
            st.pyplot(fig_kde)
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
        st.rerun()
    
    st.divider()
    st.write("Current Logical Day:", pd.to_datetime('today').strftime('%Y-%m-%d'))
    
    if st.checkbox("Show Raw Word Data"):
        st.write(words_df)
