"""
Korean paragraph কে word-by-word "token(meaning)" আকারে annotate করে।

এই কাজটা ঠিকভাবে করতে হলে (verb conjugation বোঝা, grammar particle আলাদা
করা, প্রসঙ্গ অনুযায়ী অর্থ ঠিক করা) আসলে ভাষা বোঝার দরকার — শুধু suffix
কাটাকাটি করা rule দিয়ে ভালো accuracy পাওয়া যায় না। তাই এখানে Claude API
ব্যবহার করে annotate করা হয় (এটাই সবচেয়ে accurate পদ্ধতি)।

Fallback: যদি কোনো কারণে API key না থাকে বা call ব্যর্থ হয়, তাহলে সহজ
rule-based (word-list lookup + কিছু পরিচিত particle) পদ্ধতিতে best-effort
annotate করা হয়, যদিও সেটার accuracy কম।
"""

import re
import streamlit as st
from anthropic import Anthropic

MODEL_NAME = "claude-sonnet-4-5"  # প্রয়োজনে console.anthropic.com এ available model অনুযায়ী বদলাও


SYSTEM_PROMPT = """তুমি একজন Korean-Bangla ভাষা বিশেষজ্ঞ। তোমাকে একটা Korean paragraph দেওয়া হবে।
তোমার কাজ হলো প্রতিটা শব্দ/eojeol (স্পেস দিয়ে আলাদা করা অংশ) এর ঠিক পরে বন্ধনীতে তার বাংলা অর্থ বসিয়ে দেওয়া।

নিয়মঃ
- মূল Korean টেক্সটের word order/বাক্য গঠন হুবহু অক্ষুণ্ণ রাখবে, নতুন কিছু যোগ/বাদ দেবে না।
- প্রতিটা token এর ঠিক পরে বাংলা অর্থ () এর ভিতরে বসাবে। যেমনঃ 한국에서는(কোরিয়াতে)
- Verb/adjective conjugation বুঝে root meaning + grammar/tense বাংলায় বোঝাবে (যেমনঃ 보면 → (দেখলে), 적혀 → (লেখা হয়ে))
- Grammar particle (은/는/이/가/을/를/에/에서/와/과 ইত্যাদি) থাকলে ছোট বাংলা gloss দেবে (যেমনঃ 는 → (টা/এই))
- আমি একটা "পরিচিত word list" (Korean → Bangla) দিচ্ছি — কোনো token এর মূল রূপ (stem) যদি এই list এ থাকে,
  সেই অর্থটাই অগ্রাধিকার দিয়ে ব্যবহার করবে (consistency বজায় রাখতে)।
- বাক্যের মাঝে ".", "," ইত্যাদি bracket এর পরে/token এর সাথে যথাযথভাবে বসাবে। কমা/দাঁড়ি/প্রশ্নবোধক
  চিহ্নের জন্য আলাদা () লাগবে না, এগুলো শুধু আগের word এর bracket এর পরে বসবে।
- ⚠️ অত্যন্ত গুরুত্বপূর্ণ নিষেধাজ্ঞা: bracket এর ভিতরে কখনোই একই Korean word/token হুবহু বসাবে না
  (যেমন 토목은(토목은) সম্পূর্ণ ভুল)। bracket এর ভিতরে সবসময় প্রকৃত বাংলা অনুবাদ/অর্থ থাকতে হবে,
  Korean script কখনোই bracket এর ভিতরে থাকবে না। যদি অর্থ নিশ্চিত না জানো, best guess বাংলা অর্থ দাও,
  Korean word পুনরাবৃত্তি করো না।
- শুধু annotate করা টেক্সট আউটপুট করবে, অন্য কোনো ব্যাখ্যা/preamble দেবে না।

উদাহরণ (input → output):
input: 한국의 달력을 보면 큰 숫자가 있어요.
output: 한국의(কোরিয়ার) 달력을(ক্যালেন্ডারকে) 보면(দেখলে) 큰(বড়) 숫자가(সংখ্যা) 있어요(আছে).
"""


def _filter_relevant_vocab(korean_text, vocab, max_entries=400):
    """পুরো vocab (হাজার হাজার word হতে পারে) না পাঠিয়ে, শুধু paragraph এ
    সম্ভাব্য প্রাসঙ্গিক entry গুলো বেছে পাঠানো হয় (token এর অংশ হিসেবে মিলে গেলে)।"""
    tokens = set(re.findall(r"[가-힣]+", korean_text))
    relevant = {}
    for k, v in vocab.items():
        if not k:
            continue
        for t in tokens:
            if k in t or t in k:
                relevant[k] = v
                break
        if len(relevant) >= max_entries:
            break
    return relevant


def annotate_paragraph_ai(korean_text, vocab: dict):
    """Claude API দিয়ে accurate annotate করে। Returns (annotated_text, None)."""
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY secrets এ পাওয়া যায়নি।")

    client = Anthropic(api_key=api_key)
    relevant_vocab = _filter_relevant_vocab(korean_text, vocab)
    vocab_text = "\n".join(f"{k} = {v}" for k, v in relevant_vocab.items()) or "(কোনো প্রাসঙ্গিক word পাওয়া যায়নি)"

    user_msg = f"""পরিচিত word list (অগ্রাধিকার দাও):
{vocab_text}

Annotate করার Korean paragraph:
{korean_text}"""

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    annotated = "".join(block.text for block in response.content if block.type == "text").strip()
    return annotated, []


