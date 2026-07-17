"""
Column auto-detector.
Different chapter files may have different column names
(e.g. "Korean", "한국어", "Word" / "Bangla", "বাংলা", "Meaning").
This module guesses which column is Korean and which is Bangla,
first by name keywords, then by checking the actual script used
in the cell content (Hangul range vs Bangla range).
"""

import re

KOREAN_NAME_HINTS = ["korean", "한국어", "word", "ko"]
BANGLA_NAME_HINTS = ["bangla", "বাংলা", "meaning", "অর্থ", "bn"]

HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
BANGLA_RE = re.compile(r"[\u0980-\u09ff]")


def _script_ratio(series, pattern):
    """Return fraction of non-empty cells in a column matching a script pattern."""
    sample = series.dropna().astype(str).head(30)
    if len(sample) == 0:
        return 0.0
    matches = sum(1 for v in sample if pattern.search(v))
    return matches / len(sample)


def detect_columns(df):
    """
    Returns (korean_col, bangla_col, confidence_note)
    confidence_note explains how the guess was made, so the UI
    can show it to the user for confirmation.
    """
    cols = list(df.columns)
    korean_col, bangla_col = None, None
    note = []

    # Step 1: try column name hints
    for c in cols:
        lc = str(c).lower()
        if korean_col is None and any(h in lc for h in KOREAN_NAME_HINTS):
            korean_col = c
        if bangla_col is None and any(h in lc for h in BANGLA_NAME_HINTS):
            bangla_col = c

    if korean_col:
        note.append(f"Column name দেখে '{korean_col}' কে Korean ধরা হয়েছে")
    if bangla_col:
        note.append(f"Column name দেখে '{bangla_col}' কে Bangla ধরা হয়েছে")

    # Step 2: fall back to script detection for whichever is still missing
    remaining = [c for c in cols if c not in (korean_col, bangla_col)]

    if korean_col is None:
        best, best_score = None, 0.0
        for c in remaining:
            score = _script_ratio(df[c], HANGUL_RE)
            if score > best_score:
                best, best_score = c, score
        if best and best_score > 0.3:
            korean_col = best
            note.append(f"Content-এ Hangul script দেখে '{best}' কে Korean ধরা হয়েছে")

    if bangla_col is None:
        best, best_score = None, 0.0
        for c in remaining:
            if c == korean_col:
                continue
            score = _script_ratio(df[c], BANGLA_RE)
            if score > best_score:
                best, best_score = c, score
        if best and best_score > 0.3:
            bangla_col = best
            note.append(f"Content-এ Bangla script দেখে '{best}' কে Bangla ধরা হয়েছে")

    return korean_col, bangla_col, note
