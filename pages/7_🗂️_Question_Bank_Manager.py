import streamlit as st
from utils.db import (
    save_question,
    get_question_categories,
    get_questions_by_category,
    delete_question,
    update_question_answer,
    get_unresolved_feedback,
    resolve_feedback,
)
from utils.qbank_ai import generate_answer, parse_pasted_question

st.set_page_config(page_title="Question Bank Manager", page_icon="🗂️", layout="wide")
st.title("🗂️ Question Bank Manager")

# ---------- Feedback inbox ----------
try:
    feedback_list = get_unresolved_feedback()
except Exception:
    feedback_list = []

if feedback_list:
    st.error(f"🔔 {len(feedback_list)} টা নতুন feedback আছে — নিচে দেখো")
    with st.expander(f"🔔 Reported Issues ({len(feedback_list)})", expanded=True):
        for fb in feedback_list:
            qinfo = fb.get("question_info")
            st.markdown("---")
            if qinfo:
                st.write(f"**[{qinfo['category']}]** {qinfo['question_text']}")
                opts = [qinfo["option1"], qinfo["option2"], qinfo["option3"], qinfo["option4"]]
                for i, o in enumerate(opts, start=1):
                    marker = "👉" if i == qinfo["correct_answer"] else "  "
                    st.write(f"{marker} {i}. {o}")
                st.write(f"**বর্তমান সঠিক answer:** {qinfo['correct_answer']}")
            else:
                st.write("(এই question টা মুছে ফেলা হয়েছে)")
            st.write(f"**User এর note:** {fb.get('note') or '(কিছু লেখেনি)'}")
            if fb.get("suggested_answer"):
                st.write(f"**User এর মতে সঠিক answer:** {fb['suggested_answer']}")

            c1, c2 = st.columns(2)
            if c1.button("✅ শুধু Resolve করো (কিছু বদলাবে না)", key=f"resolve_{fb['id']}"):
                resolve_feedback(fb["id"])
                st.rerun()
            if qinfo and fb.get("suggested_answer") and c2.button(
                f"✏️ Answer {fb['suggested_answer']} তে বদলে Resolve করো", key=f"fix_{fb['id']}"
            ):
                update_question_answer(fb["question_id"], fb["suggested_answer"])
                resolve_feedback(fb["id"])
                st.rerun()
    st.divider()

st.caption("পুরো question (option সহ) paste করো — app নিজেই option আলাদা করে নেবে, তারপর AI answer বের করে দেবে।")

try:
    existing_categories = get_question_categories()
except Exception:
    existing_categories = []

category_choice = st.selectbox(
    "Category বেছে নাও বা নতুন লেখো",
    options=["(নতুন Category লিখবো)"] + existing_categories,
)
if category_choice == "(নতুন Category লিখবো)":
    category = st.text_input("নতুন Category এর নাম", placeholder="যেমন: TOPIK Grammar - 았/었")
else:
    category = category_choice

pasted = st.text_area(
    "পুরো Question (option সহ) Paste করো",
    height=180,
    placeholder="13.다음 중 밑줄 친 부분이 맞는 문장을 고르십시오.\n1.어머니는 옷을 읽었어요.\n2.어제 청소기를 널었어요.\n3.친구는 창문을 쓸었어요.\n4.오전에 세탁기를 돌렸어요.",
)

if st.button("✂️ Question ও Option আলাদা করো", disabled=not pasted.strip()):
    stem, opts = parse_pasted_question(pasted)
    st.session_state["parsed_stem"] = stem
    st.session_state["parsed_opts"] = opts

if "parsed_stem" in st.session_state:
    st.subheader("Preview (দরকার হলে ঠিক করে নাও)")
    question_text = st.text_area("Question stem", value=st.session_state["parsed_stem"], height=70)

    opts = st.session_state["parsed_opts"]
    missing = any(o is None for o in opts)
    if missing:
        st.warning("⚠️ কোনো একটা option ঠিকভাবে আলাদা করা যায়নি — নিচে manually পূরণ করো।")

    o1 = st.text_input("Option 1", value=opts[0] or "")
    o2 = st.text_input("Option 2", value=opts[1] or "")
    o3 = st.text_input("Option 3", value=opts[2] or "")
    o4 = st.text_input("Option 4", value=opts[3] or "")
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
            st.success(f"✅ AI ({st.session_state['ai_engine']}) সাজেশন পাওয়া গেছে — চেক করে দরকার হলে বদলাও")

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
            "ব্যাখ্যা (প্রতিটা option অনুযায়ী)", value=st.session_state.get("ai_explanation", ""), height=160
        )

        if st.button("💾 Question Save করো"):
            save_question(category, question_text, options, final_answer, final_explanation)
            st.success("Question save হয়ে গেছে ✅")
            for k in ["parsed_stem", "parsed_opts", "ai_answer", "ai_explanation", "ai_engine", "ai_error"]:
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
            for i in range(1, 5):
                marker = "👉" if i == q["correct_answer"] else "  "
                st.write(f"{marker} {i}. {q[f'option{i}']}")
            st.write(f"**ব্যাখ্যা:**\n\n{q.get('explanation') or '(নেই)'}")
            if st.button("🗑️ মুছে ফেলো", key=f"del_q_{q['id']}"):
                delete_question(q["id"])
                st.rerun()
