"""
Core logic: given a chapter's raw dataframe + the set of words
already seen in the database, return only the words that are
new (not seen before) and de-duplicated within the file itself.
"""

import pandas as pd


def get_new_unique_words(df: pd.DataFrame, korean_col: str, bangla_col: str, existing_words: dict):
    """
    Returns a cleaned DataFrame with columns [Korean, Bangla] containing
    only words that are:
      1. not empty
      2. de-duplicated within this chapter's file
      3. not already present in `existing_words` (the full DB so far)
    """
    clean = df[[korean_col, bangla_col]].copy()
    clean.columns = ["Korean", "Bangla"]
    clean["Korean"] = clean["Korean"].astype(str).str.strip()
    clean["Bangla"] = clean["Bangla"].astype(str).str.strip()

    # drop empty rows
    clean = clean[(clean["Korean"] != "") & (clean["Korean"].str.lower() != "nan")]

    total_in_file = len(clean)

    # de-dup within this file, keep first occurrence
    clean = clean.drop_duplicates(subset="Korean", keep="first")

    # drop words already present in the database
    clean = clean[~clean["Korean"].isin(existing_words.keys())]

    return clean.reset_index(drop=True), total_in_file
