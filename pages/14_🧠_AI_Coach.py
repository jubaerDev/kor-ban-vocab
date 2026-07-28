import streamlit as st
from utils.ai_coach import send_coach_message
from utils.db import get_all_chapter_numbers, get_words_by_chapter

st.set_page_config(page_title="AI Vocabulary Coach", page_icon="🧠", layout="wide")
st.title("🧠 AI Vocabulary Coach")
st.caption(
    "Polyglot + Active Recall + Spaced Repetition পদ্ধতিতে word শেখাবে — শুধু অর্থ মুখস্থ না করিয়ে, "
    "association/story/quiz দিয়ে ধাপে ধাপে (Phase 1 → 7) শেখাবে।"
)

if "coach_history" not in st.session_state:
    st.session_state["coach_history"] = []

# ---------- Session শুরু করা (word list দিয়ে) ----------
if not st.session_state["coach_history"]:
    st.subheader("নতুন Session শুরু করো")

    try:
        chapters = get_all_chapter_numbers()
    except Exception:
        chapters = []

    col1, col2 = st.columns([1, 2])
    use_chapter = col1.checkbox("Chapter থেকে word নাও")
    word_list_text = ""

    if use_chapter and chapters:
        selected_chapter = col1.selectbox("Chapter", chapters)
        if col1.button("📥 এই Chapter এর word লোড করো"):
            words = get_words_by_chapter(selected_chapter)
            word_list_text = "\n".join(w["korean_word"] for w in words)
            st.session_state["coach_word_draft"] = word_list_text

    default_text = st.session_state.get("coach_word_draft", "")
    pasted = col2.text_area(
        "Korean word list (একটা লাইনে একটা word)",
        value=default_text,
        height=200,
        placeholder="토목\n시공\n상수도관\n설치하다\n주의하다\n누수\n...",
    )

    if st.button("🚀 Session শুরু করো", type="primary", disabled=not pasted.strip()):
        first_message = f"My vocabulary list is:\n\n{pasted.strip()}"
        with st.spinner("AI পুরো list বিশ্লেষণ করছে..."):
            try:
                reply, engine = send_coach_message([], first_message)
                st.session_state["coach_history"] = [
                    {"role": "user", "content": first_message},
                    {"role": "assistant", "content": reply},
                ]
                st.session_state["coach_engine"] = engine
                st.rerun()
            except Exception as e:
                st.error(f"শুরু করা যায়নি: {e}")

# ---------- চলমান Session (chat UI) ----------
else:
    if st.session_state.get("coach_engine"):
        st.caption(f"AI engine: {st.session_state['coach_engine']}")

    for msg in st.session_state["coach_history"]:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"])

    user_input = st.chat_input("তোমার উত্তর লেখো, বা 'NEXT' লিখে পরের ধাপে যাও...")
    if user_input:
        st.session_state["coach_history"].append({"role": "user", "content": user_input})
        with st.spinner("AI ভাবছে..."):
            try:
                reply, engine = send_coach_message(
                    st.session_state["coach_history"][:-1], user_input
                )
                st.session_state["coach_history"].append({"role": "assistant", "content": reply})
                st.session_state["coach_engine"] = engine
            except Exception as e:
                st.session_state["coach_history"].append(
                    {"role": "assistant", "content": f"⚠️ Error: {e}"}
                )
        st.rerun()

    st.divider()
    if st.button("🔄 নতুন Session শুরু করো (এই session মুছে যাবে)"):
        st.session_state["coach_history"] = []
        st.session_state.pop("coach_word_draft", None)
        st.rerun()
