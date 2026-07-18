"""
একটা Korean paragraph কে tokenize (space অনুযায়ী eojeol ভাগ) করে প্রতিটা
token এর জন্য Bangla meaning বসিয়ে "token(meaning)" আকারে বানায় —
ঠিক যেভাবে ছবিতে দেখানো বই এর স্টাইল।

Strategy (approximate, ১০০% নির্ভুল না — তাই এই output সবসময় editable
আকারে দেখানো হয়, save করার আগে manually check করার সুযোগ থাকে):

1. Token টা হুবহু vocab_words এ আছে কিনা দেখা (exact match)
2. না থাকলে, পরিচিত grammar particle/ending (নিচের তালিকা থেকে, লম্বা
   suffix আগে চেষ্টা করে) কেটে বাকি অংশ (stem) vocab_words এ খোঁজা।
   পেলে stem_meaning + particle_gloss জোড়া লাগানো হয়।
3. তাও না মিললে, deep-translator দিয়ে পুরো token টা সরাসরি translate
   করা হয় (Google Translate, free, internet লাগবে)।
"""

from deep_translator import GoogleTranslator

# পরিচিত Korean particle/ending -> বাংলা gloss (approximate; লম্বা গুলো আগে
# রাখা হয়েছে যাতে suffix matching এ ছোট suffix ভুলভাবে আগে না মিলে যায়)
PARTICLE_GLOSS = [
    ("에서는", "তে/এ (যেমন)"),
    ("에게는", "কে (যেমন)"),
    ("이라고", "বলে"),
    ("하며", "করার সাথে"),
    ("하고", "করে"),
    ("처럼", "মতো"),
    ("부터", "থেকে (শুরু)"),
    ("까지", "পর্যন্ত"),
    ("에서", "তে/এ"),
    ("에게", "কে"),
    ("으로", "দিয়ে/দিকে"),
    ("에는", "তে (যেমন)"),
    ("보다", "চেয়ে"),
    ("같이", "মতো"),
    ("이며", "এবং"),
    ("이나", "বা"),
    ("는", "টা/এই"),
    ("은", "টা/এই"),
    ("가", "টা"),
    ("이", "টা"),
    ("를", "কে"),
    ("을", "কে"),
    ("도", "ও"),
    ("만", "শুধু"),
    ("와", "এবং"),
    ("과", "এবং"),
    ("로", "দিয়ে/দিকে"),
    ("에", "তে/এ"),
]


def _lookup_with_particle(token, vocab):
    """Token এ পরিচিত কোনো particle suffix থাকলে কেটে stem meaning + particle gloss ফেরত দেয়।"""
    for suffix, gloss in PARTICLE_GLOSS:
        if token.endswith(suffix) and len(token) > len(suffix):
            stem = token[: -len(suffix)]
            if stem in vocab:
                return f"{vocab[stem]}/{gloss}"
    return None


def annotate_paragraph(korean_text, vocab: dict, use_online_fallback=True):
    """
    korean_text: raw Korean paragraph (spaces দিয়ে ভাগ করা eojeol)
    vocab: {korean_word: bangla_meaning} dict (আমাদের database থেকে)
    Returns: annotated string "token(meaning) token(meaning) ..."
    """
    tokens = korean_text.split()
    output_parts = []
    unmatched = []

    translator = GoogleTranslator(source="ko", target="bn") if use_online_fallback else None

    for token in tokens:
        # punctuation আলাদা করা (যেমন "안녕하세요?" -> "안녕하세요" + "?")
        core = token.strip("?!.,()[]")
        trailing = token[len(core):] if token.startswith(core) else ""

        meaning = None
        if core in vocab:
            meaning = vocab[core]
        else:
            meaning = _lookup_with_particle(core, vocab)

        if meaning is None and translator is not None:
            try:
                meaning = translator.translate(core)
            except Exception:
                meaning = None
                unmatched.append(core)
        elif meaning is None:
            unmatched.append(core)

        if meaning:
            output_parts.append(f"{core}({meaning}){trailing}")
        else:
            output_parts.append(f"{core}(❓){trailing}")

    return " ".join(output_parts), unmatched
