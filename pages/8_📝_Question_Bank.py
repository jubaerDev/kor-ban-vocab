import streamlit as st
from utils.db import get_question_categories, get_questions_by_category

st.set_page_config(page_title="Question Bank", page_icon="📝", layout="wide")
st.title("📝 Question Bank")

try:
    categories = get_question_categories()
except Exception as e:
    st.error("Database থেকে category list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not categories:
    st.info("এখনো কোনো question যোগ হয়নি। 🗂️ Question Bank Manager page থেকে শুরু করো।")
    st.stop()

selected_category = st.selectbox("Category বেছে নাও", categories)

questions = get_questions_by_category(selected_category)

if not questions:
    st.warning("এই category এ কোনো question নেই।")
    st.stop()

st.caption(f"এই category তে মোট {len(questions)} টা question")
st.divider()

for idx, q in enumerate(questions, start=1):
    st.markdown(f"### {idx}. {q['question_text']}")

    options = [q["option1"], q["option2"], q["option3"], q["option4"]]
    choice_key = f"choice_{q['id']}"
    show_key = f"show_{q['id']}"

    st.radio(
        "উত্তর বেছে নাও",
        options=[1, 2, 3, 4],
        format_func=lambda x, opts=options: f"{x}. {opts[x-1]}",
        key=choice_key,
        label_visibility="collapsed",
    )

    show_explanation = st.checkbox("✅ ব্যাখ্যা/সঠিক answer দেখাও", key=show_key)

    if show_explanation:
        user_choice = st.session_state.get(choice_key)
        correct = q["correct_answer"]
        if user_choice == correct:
            st.success(f"✅ সঠিক! Answer: {correct}. {options[correct-1]}")
        else:
            st.error(f"❌ ভুল। সঠিক Answer: {correct}. {options[correct-1]}")
        if q.get("explanation"):
            st.info(f"**ব্যাখ্যা:** {q['explanation']}")

    st.divider()
