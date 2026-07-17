import io
import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from utils.column_detector import detect_columns
from utils.extractor import get_new_unique_words
from utils.db import get_all_words, insert_new_words, upsert_chapter_log, get_all_chapter_numbers

st.set_page_config(page_title="Upload Chapter", page_icon="📤")
st.title("📤 নতুন Chapter Upload করো")

existing_chapters = []
try:
    existing_chapters = get_all_chapter_numbers()
except Exception:
    pass

suggested_next = (max(existing_chapters) + 1) if existing_chapters else 1
chapter_number = st.number_input("Chapter নাম্বার", min_value=1, step=1, value=suggested_next)

uploaded_file = st.file_uploader("Excel বা CSV file আপলোড করো", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)

    st.write("**Preview (প্রথম ৫ row):**")
    st.dataframe(raw_df.head())

    korean_guess, bangla_guess, notes = detect_columns(raw_df)
    if notes:
        for n in notes:
            st.info(n)

    cols = list(raw_df.columns)
    korean_col = st.selectbox(
        "Korean word এর column বেছে নাও",
        cols,
        index=cols.index(korean_guess) if korean_guess in cols else 0,
    )
    bangla_col = st.selectbox(
        "Bangla meaning এর column বেছে নাও",
        cols,
        index=cols.index(bangla_guess) if bangla_guess in cols else (1 if len(cols) > 1 else 0),
    )

    if st.button("🔍 Unique Word বের করো", type="primary"):
        with st.spinner("Database এর সাথে compare করা হচ্ছে..."):
            existing_words = get_all_words()
            new_words_df, total_in_file = get_new_unique_words(raw_df, korean_col, bangla_col, existing_words)

        st.session_state["new_words_df"] = new_words_df
        st.session_state["total_in_file"] = total_in_file
        st.session_state["chapter_number"] = chapter_number

    if "new_words_df" in st.session_state:
        new_words_df = st.session_state["new_words_df"]
        total_in_file = st.session_state["total_in_file"]

        st.success(
            f"এই Chapter এ মোট {total_in_file} টা word ছিল। "
            f"এর মধ্যে {len(new_words_df)} টা সম্পূর্ণ নতুন/unique word পাওয়া গেছে।"
        )
        st.dataframe(new_words_df)

        # --- Build CSV (2 columns only) ---
        csv_bytes = new_words_df.to_csv(index=False, header=["Korean word", "Bangla word"]).encode("utf-8-sig")

        # --- Build styled Excel ---
        wb = Workbook()
        ws = wb.active
        ws.title = f"Chapter_{chapter_number}"
        ws.append(["Korean word", "Bangla word"])
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        for _, row in new_words_df.iterrows():
            ws.append([row["Korean"], row["Bangla"]])
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 30

        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        col1, col2 = st.columns(2)
        col1.download_button(
            "⬇️ Excel Download",
            data=excel_buffer,
            file_name=f"chapter_{chapter_number}_unique.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        col2.download_button(
            "⬇️ CSV Download (2 column)",
            data=csv_bytes,
            file_name=f"chapter_{chapter_number}_unique.csv",
            mime="text/csv",
        )

        st.divider()
        if st.button("💾 Database তে Save করো (পরের চ্যাপ্টার এই word বাদ দিয়ে compare হবে)"):
            rows = [
                {"korean_word": r["Korean"], "bangla_meaning": r["Bangla"]}
                for _, r in new_words_df.iterrows()
            ]
            insert_new_words(rows, chapter_number)
            upsert_chapter_log(chapter_number, total_in_file, len(new_words_df))
            st.success(f"Chapter {chapter_number} এর {len(new_words_df)} টা word database এ save হয়ে গেছে ✅")
            del st.session_state["new_words_df"]
