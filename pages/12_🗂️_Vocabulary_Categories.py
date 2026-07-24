import streamlit as st
from utils.db import (
    get_uncategorized_words,
    save_enrichment_batch,
    get_category_list,
    get_words_by_category,
    auto_categorize_all,
)
from utils.category_ai import categorize_words_batch, FIXED_CATEGORIES
from utils.auth import is_admin

st.set_page_config(page_title="Vocabulary Categories", page_icon="🗂️", layout="wide")
st.title("🗂️ Vocabulary Categories")

# ---------- Admin: AI দিয়ে categorize করা ----------
if is_admin():
    with st.expander("🤖 AI দিয়ে Word Categorize করো (Category + Synonym + Antonym)", expanded=True):
        try:
            preview_batch, total_words, done_count = get_uncategorized_words(batch_size=30)
        except Exception as e:
            preview_batch, total_words, done_count = [], 0, 0
            st.error(f"Data আনতে সমস্যা: {e}")

        if total_words > 0:
            progress_frac = done_count / total_words if total_words else 0
            st.progress(progress_frac, text=f"{done_count} / {total_words} word categorize হয়েছে")

        remaining = total_words - done_count
        if remaining <= 0:
            st.success("✅ সব word ইতিমধ্যে categorize হয়ে গেছে!")
        else:
            st.caption(f"বাকি আছে {remaining} টা word।")
            c1, c2 = st.columns(2)
            if c1.button("🤖 পরের ৩০টা করো"):
                with st.spinner("AI প্রতিটা word এর category, synonym, antonym ঠিক করছে..."):
                    try:
                        pairs = [(w["korean_word"], w["bangla_meaning"]) for w in preview_batch]
                        results = categorize_words_batch(pairs)
                        save_enrichment_batch(results)
                        st.success(f"✅ {len(results)} টা word categorize হয়ে গেছে")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Categorize করা যায়নি: {e}")

            if c2.button("🔄 সব বাকি Auto-Categorize করো", type="primary"):
                progress_placeholder = st.progress(0.0, text="শুরু হচ্ছে...")

                def _update(done, total):
                    frac = (done / total) if total else 1.0
                    progress_placeholder.progress(frac, text=f"{done} / {total} categorize হয়েছে")

                try:
                    done, total = auto_categorize_all(progress_callback=_update)
                    st.success(f"✅ সম্পন্ন! মোট {done}/{total} word categorize হয়ে গেছে")
                    st.rerun()
                except Exception as e:
                    st.error(f"Auto-categorize মাঝপথে থেমে গেছে: {e}")

st.divider()

# ---------- সবার জন্য: Category অনুযায়ী browse ----------
try:
    used_categories = get_category_list()
except Exception as e:
    st.error("Category list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not used_categories:
    st.info("এখনো কোনো word categorize করা হয়নি। Admin হলে উপরের অংশ থেকে শুরু করো।")
    st.stop()

selected_category = st.selectbox("Category বেছে নাও", used_categories)

words = get_words_by_category(selected_category)
st.caption(f"এই category তে {len(words)} টা word")

cols = st.columns(2)
for i, w in enumerate(words):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"### {w['korean_word']}")
            st.write(f"**অর্থ:** {w['bangla_meaning']}")
            if w.get("synonyms"):
                st.write(f"**Synonym:** {w['synonyms']} ({w.get('bangla_synonyms', '')})")
            if w.get("antonyms"):
                st.write(f"**Antonym:** {w['antonyms']} ({w.get('bangla_antonyms', '')})")
