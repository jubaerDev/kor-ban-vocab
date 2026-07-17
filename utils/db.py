"""
Supabase connection + all read/write helpers.

Design note: `raw_chapter_words` is the source of truth. Every upload
saves its raw (un-deduplicated) rows there. `vocab_words` and
`chapters_log` are *derived* tables, fully rebuilt from raw data every
time something changes. This way, no matter what order chapters are
uploaded in (e.g. chapter 10, then 20, then 11-19 later), the final
"which chapter did this word first appear in" is always correct,
because rebuild always processes chapters in numeric order.
"""

import math
import unicodedata
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def _fetch_all(table, select_cols, eq_filter=None, order_cols=None, page_size=1000):
    """
    Supabase/PostgREST প্রতি request এ default সর্বোচ্চ ~1000 row ফেরত দেয়।
    Chapter/word সংখ্যা বাড়ার সাথে সাথে এই limit ছাড়িয়ে গেলে data silently
    কেটে যেতে পারে (কোনো error ছাড়াই) — এই function .range() দিয়ে ধাপে ধাপে
    সব row নিশ্চিতভাবে নিয়ে আসে।
    """
    client = get_client()
    all_rows = []
    start = 0
    while True:
        q = client.table(table).select(select_cols)
        if eq_filter:
            col, val = eq_filter
            q = q.eq(col, val)
        if order_cols:
            for col in order_cols:
                q = q.order(col)
        q = q.range(start, start + page_size - 1)
        batch = q.execute().data
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return all_rows


def _clean_value(value):
    """NaN/empty কোনো value কে None/খালি string বানিয়ে দেয়, এবং Unicode কে
    normalize (NFC) করে যাতে একই দেখতে word ভিন্ন byte representation এর
    কারণে আলাদা ধরা না পড়ে (composed vs decomposed Hangul/Bangla সমস্যা)।"""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, str):
        if value.strip().lower() == "nan":
            return ""
        return unicodedata.normalize("NFC", value.strip())
    return value


# ---------- READ helpers (used by pages) ----------

def get_all_words():
    rows = _fetch_all("vocab_words", "korean_word, bangla_meaning")
    return {row["korean_word"]: row["bangla_meaning"] for row in rows}


def get_words_by_chapter(chapter_number):
    return _fetch_all(
        "vocab_words",
        "korean_word, bangla_meaning, date_added",
        eq_filter=("chapter_number", chapter_number),
    )


def get_all_chapter_numbers():
    client = get_client()
    result = client.table("chapters_log").select("chapter_number").order("chapter_number").execute()
    return [row["chapter_number"] for row in result.data]


def get_chapters_log():
    client = get_client()
    result = client.table("chapters_log").select("*").order("chapter_number").execute()
    return result.data


def chapter_exists(chapter_number):
    """চেক করে এই chapter number আগে কখনো upload হয়েছে কিনা (duplicate warning এর জন্য)।"""
    client = get_client()
    result = (
        client.table("raw_chapter_words")
        .select("id")
        .eq("chapter_number", chapter_number)
        .limit(1)
        .execute()
    )
    return len(result.data) > 0


# ---------- WRITE helpers ----------

def save_raw_chapter(chapter_number, korean_bangla_pairs):
    """
    korean_bangla_pairs: list of (korean_word, bangla_meaning) tuples,
    straight from the uploaded file (not deduplicated against DB yet).
    Overwrites any existing raw rows for this chapter (for re-upload).
    """
    client = get_client()
    # আগে এই chapter এর পুরনো raw data থাকলে মুছে ফেলা (re-upload/overwrite এর জন্য)
    client.table("raw_chapter_words").delete().eq("chapter_number", chapter_number).execute()

    now = datetime.now(timezone.utc).isoformat()
    payload = [
        {
            "chapter_number": int(chapter_number),
            "korean_word": _clean_value(k),
            "bangla_meaning": _clean_value(b),
            "uploaded_at": now,
        }
        for k, b in korean_bangla_pairs
        if _clean_value(k)
    ]
    if payload:
        client.table("raw_chapter_words").insert(payload).execute()


def delete_chapter(chapter_number):
    """একটা chapter সম্পূর্ণ মুছে ফেলে (raw সহ) এবং database rebuild করে।"""
    client = get_client()
    client.table("raw_chapter_words").delete().eq("chapter_number", chapter_number).execute()
    rebuild_database()


