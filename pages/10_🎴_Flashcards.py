import random
import streamlit as st
from utils.db import get_due_flashcards, update_flashcard_progress, get_flashcard_stats, get_all_chapter_numbers

st.set_page_config(page_title="Flashcards", page_icon="🎴", layout="wide")
st.title("🎴 Flashcard Practice")
st.caption(
    "সঠিক বললে word পরের box এ যাবে (কম ঘন ঘন দেখাবে), ভুল হলে আবার প্রথম box এ ফিরে যাবে "
    "(পরদিনই আবার দেখাবে) — এভাবে যেগুলো জানো সেগুলোর সময় কম যাবে, যেগুলো জানো না সেগুলো বেশি দেখবে।"
)

try:
    stats = get_flashcard_stats()
    chapters = get_all_chapter_numbers()
except Exception as e:
    st.error("Database থেকে data আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("মোট Track করা Word", stats["total_tracked"])
col2.metric("✅ Mastered (Box 6)", stats["mastered"])

chapter_filter = st.selectbox("Chapter বেছে নাও (ঐচ্ছিক)", ["সব Chapter"] + chapters)
selected_chapter = None if chapter_filter == "সব Chapter" else chapter_filter

if st.button("🔄 নতুন Session শুরু করো", type="primary"):
    due = get_due_flashcards(selected_chapter)
    random.shuffle(due)
    st.session_state["fc_queue"] = due
    st.session_state["fc_index"] = 0
    st.session_state["fc_show_answer"] = False
    st.session_state["fc_correct_count"] = 0
    st.session_state["fc_wrong_count"] = 0

if "fc_queue" in st.session_state:
    queue = st.session_state["fc_queue"]
    idx = st.session_state["fc_index"]

    col3.metric("আজকের জন্য বাকি", max(len(queue) - idx, 0))

    if idx >= len(queue):
        st.success("🎉 আজকের জন্য সব শেষ!")
        st.write(
            f"✅ সঠিক: {st.session_state['fc_correct_count']} | "
            f"❌ ভুল: {st.session_state['fc_wrong_count']}"
        )
    elif not queue:
        st.info("এই মুহূর্তে review করার মতো কোনো word নেই — সব up-to-date! 🎉")
    else:
        card = queue[idx]
        st.divider()
        st.markdown(f"<h1 style='text-align:center'>{card['korean_word']}</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align:center; color:gray'>Chapter {card['chapter_number']} | Box {card['box_level']}</p>",
            unsafe_allow_html=True,
        )

        if not st.session_state["fc_show_answer"]:
            c1, c2, c3 = st.columns([1, 1, 1])
            if c2.button("👁️ উত্তর দেখাও", type="primary", use_container_width=True):
                st.session_state["fc_show_answer"] = True
                st.rerun()
        else:
            st.markdown(
                f"<h2 style='text-align:center; color:#2e7d32'>{card['bangla_meaning']}</h2>",
                unsafe_allow_html=True,
            )
            st.write("")
            c1, c2 = st.columns(2)

            def _next_card(correct):
                update_flashcard_progress(card["korean_word"], card["chapter_number"], correct)
                if correct:
                    st.session_state["fc_correct_count"] += 1
                else:
                    st.session_state["fc_wrong_count"] += 1
                st.session_state["fc_index"] += 1
                st.session_state["fc_show_answer"] = False

            if c1.button("❌ জানতাম না", use_container_width=True):
                _next_card(False)
                st.rerun()
            if c2.button("✅ ঠিক বলেছিলাম", use_container_width=True):
                _next_card(True)
                st.rerun()
else:
    st.info("উপরে **'🔄 নতুন Session শুরু করো'** বাটনে চাপো শুরু করার জন্য।")
