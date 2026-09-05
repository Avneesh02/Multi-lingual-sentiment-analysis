"""
Step 4 â€” Clean Balanced Data
==============================
Applied AFTER balancing to avoid undoing class targets from Step 3.

Cleaning operations per language:
  - Drop rows with null or whitespace-only `text`
  - Drop rows with null or invalid `sentiment`
  - Strip emoji-only rows (text contains no Unicode letter or digit)
  - Strip punctuation-only rows
  - Normalize whitespace (collapse multiple spaces/newlines/tabs)
  - Remove exact duplicates (within each language)
  - Log any near-duplicate pairs (Jaccard token similarity > 0.95, sampled)

Re-checks class balance after cleaning and logs drift.

Input:  data/balanced/*.csv
Output: data/balanced/*.csv  (in-place overwrite of balanced files)
        Writes to data/standardized/ or data/raw/ is NEVER done.

Usage:
    python scripts/04_clean.py
"""

import os
import re
import sys
import unicodedata
import pandas as pd

# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAL_DIR = os.path.join(PROJECT_ROOT, "data", "balanced")
VALID_LABELS = {"angry", "neutral", "happy", "sad", "fear"}
LANG_FILES = [
    ("hi", "hindi.csv"),
    ("bn", "bengali.csv"),
    ("kn", "kannada.csv"),
    ("te", "telugu.csv"),
    ("ta", "tamil.csv"),
    ("gu", "gujarati.csv"),
    ("mr", "marathi.csv"),
    ("en", "english.csv"),
    ("ml", "malayalam.csv"),
]

# Regex: text is "meaningful" only if it contains at least one Unicode letter or digit
_LETTER_OR_DIGIT = re.compile(r"[\w]", re.UNICODE)


def has_meaningful_content(text: str) -> bool:
    """Return True if text contains at least one letter or digit (Unicode-aware)."""
    return bool(_LETTER_OR_DIGIT.search(str(text)))


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into a single space and strip ends."""
    return re.sub(r"\s+", " ", str(text)).strip()


def jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a and not tokens_b:
        return 1.0
    inter = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(inter) / len(union)


def find_near_duplicates(df: pd.DataFrame, sample_size: int = 500,
                         threshold: float = 0.95) -> int:
    """
    Sample up to `sample_size` rows and estimate how many near-duplicate pairs exist.
    Returns count of near-duplicate pairs found in the sample.
    """
    if len(df) > sample_size:
        sample = df["text"].sample(sample_size, random_state=42).tolist()
    else:
        sample = df["text"].tolist()

    tokenized = [set(str(t).lower().split()) for t in sample]
    near_dup_count = 0
    n = len(tokenized)
    for i in range(n):
        for j in range(i + 1, min(i + 20, n)):  # only check nearby pairs for speed
            if jaccard_similarity(tokenized[i], tokenized[j]) >= threshold:
                near_dup_count += 1
    return near_dup_count


def clean_language(df: pd.DataFrame, lang_code: str) -> pd.DataFrame:
    n_start = len(df)
    stats = {}

    # 1. Normalize whitespace first
    df["text"] = df["text"].apply(normalize_whitespace)
    df["sentiment"] = df["sentiment"].astype(str).str.lower().str.strip()

    # 2. Drop null / empty text
    mask_null = df["text"].isnull() | (df["text"].str.strip() == "")
    stats["null_empty_text"] = mask_null.sum()
    df = df[~mask_null]

    # 3. Drop null / invalid sentiment
    mask_bad_label = ~df["sentiment"].isin(VALID_LABELS)
    stats["invalid_sentiment"] = mask_bad_label.sum()
    df = df[~mask_bad_label]

    # 4. Drop emoji-only / punctuation-only (no letter or digit)
    mask_no_content = ~df["text"].apply(has_meaningful_content)
    stats["emoji_or_punct_only"] = mask_no_content.sum()
    df = df[~mask_no_content]

    # 5. Remove exact duplicates (keep first within language)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["text", "language"], keep="first")
    stats["exact_duplicates_removed"] = before_dedup - len(df)

    # 6. Near-duplicate check (informational only â€” we log but don't auto-remove
    #    since aggressive removal after balancing could destabilize class counts)
    near_dups = find_near_duplicates(df)
    stats["near_dup_pairs_in_sample"] = near_dups

    n_end = len(df)
    stats["rows_start"] = n_start
    stats["rows_end"] = n_end
    stats["rows_dropped"] = n_start - n_end

    print(f"\n  [{lang_code.upper()}] Cleaning summary:")
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # 7. Post-clean class balance check
    dist_after = df["sentiment"].value_counts().to_dict()
    print(f"  Class distribution after cleaning: {dist_after}")

    return df.reset_index(drop=True)


def main():
    print("=" * 60)
    print("Step 4 â€” Clean Balanced Data")
    print("=" * 60)

    all_drift = []

    for lang_code, filename in LANG_FILES:
        filepath = os.path.join(BAL_DIR, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: {filepath} not found. Run step 3 first.", file=sys.stderr)
            sys.exit(1)

        df = pd.read_csv(filepath)
        dist_before = df["sentiment"].value_counts().to_dict()

        df_clean = clean_language(df, lang_code)

        dist_after = df_clean["sentiment"].value_counts().to_dict()

        # Compute drift: how much did each class change?
        for label in VALID_LABELS:
            before = dist_before.get(label, 0)
            after = dist_after.get(label, 0)
            if before != after:
                all_drift.append({
                    "language": lang_code, "label": label,
                    "before": before, "after": after,
                    "delta": after - before,
                })

        # Overwrite balanced file in-place (data/raw and data/standardized untouched)
        df_clean.to_csv(filepath, index=False, encoding="utf-8")
        print(f"  Saved -> {filepath}")

    print(f"\n{'=' * 60}")
    if all_drift:
        drift_df = pd.DataFrame(all_drift)
        print("Class distribution DRIFT after cleaning (language/label combos that changed):")
        print(drift_df.to_string(index=False))
    else:
        print("No class distribution drift detected after cleaning. âœ“")

    print("\nCleaning complete. âœ“")


if __name__ == "__main__":
    main()

