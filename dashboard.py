import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from db_manager import DB_PATH

st.set_page_config(page_title="English Progress Dashboard", layout="wide")

def get_data():
    conn = sqlite3.connect(DB_PATH)
    words_df = pd.read_sql_query("SELECT * FROM words", conn)
    activity_df = pd.read_sql_query("SELECT * FROM activity_log ORDER BY date", conn)
    conn.close()
    return words_df, activity_df

st.title("📈 English Improvement Dashboard")

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

# Activity Chart
st.subheader("Daily Accuracy Trend")
if not activity_df.empty:
    activity_df['accuracy'] = (activity_df['correct_answers'] / activity_df['words_practiced']) * 100
    st.line_chart(activity_df.set_index('date')['accuracy'])
else:
    st.info("Start practicing to see your progress chart!")

# Word Analysis
st.subheader("Words Needing Focus")
if not words_df.empty:
    # Filter for words tested at least once
    tested_words = words_df[words_df['times_tested'] > 0].copy()
    if not tested_words.empty:
        tested_words['accuracy'] = (tested_words['times_correct'] / tested_words['times_tested']) * 100
        worst_words = tested_words.sort_values(by='accuracy').head(10)
        st.table(worst_words[['english_word', 'thai_translation', 'times_tested', 'accuracy']])
    else:
        st.write("Practiced words will appear here.")
else:
    st.write("Database is empty.")

# Refresh button
if st.button("Refresh Data"):
    st.rerun()
