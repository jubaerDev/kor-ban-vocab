
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_all_words():
    client = get_client()
    result = client.table("vocab_words").select("korean_word, bangla_meaning").execute()
    return {row["korean_word"]: row["bangla_meaning"] for row in result.data}


def get_words_by_chapter(chapter_number):
    client = get_client()
    result = (
        client.table("vocab_words")
        .select("korean_word, bangla_meaning, date_added")
        .eq("chapter_number", chapter_number)
        .execute()
    )
    return result.data


def get_all_chapter_numbers():
    client = get_client()
    result = client.table("chapters_log").select("chapter_number").order("chapter_number").execute()
    return [row["chapter_number"] for row in result.data]


def get_chapters_log():
    client = get_client()
    result = client.table("chapters_log").select("*").order("chapter_number").execute()
    return result.data


def insert_new_words(rows, chapter_number):
    if not rows:
        return
    client = get_client()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    payload = [
        {
            "korean_word": r["korean_word"],
            "bangla_meaning": r["bangla_meaning"],
            "chapter_number": chapter_number,
            "date_added": now,
        }
        for r in rows
    ]
    client.table("vocab_words").insert(payload).execute()


def upsert_chapter_log(chapter_number, total_words_in_file, unique_new_words):
    client = get_client()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    client.table("chapters_log").upsert(
        {
            "chapter_number": chapter_number,
            "total_words_in_file": total_words_in_file,
            "unique_new_words": unique_new_words,
            "upload_date": now,
        },
        on_conflict="chapter_number",
    ).execute()
