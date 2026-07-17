import pandas as pd
import streamlit as st
from utils.db import get_all_chapter_numbers, get_words_by_chapter

st.set_page_config(page_title="Browse History", page_icon="📂")
st.title("📂 আগের Chapter গুলো দেখো")

try:
    chapters = get_all_chapter_numbers()
except Exception as e:
    st.error("Database থেকে chapter list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not chapters:
    st.info("এখনো কোনো chapter save হয়নি।")
    st.stop()

selected = st.selectbox("Chapter বেছে নাও", sorted(chapters))

rows = get_words_by_chapter(selected)
df = pd.DataFrame(rows)

if df.empty:
    st.warning("এই chapter এ কোনো word পাওয়া যায়নি।")
else:
    st.write(f"**Chapter {selected}** — {len(df)} টা unique word")
    st.dataframe(df[["korean_word", "bangla_meaning", "date_added"]])

    csv_bytes = df[["korean_word", "bangla_meaning"]].to_csv(
        index=False, header=["Korean word", "Bangla word"]
    ).encode("utf-8-sig")
    st.download_button("⬇️ CSV Download", data=csv_bytes, file_name=f"chapter_{selected}_unique.csv", mime="text/csv")
