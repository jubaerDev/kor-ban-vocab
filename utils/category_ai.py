"""
Vocabulary Category ফিচারের জন্য: একগুচ্ছ Korean word (+ Bangla meaning) দিলে
প্রতিটার জন্য fixed category তালিকা থেকে সবচেয়ে উপযুক্ত category বেছে দেয়,
সাথে Korean+Bangla synonym/antonym বানিয়ে দেয়।
"""

import json
import re
import streamlit as st

CANDIDATE_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]

FIXED_CATEGORIES = [
    "Adjectives",
    "Daily Life",
    "Exam Topics",
    "Food and Shopping",
    "Health and Hospital",
    "Housing",
    "Industry and Job Type",
    "Korean Culture",
    "Numbers, Time, and Date",
    "Safety",
    "Transportation",
    "Verbs",
    "Workplace",
    "Other",
]

CATEGORY_PROMPT = f"""তুমি একজন Korean ভাষা বিশেষজ্ঞ। তোমাকে কতগুলো Korean word (এবং তার Bangla অর্থ)
দেওয়া হবে, প্রতিটা "Korean - Bangla" ফরম্যাটে আলাদা লাইনে।

প্রতিটা word এর জন্য:
1. নিচের নির্দিষ্ট category তালিকা থেকে সবচেয়ে উপযুক্ত একটা category বেছে দাও
   (এই তালিকার বাইরে কিছু দেবে না, ঠিক এই বানানেই লিখবে):
   {", ".join(FIXED_CATEGORIES)}
2. সেই word এর ১-৩টা Korean synonym (কাছাকাছি অর্থের শব্দ) দাও, খুঁজে না পেলে খালি স্ট্রিং দাও
3. সেই word এর ১-৩টা Korean antonym (বিপরীত অর্থের শব্দ) দাও, খুঁজে না পেলে খালি স্ট্রিং দাও
4. synonym ও antonym গুলোর বাংলা অর্থও কমা দিয়ে আলাদা করে দাও

শুধু নিচের JSON array ফরম্যাটে দাও, অন্য কোনো টেক্সট দিও না:
[{{"korean_word": "...", "category": "...", "synonyms": "syn1, syn2", "antonyms": "ant1, ant2", "bangla_synonyms": "বাংলা১, বাংলা২", "bangla_antonyms": "বাংলা১, বাংলা২"}}]
"""


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def categorize_words_batch(words):
    """words: list of (korean_word, bangla_meaning) tuples.
    Returns: list of dict {korean_word, category, synonyms, antonyms, bangla_synonyms, bangla_antonyms}"""
    word_list_text = "\n".join(f"{k} - {b}" for k, b in words)
    errors = []

    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,
                system=CATEGORY_PROMPT,
                messages=[{"role": "user", "content": word_list_text}],
            )
            text = "".join(b.text for b in response.content if b.type == "text")
            return _extract_json(text)
        except Exception as e:
            errors.append(f"Anthropic: {e}")

    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai as google_genai

            client = google_genai.Client(api_key=gemini_key)
            full_prompt = f"{CATEGORY_PROMPT}\n\n{word_list_text}"
            last_err = None
            for model_name in CANDIDATE_MODELS:
                try:
                    response = client.models.generate_content(model=model_name, contents=full_prompt)
                    return _extract_json(response.text)
                except Exception as e:
                    last_err = e
            raise last_err
        except Exception as e:
            errors.append(f"Gemini: {e}")

    raise RuntimeError(" | ".join(errors) if errors else "কোনো AI key পাওয়া যায়নি।")
