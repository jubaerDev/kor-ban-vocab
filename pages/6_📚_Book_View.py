import streamlit as st
from utils.db import get_book_chapters, get_chapter_paragraphs, delete_paragraph

st.set_page_config(page_title="Book View", page_icon="📚", layout="wide")
st.title("📚 বই আকারে দেখো")

try:
    chapters = get_book_chapters()
except Exception as e:
    st.error("Database থেকে chapter list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not chapters:
    st.info("এখনো কোনো paragraph save হয়নি। 📖 Paragraph Translator page থেকে শুরু করো।")
    st.stop()

selected = st.selectbox("Chapter বেছে নাও", chapters)

paragraphs = get_chapter_paragraphs(selected)

if not paragraphs:
    st.warning("এই chapter এ কোনো paragraph নেই।")
    st.stop()

chapter_title = paragraphs[0].get("chapter_title") or ""

st.markdown(f"<h2 style='text-align:center'>Chapter: {selected:02d}</h2>", unsafe_allow_html=True)
if chapter_title:
    st.markdown(f"<h4 style='text-align:center'>{chapter_title}</h4>", unsafe_allow_html=True)
st.divider()

current_heading = None
for p in paragraphs:
    if p.get("heading") and p["heading"] != current_heading:
        current_heading = p["heading"]
        st.markdown(f"### {current_heading}")

    label = p.get("paragraph_label") or ""
    st.markdown(f"**{label}:**")
    st.write(p["annotated_text"])

    with st.expander("✏️ Edit / 🗑️ Delete"):
        st.text_area("Korean মূল text", value=p["korean_original"], disabled=True, key=f"ko_{p['id']}")
        if st.button("🗑️ এই Paragraph মুছে ফেলো", key=f"del_{p['id']}"):
            delete_paragraph(p["id"])
            st.success("মুছে ফেলা হয়েছে ✅")
            st.rerun()

    st.markdown("")

st.divider()
full_text = f"Chapter: {selected:02d}\n{chapter_title}\n\n" + "\n\n".join(
    f"{p.get('heading','')}\n{p.get('paragraph_label','')}:\n{p['annotated_text']}" for p in paragraphs
)
st.download_button(
    "⬇️ পুরো Chapter টেক্সট হিসেবে Download করো",
    data=full_text.encode("utf-8-sig"),
    file_name=f"chapter_{selected}_book.txt",
    mime="text/plain",
)
