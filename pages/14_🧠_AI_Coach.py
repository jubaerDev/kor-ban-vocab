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


def _start_session(word_list_text, label):
    first_message = f"My vocabulary list is:\n\n{word_list_text.strip()}"
    with st.spinner(f"AI {label} বিশ্লেষণ করছে..."):
        try:
            reply, engine = send_coach_message([], first_message)
            st.session_state["coach_history"] = [
                {"role": "user", "content": first_message},
                {"role": "assistant", "content": reply},
            ]
            st.session_state["coach_engine"] = engine
            st.session_state["coach_label"] = label
            st.rerun()
        except Exception as e:
            st.error(f"শুরু করা যায়নি: {e}")


# ---------- Session শুরু করা ----------
if not st.session_state["coach_history"]:
    st.subheader("📖 পুরো একটা Chapter নিয়ে Session শুরু করো")
    st.caption("Chapter বেছে নিলেই সেই chapter এর সব word নিয়ে সাথে সাথে session শুরু হয়ে যাবে।")

    try:
        chapters = get_all_chapter_numbers()
    except Exception:
        chapters = []

    if not chapters:
        st.info("এখনো কোনো chapter upload হয়নি।")
    else:
        selected_chapter = st.selectbox("Chapter বেছে নাও", chapters, format_func=lambda c: f"Chapter {c}")

        try:
            chapter_words = get_words_by_chapter(selected_chapter)
        except Exception as e:
            chapter_words = []
            st.error(f"Word লোড করা যায়নি: {e}")

        st.write(f"এই Chapter এ **{len(chapter_words)}** টা word আছে।")

        if len(chapter_words) > 60:
            st.warning(
                "⚠️ এতগুলো word একসাথে দিলে AI প্রথম response এ শুধু group/analysis দেখাবে "
                "(ধাপে ধাপে শেখাবে), কিন্তু response অনেক বড় হতে পারে। চাইলে নিচে থেকে "
                "chapter-কে ছোট অংশে ভাগ করেও শুরু করতে পারো।"
            )

        if st.button(f"🚀 পুরো Chapter {selected_chapter} নিয়ে Session শুরু করো", type="primary", disabled=not chapter_words):
            word_list_text = "\n".join(w["korean_word"] for w in chapter_words)
            _start_session(word_list_text, f"Chapter {selected_chapter}")

    st.divider()
    with st.expander("✏️ অথবা নিজের মতো word list Paste করো (custom)"):
        pasted = st.text_area(
            "Korean word list (একটা লাইনে একটা word)",
            height=180,
            placeholder="토목\n시공\n상수도관\n설치하다\n주의하다\n누수\n...",
        )
        if st.button("🚀 এই Custom List দিয়ে Session শুরু করো", disabled=not pasted.strip()):
            _start_session(pasted, "custom list")

# ---------- চলমান Session (chat UI) ----------
else:
    label = st.session_state.get("coach_label", "")
    engine = st.session_state.get("coach_engine", "")
    st.caption(f"চলছে: {label} | AI engine: {engine}")

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
        st.session_state.pop("coach_label", None)
        st.rerun()
