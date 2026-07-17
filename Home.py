import streamlit as st
from utils.db import get_chapters_log, get_all_words

st.set_page_config(page_title="Korean-Bangla Vocab Tracker", page_icon="📚", layout="wide")

st.title("📚 Korean → Bangla Vocabulary Tracker")
st.write(
    "প্রতিটা chapter upload করলে আগের সব chapter এর সাথে compare করে "
    "শুধু নতুন/unique word বের করে রাখা হয়। বাম পাশের sidebar থেকে page বেছে নাও।"
)

try:
    log = get_chapters_log()
    words = get_all_words()

    col1, col2 = st.columns(2)
    col1.metric("মোট Chapter আপলোড হয়েছে", len(log))
    col2.metric("মোট Unique শব্দ (সব চ্যাপ্টার মিলিয়ে)", len(words))
except Exception as e:
    st.warning("Database এর সাথে connect করা যায়নি। `.streamlit/secrets.toml` এ SUPABASE_URL এবং SUPABASE_KEY ঠিকভাবে দেওয়া আছে কিনা check করো।")
    st.caption(f"Error detail: {e}")

st.divider()
st.subheader("Pages")
st.markdown(
    """
- **📤 Upload Chapter** — নতুন chapter এর Excel/CSV upload করে unique word বের করো
- **📊 Dashboard** — chapter-wise stats ও growth দেখো
- **📂 Browse History** — আগের যেকোনো chapter এর data দেখো/download করো
"""
)
