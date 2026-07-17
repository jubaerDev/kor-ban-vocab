import pandas as pd
import streamlit as st
from utils.db import get_all_chapter_numbers, get_words_by_chapter, get_chapter_full_analysis

st.set_page_config(page_title="Browse History", page_icon="📂")
st.title("📂 আগের Chapter গুলো দেখো")

try:
    chapters = get_all_chapter_numbers()
except Exception as e:
    st.error("Database থেকে chapter list আনা যায়নি।")
    st.caption(f"Error detail: {e}")
    st.stop()

if not chapters:
    st.info("এখনো কোনো chapter save হয়নি।")
    st.stop()

selected = st.selectbox("Chapter বেছে নাও", sorted(chapters))

tab1, tab2 = st.tabs(["✅ শুধু Unique Word", "🔍 সব Word (Full Comparison)"])

with tab1:
    rows = get_words_by_chapter(selected)
    df = pd.DataFrame(rows)

    if df.empty:
        st.warning("এই chapter এ কোনো unique word নেই।")
    else:
        st.write(f"**Chapter {selected}** — {len(df)} টা unique word")
        st.caption("যেগুলো CSV তে চাও, সেগুলোর পাশের বক্সে ✅ টিক দাও (নিচে সব/কোনোটা না বাছারও বাটন আছে)।")

        display_df = df[["korean_word", "bangla_meaning"]].copy()
        display_df.insert(0, "Select", False)

        col_a, col_b = st.columns(2)
        select_all = col_a.button("✅ সব সিলেক্ট করো")
        clear_all = col_b.button("❌ সব বাদ দাও")

        state_key = f"select_state_{selected}"
        if select_all:
            st.session_state[state_key] = True
        elif clear_all:
            st.session_state[state_key] = False

        if state_key in st.session_state:
            display_df["Select"] = st.session_state[state_key]

        edited_df = st.data_editor(
            display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn("বাছো"),
                "korean_word": st.column_config.TextColumn("Korean word", disabled=True),
                "bangla_meaning": st.column_config.TextColumn("Bangla word", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{selected}",
        )

        selected_rows = edited_df[edited_df["Select"]]

        st.write(f"**{len(selected_rows)} টা word সিলেক্ট করা হয়েছে**")

        # --- সব unique word এর CSV (আগের মতোই) ---
        all_csv_bytes = df[["korean_word", "bangla_meaning"]].to_csv(
            index=False, header=["Korean word", "Bangla word"]
        ).encode("utf-8-sig")

        col1, col2 = st.columns(2)
        col1.download_button(
            "⬇️ সব Unique Word এর CSV",
            data=all_csv_bytes,
            file_name=f"chapter_{selected}_unique.csv",
            mime="text/csv",
        )

        if not selected_rows.empty:
            selected_csv_bytes = selected_rows[["korean_word", "bangla_meaning"]].to_csv(
                index=False, header=["Korean word", "Bangla word"]
            ).encode("utf-8-sig")
            col2.download_button(
                f"⬇️ শুধু সিলেক্ট করা {len(selected_rows)} টা এর CSV",
                data=selected_csv_bytes,
                file_name=f"chapter_{selected}_selected.csv",
                mime="text/csv",
            )
        else:
            col2.button("⬇️ শুধু সিলেক্ট করা এর CSV", disabled=True)

with tab2:
    st.caption(
        "এখানে ওই chapter এর raw file এ থাকা সব word দেখা যাবে (duplicate সহ), "
        "প্রতিটার পাশে বোঝা যাবে সেটা কেন unique list এ আছে বা নেই।"
    )
    analysis = get_chapter_full_analysis(selected)
    if not analysis:
        st.warning("এই chapter এর raw data পাওয়া যায়নি।")
    else:
        full_df = pd.DataFrame(analysis)
        st.write(f"**Chapter {selected}** — raw file এ মোট {len(full_df)} টা row")

        counts = full_df["Status"].apply(
            lambda s: "unique" if s.startswith("✅") else ("repeat" if s.startswith("🔁") else "seen_before")
        ).value_counts()
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Unique", int(counts.get("unique", 0)))
        c2.metric("🔁 File এর মধ্যে Repeat", int(counts.get("repeat", 0)))
        c3.metric("↩️ আগেই অন্য Chapter এ", int(counts.get("seen_before", 0)))

        st.dataframe(full_df, use_container_width=True)
