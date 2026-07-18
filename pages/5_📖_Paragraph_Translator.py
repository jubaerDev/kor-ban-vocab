import streamlit as st
from utils.db import get_all_words, save_paragraph, get_book_chapters
from utils.translator import annotate_paragraph
from utils.auth import require_admin

st.set_page_config(page_title="Paragraph Translator", page_icon="📖", layout="wide")
require_admin()
st.title("📖 Paragraph Translator")
st.caption(
    "Korean paragraph paste করো — AI (Gemini/Anthropic) দিয়ে annotate করবে। "
    "Save করার আগে ফলাফল ঠিকমতো check/edit করে নিও।"
)

col1, col2 = st.columns(2)
try:
    existing_chapters = get_book_chapters()
except Exception:
    existing_chapters = []
suggested_chapter = (max(existing_chapters) + 1) if existing_chapters else 1

chapter_number = col1.number_input("Chapter নাম্বার", min_value=1, step=1, value=suggested_chapter)
chapter_title = col2.text_input("Chapter Title", placeholder="যেমন: 한국의 인사 예절 (কোরিয়ার অভিবাদন শিষ্টাচার)")

heading = st.text_input("Heading / উপশিরোনাম (থাকলে)", placeholder="ঐচ্ছিক")
paragraph_label = st.text_input("Paragraph Label", value="অনুচ্ছেদ ১")

korean_text = st.text_area("Korean Paragraph পেস্ট করো", height=150, placeholder="한국에서는 상대에 따라 인사하는 방식이 다릅니다...")

use_fallback = st.checkbox("AI কাজ না করলে rule-based fallback ব্যবহার করো (শেষ উপায়, কম accurate)", value=False)
use_vocab = st.checkbox(
    "আমাদের word database AI কে দাও (uncheck করলে Gemini সম্পূর্ণ স্বাধীনভাবে translate করবে)",
    value=False,
)

if st.button("🔍 Auto-Annotate করো", type="primary", disabled=not korean_text.strip()):
    with st.spinner("AI দিয়ে annotate করা হচ্ছে..."):
        vocab = get_all_words() if use_vocab else {}
        annotated, unmatched, engine, error_detail = annotate_paragraph(
            korean_text, vocab, use_online_fallback=use_fallback, use_vocab=use_vocab
        )
    st.session_state["annotated_draft"] = annotated
    st.session_state["unmatched"] = unmatched
    st.session_state["engine"] = engine
    st.session_state["error_detail"] = error_detail

if "annotated_draft" in st.session_state:
    engine = st.session_state.get("engine")
    if engine == "anthropic":
        st.success("✅ Anthropic (Claude) দিয়ে annotate হয়েছে")
    elif engine == "gemini":
        st.success("✅ Gemini দিয়ে annotate হয়েছে")
    elif engine == "rule_based":
        st.error(
            "⚠️ AI (Anthropic/Gemini) দুটোই কাজ করেনি, তাই rule-based (কম accurate) পদ্ধতি ব্যবহার হয়েছে।"
        )

    if st.session_state.get("error_detail"):
        with st.expander("🔧 আসল error message দেখো (debug)"):
            st.code(st.session_state["error_detail"])

    st.subheader("ফলাফল (Save করার আগে ঠিক করে নাও)")
    edited = st.text_area("Annotated Text", value=st.session_state["annotated_draft"], height=200, key="edit_box")

    if st.session_state.get("unmatched"):
        st.warning(
            f"❓ চিহ্নিত {len(st.session_state['unmatched'])} টা word এর meaning সরাসরি পাওয়া যায়নি — "
            "উপরে (❓) দেখলে ম্যানুয়ালি ঠিক করে দাও: "
            + ", ".join(st.session_state["unmatched"][:15])
        )

    if st.button("💾 এই Paragraph Save করো"):
        save_paragraph(chapter_number, chapter_title, heading, paragraph_label, korean_text, edited)
        st.success(f"Chapter {chapter_number} — {paragraph_label} save হয়ে গেছে ✅")
        del st.session_state["annotated_draft"]
        st.session_state.pop("unmatched", None)
