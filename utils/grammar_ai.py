"""
Grammar Bank এর জন্য দুইটা AI কাজ:
1. Messy/OCR করা grammar table টেক্সট থেকে structured (chapter, term,
   explanation, example) list বের করা।
2. একটা grammar point থেকে ২০টা practice MCQ question বানানো (Question
   Bank এর মতোই format — answer + per-option ব্যাখ্যা)।
"""

import json
import re
import streamlit as st

CANDIDATE_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]

PARSE_PROMPT = """তোমাকে একটা messy/OCR করা Korean grammar textbook table এর টেক্সট দেওয়া হবে।
এই টেবিলে সাধারণত এই column গুলো থাকে: অধ্যায় (chapter number, যেমন "1 과"), 문법 (grammar
pattern/term), 설명 (বাংলা ব্যাখ্যা), 활용 (Korean example sentence)।

তোমার কাজ: এই এলোমেলো টেক্সট থেকে প্রতিটা grammar entry আলাদা করে নিচের JSON array
ফরম্যাটে দাও:
[{"chapter": <int>, "term": "<Korean grammar pattern>", "explanation": "<বাংলা ব্যাখ্যা>", "example": "<Korean example sentence(s)>"}]

নিয়মঃ
- OCR এ Bangla বানান ভুল থাকতে পারে (যেমন 'রীরত' আসলে 'রীতি') - বুঝে ঠিক করে দেবে, অর্থ ঠিক রেখে
- একই chapter এ একাধিক grammar point থাকলে প্রতিটা আলাদা array entry হবে
- Korean text (grammar term ও example) যতটা সম্ভব হুবহু রাখবে, বদলাবে না
- শুধু JSON array দেবে, অন্য কোনো টেক্সট/ব্যাখ্যা দেবে না
"""

QUESTION_GEN_PROMPT = """তুমি একজন TOPIK/EPS-TOPIK Korean ভাষা পরীক্ষার প্রশ্ন প্রণয়নকারী।
তোমাকে একটা নির্দিষ্ট Korean grammar point (pattern, বাংলা ব্যাখ্যা, উদাহরণ) দেওয়া হবে।
এই grammar point practice করার জন্য ২০টা ভিন্ন multiple-choice question বানাও (fill-in-the-blank
বা "কোনটা সঠিক বাক্য" ধরনের প্রশ্ন), প্রতিটাতে ৪টা option, একটা সঠিক answer, আর প্রতিটা option
কেন সঠিক/ভুল তার সংক্ষিপ্ত বাংলা ব্যাখ্যা।

শুধু নিচের JSON ফরম্যাটে দাও, অন্য কোনো টেক্সট দিও না:
[
  {
    "question": "<প্রশ্ন, Korean বাক্যে blank/underline অংশ থাকতে পারে>",
    "options": ["option1", "option2", "option3", "option4"],
    "answer": <1-4>,
    "explanations": ["option1 কেন সঠিক/ভুল", "option2 কেন সঠিক/ভুল", "option3 কেন সঠিক/ভুল", "option4 কেন সঠিক/ভুল"]
  },
  ... (মোট ২০টা)
]
"""


def _call_ai(prompt, user_content, max_tokens=4000):
    """Anthropic → Gemini ক্রমে চেষ্টা করে raw text response ফেরত দেয়।"""
    errors = []

    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=max_tokens,
                system=prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            return "".join(b.text for b in response.content if b.type == "text")
        except Exception as e:
            errors.append(f"Anthropic: {e}")

    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai as google_genai

            client = google_genai.Client(api_key=gemini_key)
            full_prompt = f"{prompt}\n\n{user_content}"
            last_err = None
            for model_name in CANDIDATE_MODELS:
                try:
                    response = client.models.generate_content(model=model_name, contents=full_prompt)
                    return response.text
                except Exception as e:
                    last_err = e
            raise last_err
        except Exception as e:
            errors.append(f"Gemini: {e}")

    raise RuntimeError(" | ".join(errors) if errors else "কোনো AI key পাওয়া যায়নি।")


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip())
    # array বা object যেটা থাকুক
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def parse_grammar_text(raw_text):
    """Messy text থেকে [{"chapter":, "term":, "explanation":, "example":}] বের করে।"""
    response_text = _call_ai(PARSE_PROMPT, raw_text, max_tokens=8000)
    return _extract_json(response_text)


def generate_grammar_questions(grammar_term, explanation, example):
    """একটা grammar point থেকে ২০টা MCQ question বানায়।
    Returns list of dicts: {question, options, answer, explanations}"""
    user_content = f"""Grammar term: {grammar_term}
ব্যাখ্যা: {explanation}
উদাহরণ: {example}"""
    response_text = _call_ai(QUESTION_GEN_PROMPT, user_content, max_tokens=8000)
    return _extract_json(response_text)


def format_option_explanations(answer, options, explanations):
    lines = []
    for i in range(4):
        tag = "✅ সঠিক" if (i + 1) == answer else "❌ ভুল"
        lines.append(f"{i+1}. {options[i]} — {tag}: {explanations[i]}")
    return "\n".join(lines)
