import pandas as pd
import streamlit as st
from utils.db import get_chapters_log, get_all_words

st.set_page_config(page_title="Dashboard", page_icon="📊")
st.title("📊 Dashboard")

try:
    log = get_chapters_log()
    words = get_all_words()
except Exception as e:
    st.error("Database থেকে data আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not log:
    st.info("এখনো কোনো chapter upload হয়নি।")
    st.stop()

df = pd.DataFrame(log)

col1, col2, col3 = st.columns(3)
col1.metric("মোট Chapter", len(df))
col2.metric("মোট Unique শব্দ", len(words))
col3.metric("গড় নতুন শব্দ/Chapter", round(df["unique_new_words"].mean(), 1))

st.subheader("Chapter-wise নতুন শব্দের সংখ্যা")
chart_df = df[["chapter_number", "unique_new_words"]].set_index("chapter_number")
st.bar_chart(chart_df)

st.subheader("Cumulative Total (সময়ের সাথে বৃদ্ধি)")
df_sorted = df.sort_values("chapter_number")
df_sorted["cumulative_words"] = df_sorted["unique_new_words"].cumsum()
st.line_chart(df_sorted.set_index("chapter_number")["cumulative_words"])

st.subheader("সব Chapter এর বিস্তারিত")
st.dataframe(df[["chapter_number", "total_words_in_file", "unique_new_words", "upload_date"]])
