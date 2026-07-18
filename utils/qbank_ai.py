"""
Question Bank এর জন্য: একটা MCQ question + ৪টা option দিলে AI দিয়ে সঠিক
answer আর বাংলা ব্যাখ্যা বের করা। translator.py এর মতোই Anthropic → Gemini
ক্রমে চেষ্টা করে, দুটোই ব্যর্থ হলে None ফেরত দেয় (তখন manual answer দিতে হবে)।
"""

import json
import re
import streamlit as st

QBANK_SYSTEM_PROMPT = """তুমি একজন TOPIK Korean ভাষা পরীক্ষার বিশেষজ্ঞ। তোমাকে একটা multiple-choice
প্রশ্ন এবং ৪টা option দেওয়া হবে (প্রতিটাতে ভিন্ন শব্দ/অংশ থাকতে পারে, প্রশ্নে বলা নিয়ম
অনুযায়ী কোনটা সঠিক তা বের করতে হবে)। তোমার কাজ:
1. কোন option (1, 2, 3, বা 4) সঠিক সেটা নির্ণয় করা
2. কেন সেটা সঠিক আর বাকিগুলো ভুল, তার একটা সংক্ষিপ্ত বাংলা ব্যাখ্যা লেখা

শুধু নিচের JSON ফরম্যাটে উত্তর দাও, অন্য কোনো টেক্সট/ব্যাখ্যা JSON এর বাইরে দেবে না:
{"answer": <1, 2, 3, বা 4 - সংখ্যা>, "explanation": "<বাংলা ব্যাখ্যা, ২-৪ বাক্য>"}
"""

CANDIDATE_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]


def _parse_json_response(text):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    data = json.loads(text)
    return int(data["answer"]), str(data["explanation"])


def generate_answer(question_text, options):
    """options: list of 4 strings. Returns (answer_number, explanation, engine) অথবা raises Exception।"""
    user_msg = f"""Question: {question_text}

1. {options[0]}
2. {options[1]}
3. {options[2]}
4. {options[3]}"""

    errors = []

    # ১. Anthropic চেষ্টা
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=500,
                system=QBANK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(b.text for b in response.content if b.type == "text")
            answer, explanation = _parse_json_response(text)
            return answer, explanation, "anthropic"
        except Exception as e:
            errors.append(f"Anthropic: {e}")

    # ২. Gemini চেষ্টা
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai as google_genai

            client = google_genai.Client(api_key=gemini_key)
            full_prompt = f"{QBANK_SYSTEM_PROMPT}\n\n{user_msg}"
            last_err = None
            for model_name in CANDIDATE_MODELS:
                try:
                    response = client.models.generate_content(model=model_name, contents=full_prompt)
                    answer, explanation = _parse_json_response(response.text)
                    return answer, explanation, "gemini"
                except Exception as e:
                    last_err = e
            raise last_err
        except Exception as e:
            errors.append(f"Gemini: {e}")

    raise RuntimeError(" | ".join(errors) if errors else "কোনো AI key (Anthropic/Gemini) secrets এ পাওয়া যায়নি।")
