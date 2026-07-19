import streamlit as st
from utils.db import (
    save_grammar_point,
    get_grammar_chapters,
    get_grammar_points,
    delete_grammar_point,
    save_question,
)
from utils.grammar_ai import parse_grammar_text, generate_grammar_questions, format_option_explanations
from utils.auth import is_admin, require_admin

st.set_page_config(page_title="Grammar Bank", page_icon="📖", layout="wide")
st.title("📖 Grammar Bank")

# ---------- Admin-only: Bulk import + manual add ----------
if is_admin():
    with st.expander("🤖 Bulk Import (AI দিয়ে messy/OCR টেক্সট থেকে Parse করো)"):
        st.caption(
            "বইয়ের raw/OCR করা grammar table টেক্সট (ভুলভাল বানান সহ) সরাসরি paste করো — "
            "AI নিজেই chapter, grammar term, ব্যাখ্যা, উদাহরণ আলাদা করে দেবে। "
            "একসাথে অনেক বড় টেক্সট দিলে ভালো হয় ১০-১৫ chapter করে ভাগ করে দেওয়া।"
        )
        raw_text = st.text_area("Raw grammar text পেস্ট করো", height=200, key="raw_grammar_input")
        if st.button("🤖 AI দিয়ে Parse করো", disabled=not raw_text.strip()):
            with st.spinner("AI পুরো টেক্সট পড়ে structured করছে..."):
                try:
                    parsed = parse_grammar_text(raw_text)
                    st.session_state["parsed_grammar"] = parsed
                except Exception as e:
                    st.error(f"Parse করা যায়নি: {e}")

        if "parsed_grammar" in st.session_state:
            parsed = st.session_state["parsed_grammar"]
            st.success(f"✅ {len(parsed)} টা grammar point পাওয়া গেছে — নিচে check করে Save করো")
            st.dataframe(parsed, use_container_width=True)
            if st.button("💾 সব কয়টা Save করো"):
                for item in parsed:
                    save_grammar_point(
                        item.get("chapter"), item.get("term"), item.get("explanation"), item.get("example")
                    )
                st.success(f"{len(parsed)} টা grammar point save হয়ে গেছে ✅")
                del st.session_state["parsed_grammar"]
                st.rerun()

    with st.expander("➕ একটা Grammar Point Manually যোগ করো"):
        c1, c2 = st.columns([1, 3])
        m_chapter = c1.number_input("Chapter", min_value=1, step=1, key="manual_chapter")
        m_term = c2.text_input("Grammar Term (Korean)", key="manual_term")
        m_explanation = st.text_area("ব্যাখ্যা (বাংলা)", key="manual_explanation")
        m_example = st.text_area("উদাহরণ (Korean)", key="manual_example")
        if st.button("💾 Save করো", key="manual_save"):
            if m_term.strip():
                save_grammar_point(m_chapter, m_term, m_explanation, m_example)
                st.success("Save হয়ে গেছে ✅")
                st.rerun()
            else:
                st.warning("Grammar term খালি রাখা যাবে না।")

st.divider()

# ---------- সবার জন্য: Browse ----------
try:
    chapters = get_grammar_chapters()
except Exception as e:
    st.error("Database থেকে chapter list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not chapters:
    st.info("এখনো কোনো grammar point যোগ হয়নি।")
    st.stop()

selected_chapter = st.selectbox("Chapter বেছে নাও", chapters, format_func=lambda c: f"Chapter {c}")
points = get_grammar_points(selected_chapter)

st.caption(f"Chapter {selected_chapter} — {len(points)} টা grammar point")

for gp in points:
    with st.container(border=True):
        st.markdown(f"### {gp['grammar_term']}")
        st.write(f"**ব্যাখ্যা:** {gp.get('explanation') or '(নেই)'}")
        st.write(f"**উদাহরণ:** {gp.get('example') or '(নেই)'}")

        if is_admin():
            c1, c2 = st.columns([1, 1])
            gen_key = f"gen_{gp['id']}"
            if c1.button("🤖 AI দিয়ে ২০টা Question Generate করো", key=f"btn_{gp['id']}"):
                with st.spinner("AI প্রশ্ন বানাচ্ছে (কিছুটা সময় লাগতে পারে)..."):
                    try:
                        questions = generate_grammar_questions(
                            gp["grammar_term"], gp.get("explanation", ""), gp.get("example", "")
                        )
                        st.session_state[gen_key] = questions
                    except Exception as e:
                        st.error(f"Question generate করা যায়নি: {e}")

            if c2.button("🗑️ এই Grammar Point মুছে ফেলো", key=f"del_{gp['id']}"):
                delete_grammar_point(gp["id"])
                st.rerun()

            if gen_key in st.session_state:
                questions = st.session_state[gen_key]
                st.success(f"✅ {len(questions)} টা question তৈরি হয়েছে")
                with st.expander("প্রিভিউ দেখো"):
                    for i, q in enumerate(questions, start=1):
                        st.write(f"**{i}. {q['question']}**")
                        for j, opt in enumerate(q["options"], start=1):
                            marker = "👉" if j == q["answer"] else "  "
                            st.write(f"{marker} {j}. {opt}")

                category_name = f"Grammar {gp['chapter_number']}과 - {gp['grammar_term'][:40]}"
                if st.button(f"💾 এই {len(questions)} টা Question Bank এ Save করো", key=f"save_q_{gp['id']}"):
                    for q in questions:
                        explanation_text = format_option_explanations(q["answer"], q["options"], q["explanations"])
                        save_question(category_name, q["question"], q["options"], q["answer"], explanation_text)
                    st.success(f"সব প্রশ্ন Question Bank এ (category: {category_name}) save হয়ে গেছে ✅")
                    del st.session_state[gen_key]
                    st.rerun()
