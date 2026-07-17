import streamlit as st
from utils.db import get_all_chapter_numbers, delete_chapter, rebuild_database, get_chapters_log

st.set_page_config(page_title="Manage Chapters", page_icon="🗑️")
st.title("🗑️ Chapter মুছে ফেলা / Rebuild")

try:
    chapters = get_all_chapter_numbers()
except Exception as e:
    st.error("Database থেকে chapter list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not chapters:
    st.info("এখনো কোনো chapter save হয়নি।")
    st.stop()

st.subheader("একটা Chapter মুছে ফেলো")
selected = st.selectbox("কোন chapter মুছবে?", sorted(chapters))
st.warning(
    f"⚠️ এটা Chapter {selected} এর সব word স্থায়ীভাবে মুছে ফেলবে এবং পুরো database rebuild করবে। "
    "এই কাজ ফেরানো যাবে না।"
)
confirm = st.checkbox(f"হ্যাঁ, আমি নিশ্চিত Chapter {selected} মুছে ফেলতে চাই")

if st.button("🗑️ Delete Chapter", type="primary", disabled=not confirm):
    with st.spinner("মুছে ফেলা হচ্ছে এবং database rebuild হচ্ছে..."):
        delete_chapter(selected)
    st.success(f"Chapter {selected} মুছে ফেলা হয়েছে এবং database rebuild হয়ে গেছে ✅")
    st.rerun()

st.divider()
st.subheader("Manual Rebuild")
st.write(
    "সাধারণত rebuild automatic হয়ে যায় (upload বা delete করলে)। "
    "কোনো কারণে data ঠিক না লাগলে এখানে চাপলে জোর করে পুরো database recalculate হবে।"
)
if st.button("🔄 এখনই পুরো Database Rebuild করো"):
    with st.spinner("Rebuild চলছে..."):
        rebuild_database()
    st.success("Rebuild সম্পন্ন ✅")
    st.rerun()

st.divider()
st.subheader("বর্তমান Chapter List")
log = get_chapters_log()
st.dataframe(
    [{"Chapter": r["chapter_number"], "Unique words": r["unique_new_words"]} for r in log]
)
