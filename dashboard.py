import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db_manager import DB_PATH

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
tab1, tab2 = st.tabs(["Daily Trends", "Word Analysis"])

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

# Sidebar Controls
with st.sidebar:
    st.header("Settings & Data")
    if st.button("Refresh Data", use_container_width=True):
        st.rerun()
    
    st.divider()
    st.write("Current Logical Day:", pd.to_datetime('today').strftime('%Y-%m-%d'))
    
    if st.checkbox("Show Raw Word Data"):
        st.write(words_df)
