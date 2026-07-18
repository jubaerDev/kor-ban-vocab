import streamlit as st
from utils.db import save_question, get_question_categories, get_questions_by_category, delete_question
from utils.qbank_ai import generate_answer

st.set_page_config(page_title="Question Bank Manager", page_icon="🗂️", layout="wide")
st.title("🗂️ Question Bank Manager")
st.caption("প্রশ্ন যোগ করো — AI সঠিক answer বের করে দেবে, চাইলে নিজেও ঠিক করে দিতে পারবে।")

try:
    existing_categories = get_question_categories()
except Exception:
    existing_categories = []

col1, col2 = st.columns([2, 1])
with col1:
    category_choice = st.selectbox(
        "Category বেছে নাও বা নতুন লেখো",
        options=["(নতুন Category লিখবো)"] + existing_categories,
    )
    if category_choice == "(নতুন Category লিখবো)":
        category = st.text_input("নতুন Category এর নাম", placeholder="যেমন: TOPIK Grammar - 았/었")
    else:
        category = category_choice

question_text = st.text_area("Question টেক্সট", placeholder="다음 중 밑줄 친 부분이 맞는 문장을 고르십시오.", height=80)

st.write("**৪টা Option লেখো:**")
o1 = st.text_input("Option 1", key="opt1")
o2 = st.text_input("Option 2", key="opt2")
o3 = st.text_input("Option 3", key="opt3")
o4 = st.text_input("Option 4", key="opt4")
options = [o1, o2, o3, o4]

all_filled = category and question_text.strip() and all(o.strip() for o in options)

if st.button("🤖 AI দিয়ে Answer Generate করো", type="primary", disabled=not all_filled):
    with st.spinner("AI চিন্তা করছে..."):
        try:
            answer, explanation, engine = generate_answer(question_text, options)
            st.session_state["ai_answer"] = answer
            st.session_state["ai_explanation"] = explanation
            st.session_state["ai_engine"] = engine
            st.session_state["ai_error"] = None
        except Exception as e:
            st.session_state["ai_answer"] = None
            st.session_state["ai_explanation"] = ""
            st.session_state["ai_error"] = str(e)

if "ai_answer" in st.session_state:
    if st.session_state.get("ai_error"):
        st.error(f"AI answer generate করা যায়নি — ম্যানুয়ালি দিতে হবে। কারণ: {st.session_state['ai_error']}")
    else:
        st.success(f"✅ AI ({st.session_state['ai_engine']}) সাজেশন পাওয়া গেছে — নিচে চেক করো, দরকার হলে বদলাও")

    default_answer = st.session_state.get("ai_answer") or 1
    st.subheader("চূড়ান্ত Answer (নিশ্চিত/সংশোধন করো)")
    final_answer = st.radio(
        "সঠিক Option কোনটা?",
        options=[1, 2, 3, 4],
        index=default_answer - 1,
        format_func=lambda x: f"{x}. {options[x-1]}",
        horizontal=True,
    )
    final_explanation = st.text_area(
        "ব্যাখ্যা (বাংলা)", value=st.session_state.get("ai_explanation", ""), height=100
    )

    if st.button("💾 Question Save করো"):
        save_question(category, question_text, options, final_answer, final_explanation)
        st.success("Question save হয়ে গেছে ✅")
        for k in ["ai_answer", "ai_explanation", "ai_engine", "ai_error"]:
            st.session_state.pop(k, None)
        st.rerun()

st.divider()
st.subheader("এই Category এর Question গুলো দেখো/মুছো")
if category:
    try:
        qs = get_questions_by_category(category)
    except Exception:
        qs = []
    if not qs:
        st.info("এই category এ এখনো কোনো question নেই।")
    for q in qs:
        with st.expander(f"Q{q['id']}: {q['question_text'][:50]}..."):
            st.write(f"1. {q['option1']}")
            st.write(f"2. {q['option2']}")
            st.write(f"3. {q['option3']}")
            st.write(f"4. {q['option4']}")
            st.write(f"**সঠিক answer:** {q['correct_answer']}")
            st.write(f"**ব্যাখ্যা:** {q.get('explanation') or '(নেই)'}")
            if st.button("🗑️ মুছে ফেলো", key=f"del_q_{q['id']}"):
                delete_question(q["id"])
                st.rerun()