def get_chapter_full_analysis(chapter_number):
    """
    ওই chapter এর raw file এ থাকা প্রতিটা word ফেরত দেয়, সাথে একটা status:
    - "unique"   → এই chapter এর জন্যই নতুন/unique হিসেবে গণ্য হয়েছে
    - "repeat_in_file" → একই chapter এর raw file এর ভেতরেই এই word বার বার এসেছে
    - "seen_before" → word টা আগের অন্য কোনো chapter এ ইতিমধ্যে আছে (with chapter no.)
    """
    raw = _fetch_all(
        "raw_chapter_words",
        "korean_word, bangla_meaning, id",
        eq_filter=("chapter_number", chapter_number),
        order_cols=["id"],
    )

    vocab_rows = _fetch_all("vocab_words", "korean_word, chapter_number")
    vocab_map = {
        unicodedata.normalize("NFC", (r["korean_word"] or "").strip()): r["chapter_number"]
        for r in vocab_rows
    }

    local_seen = set()
    results = []
    for r in raw:
        k, b = unicodedata.normalize("NFC", (r["korean_word"] or "").strip()), r["bangla_meaning"]
        if k in local_seen:
            status = "🔁 একই chapter এ repeat"
        else:
            local_seen.add(k)
            assigned = vocab_map.get(k)
            if assigned == chapter_number:
                status = "✅ Unique (এই chapter এর)"
            elif assigned is not None:
                status = f"↩️ আগে থেকেই আছে (Chapter {assigned})"
            else:
                status = "⚠️ অজানা"
        results.append({"Korean": k, "Bangla": b, "Status": status})
    return results


def rebuild_database():
    """
    raw_chapter_words থেকে chapter-number ক্রম অনুযায়ী প্রতিটা chapter প্রসেস করে
    vocab_words ও chapters_log সম্পূর্ণ নতুন করে বানায়। এটাই নিশ্চিত করে যে
    upload এর ক্রম যাই হোক, chapter number এর প্রকৃত ক্রম অনুযায়ী "প্রথম কোথায়
    দেখা গেছে" হিসাব হবে।
    """
    client = get_client()

    raw = _fetch_all(
        "raw_chapter_words",
        "chapter_number, korean_word, bangla_meaning, id",
        order_cols=["chapter_number", "id"],
    )

    # chapter অনুযায়ী group করা (raw ইতিমধ্যে chapter_number, id অনুযায়ী sorted)
    by_chapter = {}
    for row in raw:
        by_chapter.setdefault(row["chapter_number"], []).append(row)

    seen_words = set()
    vocab_payload = []
    log_payload = []
    now = datetime.now(timezone.utc).isoformat()

    for chapter_number in sorted(by_chapter.keys()):
        rows = by_chapter[chapter_number]
        total_in_file = len(rows)

        local_seen = set()
        new_this_chapter = []
        for r in rows:
            k = unicodedata.normalize("NFC", (r["korean_word"] or "").strip())
            if not k or k in local_seen:
                continue
            local_seen.add(k)
            if k in seen_words:
                continue
            seen_words.add(k)
            new_this_chapter.append(r)

        for r in new_this_chapter:
            vocab_payload.append(
                {
                    "korean_word": unicodedata.normalize("NFC", (r["korean_word"] or "").strip()),
                    "bangla_meaning": r["bangla_meaning"],
                    "chapter_number": chapter_number,
                    "date_added": now,
                }
            )

        log_payload.append(
            {
                "chapter_number": chapter_number,
                "total_words_in_file": total_in_file,
                "unique_new_words": len(new_this_chapter),
                "upload_date": now,
            }
        )

    # পুরনো vocab_words / chapters_log খালি করা
    client.table("vocab_words").delete().gte("id", 0).execute()
    client.table("chapters_log").delete().gte("chapter_number", 0).execute()

    if vocab_payload:
        # বড় হলে batch করে insert করা (Supabase এর সাথে সমস্যা এড়াতে)
        batch_size = 500
        for i in range(0, len(vocab_payload), batch_size):
            client.table("vocab_words").insert(vocab_payload[i : i + batch_size]).execute()

    if log_payload:
        client.table("chapters_log").insert(log_payload).execute()
