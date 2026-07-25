import pandas as pd
import streamlit as st
from utils.db import get_weak_chapters, get_weak_categories, get_trouble_words

st.set_page_config(page_title="Weak Areas", page_icon="🎯", layout="wide")
st.title("🎯 দুর্বল জায়গা কোথায়?")
st.caption(
    "Flashcard practice করার সময়কার data থেকে বের করা — কোন chapter/category তে সবচেয়ে বেশি ভুল হচ্ছে, "
    "আর কোন word গুলো বার বার ভুলে যাচ্ছ।"
)

try:
    weak_chapters = get_weak_chapters()
    weak_categories = get_weak_categories()
    trouble_words = get_trouble_words(limit=30)
except Exception as e:
    st.error("Data আনতে সমস্যা হয়েছে।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not weak_chapters and not weak_categories:
    st.info(
        "এখনো যথেষ্ট practice data নেই। Flashcard দিয়ে কিছু practice করার পর "
        "এখানে দুর্বল জায়গা দেখা যাবে।"
    )
    st.stop()

tab1, tab2, tab3 = st.tabs(["📖 Chapter অনুযায়ী", "🗂️ Category অনুযায়ী", "😵 আটকে থাকা Word"])

with tab1:
    st.subheader("সবচেয়ে দুর্বল Chapter (উপরে যেগুলো, সেখানে বেশি ভুল হচ্ছে)")
    df = pd.DataFrame(weak_chapters)
    reviewed_df = df[df["reviews"] > 0].copy()
    if reviewed_df.empty:
        st.info("এখনো কোনো chapter এ যথেষ্ট review হয়নি।")
    else:
        reviewed_df["accuracy"] = reviewed_df["accuracy"].round(1)
        st.bar_chart(reviewed_df.set_index("chapter")["accuracy"])
        st.dataframe(
            reviewed_df.rename(
                columns={
                    "chapter": "Chapter",
                    "accuracy": "Accuracy %",
                    "words_tracked": "Word Tracked",
                    "stuck_words": "আটকে আছে (Box 1)",
                    "reviews": "মোট Review",
                }
            ),
            use_container_width=True,
        )
        weakest = reviewed_df.iloc[0]
        st.warning(
            f"⚠️ সবচেয়ে দুর্বল: **Chapter {int(weakest['chapter'])}** "
            f"(accuracy মাত্র {weakest['accuracy']}%) — এটা বেশি practice করা দরকার।"
        )

with tab2:
    st.subheader("সবচেয়ে দুর্বল Category")
    df2 = pd.DataFrame(weak_categories)
    reviewed_df2 = df2[df2["reviews"] > 0].copy()
    if reviewed_df2.empty:
        st.info(
            "এখনো কোনো category তে যথেষ্ট review হয়নি (word categorize করা না থাকলে বা "
            "categorize করা word গুলো এখনো practice না হলে এখানে কিছু দেখাবে না)।"
        )
    else:
        reviewed_df2["accuracy"] = reviewed_df2["accuracy"].round(1)
        st.bar_chart(reviewed_df2.set_index("category")["accuracy"])
        st.dataframe(
            reviewed_df2.rename(
                columns={"category": "Category", "accuracy": "Accuracy %", "words_tracked": "Word Tracked", "reviews": "মোট Review"}
            ),
            use_container_width=True,
        )
        weakest_cat = reviewed_df2.iloc[0]
        st.warning(
            f"⚠️ সবচেয়ে দুর্বল category: **{weakest_cat['category']}** "
            f"(accuracy মাত্র {weakest_cat['accuracy']}%)"
        )

with tab3:
    st.subheader("যেসব Word বার বার ভুলে যাচ্ছ")
    st.caption("এই word গুলো ২ বারের বেশি practice করার পরও এখনো 'নতুন' অবস্থায় (Box 1) আটকে আছে।")
    if not trouble_words:
        st.success("🎉 কোনো word এ আটকে নেই — চমৎকার!")
    else:
        tw_df = pd.DataFrame(trouble_words)
        st.dataframe(
            tw_df[["korean_word", "bangla_meaning", "chapter_number", "times_reviewed", "times_correct"]].rename(
                columns={
                    "korean_word": "Korean",
                    "bangla_meaning": "Bangla",
                    "chapter_number": "Chapter",
                    "times_reviewed": "কতবার দেখেছ",
                    "times_correct": "কতবার ঠিক বলেছ",
                }
            ),
            use_container_width=True,
        )

st.divider()
st.info(
    "💡 **পরামর্শ:** উপরের দুর্বল chapter/category গুলো targeted ভাবে Flashcard এ গিয়ে practice করো — "
    "সব chapter সমান সময় না দিয়ে, যেখানে ভুল বেশি সেখানে বেশি সময় দিলে দ্রুত উন্নতি হবে।"
)