def annotate_paragraph_gemini(korean_text, vocab: dict, use_vocab=True):
    """Google Gemini (সম্পূর্ণ ফ্রি tier) দিয়ে accurate annotate করে।
    নতুন google-genai SDK ব্যবহার করা হয়েছে যাতে নতুন 'AQ.' প্রিফিক্স key ও কাজ করে
    (পুরনো google-generativeai library এই নতুন key format সাপোর্ট করে না)।
    use_vocab=False দিলে আমাদের word database একদম ব্যবহার হবে না —
    Gemini তার নিজের জ্ঞান দিয়ে সম্পূর্ণ স্বাধীনভাবে annotate করবে (best quality)।"""
    from google import genai as google_genai

    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY secrets এ পাওয়া যায়নি।")

    client = google_genai.Client(api_key=api_key)

    if use_vocab:
        relevant_vocab = _filter_relevant_vocab(korean_text, vocab)
        vocab_text = "\n".join(f"{k} = {v}" for k, v in relevant_vocab.items()) or "(কোনো প্রাসঙ্গিক word পাওয়া যায়নি)"
        vocab_block = f"পরিচিত word list (অগ্রাধিকার দাও):\n{vocab_text}\n\n"
    else:
        vocab_block = ""

    user_msg = f"""{SYSTEM_PROMPT}

{vocab_block}Annotate করার Korean paragraph:
{korean_text}"""

    # একাধিক বর্তমান free-tier model ক্রমান্বয়ে চেষ্টা করা হয়, যাতে Google কোনো একটা
    # deprecate/quota-0 করে দিলেও app immediately ভেঙে না পড়ে।
    candidate_models = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"]
    last_err = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(model=model_name, contents=user_msg)
            return response.text.strip(), []
        except Exception as e:
            last_err = e
    raise last_err


# ---------- Fallback (rule-based, কম accurate) ----------

PARTICLE_GLOSS = [
    ("에서는", "তে/এ (যেমন)"), ("에게는", "কে (যেমন)"), ("이라고", "বলে"),
    ("하며", "করার সাথে"), ("하고", "করে"), ("처럼", "মতো"), ("부터", "থেকে (শুরু)"),
    ("까지", "পর্যন্ত"), ("에서", "তে/এ"), ("에게", "কে"), ("으로", "দিয়ে/দিকে"),
    ("에는", "তে (যেমন)"), ("보다", "চেয়ে"), ("같이", "মতো"), ("이며", "এবং"),
    ("이나", "বা"), ("는", "টা/এই"), ("은", "টা/এই"), ("가", "টা"), ("이", "টা"),
    ("를", "কে"), ("을", "কে"), ("도", "ও"), ("만", "শুধু"), ("와", "এবং"),
    ("과", "এবং"), ("로", "দিয়ে/দিকে"), ("에", "তে/এ"),
]


def _lookup_with_particle(token, vocab):
    for suffix, gloss in PARTICLE_GLOSS:
        if token.endswith(suffix) and len(token) > len(suffix):
            stem = token[: -len(suffix)]
            if stem in vocab:
                return f"{vocab[stem]}/{gloss}"
    return None


def annotate_paragraph_rule_based(korean_text, vocab: dict):
    tokens = korean_text.split()
    output_parts = []
    unmatched = []
    for token in tokens:
        core = token.strip("?!.,()[]")
        trailing = token[len(core):] if token.startswith(core) else ""
        meaning = vocab.get(core) or _lookup_with_particle(core, vocab)
        if meaning:
            output_parts.append(f"{core}({meaning}){trailing}")
        else:
            output_parts.append(f"{core}(❓){trailing}")
            unmatched.append(core)
    return " ".join(output_parts), unmatched


import re as _re


def _looks_broken(annotated_text):
    """যদি bracket এর ভিতরে হুবহু আগের Korean word-ই থাকে (translate না করে
    echo করা), সেটা ধরে ফেলে — যাতে এই খারাপ output স্বয়ংক্রিয়ভাবে বাদ দিয়ে
    পরের engine চেষ্টা করা যায়।"""
    matches = _re.findall(r"([가-힣]+)\(([^)]*)\)", annotated_text)
    if not matches:
        return False
    same_count = sum(1 for k, v in matches if k == v.strip())
    return same_count / len(matches) > 0.25


def annotate_paragraph(korean_text, vocab: dict, use_online_fallback=True, use_vocab=True):
    """মূল entry point: Anthropic (যদি key থাকে) → Gemini (ফ্রি, যদি key থাকে)
    → rule-based fallback, এই ক্রমে চেষ্টা করে। কোনো engine এর output যদি
    "word(word)" আকারে ভাঙা/echo হয়ে যায়, সেটা বাতিল করে পরেরটা চেষ্টা করে।
    use_vocab=False দিলে AI আমাদের word database না দেখে সম্পূর্ণ স্বাধীনভাবে annotate করবে।"""
    errors = []
    try:
        annotated, unmatched = annotate_paragraph_ai(korean_text, vocab if use_vocab else {})
        if _looks_broken(annotated):
            raise RuntimeError("output এ Korean word নিজেই repeat হয়েছে (translate হয়নি)")
        return annotated, unmatched, "anthropic", None
    except Exception as e:
        errors.append(f"Anthropic: {e}")

    try:
        annotated, unmatched = annotate_paragraph_gemini(korean_text, vocab, use_vocab=use_vocab)
        if _looks_broken(annotated):
            raise RuntimeError("output এ Korean word নিজেই repeat হয়েছে (translate হয়নি)")
        return annotated, unmatched, "gemini", None
    except Exception as e:
        errors.append(f"Gemini: {e}")

    error_detail = " | ".join(errors)
    if not use_online_fallback:
        raise RuntimeError(error_detail)

    annotated, unmatched = annotate_paragraph_rule_based(korean_text, vocab)
    return annotated, unmatched, "rule_based", error_detail
