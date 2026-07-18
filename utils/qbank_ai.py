"""
Question Bank এর জন্য:
1. পুরো paste করা question block (question + "1. ... 2. ... 3. ... 4. ...")
   থেকে স্বয়ংক্রিয়ভাবে question stem ও ৪টা option আলাদা করা।
2. AI দিয়ে সঠিক answer + প্রতিটা option এর জন্য আলাদা ব্যাখ্যা বের করা।
"""

import json
import re
import streamlit as st

QBANK_SYSTEM_PROMPT = """তুমি একজন TOPIK Korean ভাষা পরীক্ষার বিশেষজ্ঞ। তোমাকে একটা multiple-choice
প্রশ্ন এবং ৪টা option দেওয়া হবে। তোমার কাজ:
1. কোন option (1, 2, 3, বা 4) সঠিক সেটা নির্ণয় করা
2. প্রতিটা option এর জন্য আলাদা আলাদা ভাবে ব্যাখ্যা করা কেন সেটা সঠিক বা ভুল (প্রতিটা ১-২ বাক্যে)

শুধু নিচের JSON ফরম্যাটে উত্তর দাও, অন্য কোনো টেক্সট JSON এর বাইরে দেবে না:
{"answer": <1, 2, 3, বা 4>, "explanations": ["option1 কেন সঠিক/ভুল", "option2 কেন সঠিক/ভুল", "option3 কেন সঠিক/ভুল", "option4 কেন সঠিক/ভুল"]}
"""

CANDIDATE_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]


# ---------- Auto-parse pasted question+options block ----------

_OPTION_LINE_RE = re.compile(r"^\s*([1-4])\s*[.\)．]\s*(.+?)\s*$")


def parse_pasted_question(raw_text):
    """
    পুরো paste করা block থেকে question stem ও ৪টা option আলাদা করে।
    Options আলাদা লাইনে "1. ..." "2. ..." আকারে থাকবে ধরে নেওয়া হয়েছে
    (একই লাইনে ১টার বেশি option থাকলেও চেষ্টা করবে, তবে আলাদা লাইন সবচেয়ে নির্ভরযোগ্য)।
    Returns: (question_stem, [opt1, opt2, opt3, opt4]) — না মিললে None value থাকবে,
    সেগুলো UI তে manually পূরণ করতে হবে।
    """
    lines = [l for l in raw_text.splitlines() if l.strip()]
    options = {1: None, 2: None, 3: None, 4: None}
    stem_lines = []

    for line in lines:
        m = _OPTION_LINE_RE.match(line)
        if m:
            num = int(m.group(1))
            options[num] = m.group(2).strip()
        else:
            # option শুরু হওয়ার আগ পর্যন্ত সব লাইন question stem এর অংশ
            if all(v is None for v in options.values()):
                stem_lines.append(line.strip())

    question_stem = " ".join(stem_lines).strip()
    # প্রশ্ন নম্বর প্রিফিক্স (যেমন "13.") থাকলে সরিয়ে দেওয়া
    question_stem = re.sub(r"^\d+\.\s*", "", question_stem)

    return question_stem, [options[1], options[2], options[3], options[4]]


# ---------- AI answer + per-option explanation ----------

def _parse_json_response(text):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    data = json.loads(text)
    return int(data["answer"]), list(data["explanations"])


def _format_explanation(answer, options, explanations):
    lines = []
    for i in range(4):
        tag = "✅ সঠিক" if (i + 1) == answer else "❌ ভুল"
        lines.append(f"{i+1}. {options[i]} — {tag}: {explanations[i]}")
    return "\n".join(lines)


def generate_answer(question_text, options):
    """options: list of 4 strings. Returns (answer_number, formatted_explanation, engine)।"""
    user_msg = f"""Question: {question_text}

1. {options[0]}
2. {options[1]}
3. {options[2]}
4. {options[3]}"""

    errors = []

    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=800,
                system=QBANK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(b.text for b in response.content if b.type == "text")
            answer, explanations = _parse_json_response(text)
            return answer, _format_explanation(answer, options, explanations), "anthropic"
        except Exception as e:
            errors.append(f"Anthropic: {e}")

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
                    answer, explanations = _parse_json_response(response.text)
                    return answer, _format_explanation(answer, options, explanations), "gemini"
                except Exception as e:
                    last_err = e
            raise last_err
        except Exception as e:
            errors.append(f"Gemini: {e}")

    raise RuntimeError(" | ".join(errors) if errors else "কোনো AI key (Anthropic/Gemini) secrets এ পাওয়া যায়নি।")
