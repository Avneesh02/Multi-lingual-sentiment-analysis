"""
Step 3 â€” Per-Language Label Balancing
=======================================
For each language independently:
  1. Compute target_count = floor(total_rows / 5) per class
  2. UNDERSAMPLE majority classes (angry, neutral) via RandomUnderSampler
  3. OVERSAMPLE minority classes (fear, sad) via light text augmentation
     using nlpaug RandomWordAug (insert/delete/swap on Unicode tokens).
     Falls back to plain row duplication if nlpaug is unavailable.

Input:  data/standardized/*.csv   (read-only)
Output: data/balanced/*.csv
        data/balanced/label_distribution_report.csv

Usage:
    python scripts/03_balance_labels.py [--no-augment]
"""

import os
import sys
import argparse
import random
import math
import pandas as pd
import numpy as np
from collections import Counter

# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STD_DIR = os.path.join(PROJECT_ROOT, "data", "standardized")
BAL_DIR = os.path.join(PROJECT_ROOT, "data", "balanced")
VALID_LABELS = ["angry", "neutral", "happy", "sad", "fear"]
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
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Augmentation helpers
# ---------------------------------------------------------------------------
NLPAUG_AVAILABLE = False
try:
    import nlpaug.augmenter.word as naw
    NLPAUG_AVAILABLE = True
    print("[INFO] nlpaug is available â€” will use word-level augmentation.")
except ImportError:
    print("[WARN] nlpaug not installed â€” falling back to plain row duplication for oversampling.")


def build_augmenter():
    """Return an nlpaug RandomWordAug that randomly swaps/inserts/deletes words."""
    if not NLPAUG_AVAILABLE:
        return None
    # RandomWordAug with action='swap' is language-agnostic and works on any Unicode text
    aug = naw.RandomWordAug(action="swap", aug_p=0.15)
    return aug


def augment_text(text: str, augmenter) -> str:
    """Apply one augmentation pass; return original on failure."""
    if augmenter is None:
        return text
    try:
        result = augmenter.augment(text)
        if isinstance(result, list):
            result = result[0]
        return result if result and result.strip() else text
    except Exception:
        return text


def oversample_with_augmentation(df_class: pd.DataFrame, target_n: int,
                                  augmenter, seed: int) -> pd.DataFrame:
    """
    Oversample df_class from len(df_class) to target_n rows.
    New rows are augmented copies of randomly-sampled originals.
    Falls back to plain duplication if augmenter is None (with code comment below).
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    existing = df_class.copy()
    needed = target_n - len(existing)
    if needed <= 0:
        return existing

    # Sample rows to augment
    source_rows = existing.sample(n=needed, replace=True, random_state=seed)
    new_rows = []
    for _, row in source_rows.iterrows():
        new_text = augment_text(str(row["text"]), augmenter)
        # FALLBACK NOTE: if augmenter is None (nlpaug unavailable), augment_text
        # returns the original string â€” this is plain row duplication. The
        # model won't memorize exact duplicates after cleaning (Step 4) removes
        # exact duplicates, but diversity is lower. Comment documents fallback.
        new_rows.append({"text": new_text, "sentiment": row["sentiment"],
                          "language": row["language"]})

    augmented = pd.DataFrame(new_rows)
    return pd.concat([existing, augmented], ignore_index=True)


# ---------------------------------------------------------------------------
# Core balancing logic
# ---------------------------------------------------------------------------

def balance_language(df: pd.DataFrame, lang_code: str, augmenter,
                     report_rows: list) -> pd.DataFrame:
    """
    Balance one language's DataFrame to equal class distribution.
    Pre-deduplicates on text to ensure target_per_class is computed on
    the actual unique-row count (avoids Gujarati-style datasets where the
    raw file has heavy exact duplicates that Step 4 would later remove,
    leaving classes massively unbalanced).
    Returns the balanced DataFrame.
    """
    from imblearn.under_sampling import RandomUnderSampler

    # Pre-deduplicate: remove exact text duplicates before computing target
    n_raw = len(df)
    df = df.drop_duplicates(subset=["text"], keep="first").copy()
    if len(df) < n_raw:
        print(f"  [{lang_code.upper()}] Pre-dedup: {n_raw} -> {len(df)} unique rows")

    total = len(df)
    target_per_class = math.floor(total / 5)
    counts_before = df["sentiment"].value_counts().to_dict()

    print(f"\n  [{lang_code.upper()}] total={total}, target_per_class={target_per_class}")
    print(f"  Before: {counts_before}")

    # -- Early exit if already perfectly balanced
    if all(abs(v - target_per_class) <= 1 for v in counts_before.values()):
        print(f"  Already balanced â€” skipping augmentation/undersampling.")
        for label in VALID_LABELS:
            report_rows.append({
                "language": lang_code, "label": label,
                "count_before": counts_before.get(label, 0),
                "count_after": counts_before.get(label, 0),
                "action": "none",
            })
        return df.copy()

    balanced_parts = []
    for label in VALID_LABELS:
        subset = df[df["sentiment"] == label].copy()
        n_have = len(subset)

        if n_have == 0:
            # Create placeholder (shouldn't happen after Step 1 validation)
            print(f"  WARNING: label '{label}' has 0 rows for {lang_code} â€” skipping.")
            action = "skipped_zero"
            n_after = 0
        elif n_have > target_per_class:
            # Undersample
            subset = subset.sample(n=target_per_class, random_state=RANDOM_SEED)
            action = "undersampled"
            n_after = len(subset)
        elif n_have < target_per_class:
            # Oversample with augmentation
            subset = oversample_with_augmentation(
                subset, target_per_class, augmenter, seed=RANDOM_SEED + hash(label) % 1000
            )
            action = "oversampled" + ("_augmented" if NLPAUG_AVAILABLE else "_duplicated")
            n_after = len(subset)
        else:
            action = "unchanged"
            n_after = n_have

        balanced_parts.append(subset)
        report_rows.append({
            "language": lang_code, "label": label,
            "count_before": n_have,
            "count_after": n_after,
            "action": action,
        })

    result = pd.concat(balanced_parts, ignore_index=True)
    counts_after = result["sentiment"].value_counts().to_dict()
    print(f"  After:  {counts_after}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Step 3 â€” Balance labels per language")
    parser.add_argument("--no-augment", action="store_true",
                        help="Disable nlpaug augmentation (use plain duplication)")
    args = parser.parse_args()

    print("=" * 60)
    print("Step 3 â€” Per-Language Label Balancing")
    print("=" * 60)

    os.makedirs(BAL_DIR, exist_ok=True)
    augmenter = None if args.no_augment else build_augmenter()

    report_rows = []

    for lang_code, filename in LANG_FILES:
        src_path = os.path.join(STD_DIR, filename)
        dst_path = os.path.join(BAL_DIR, filename)

        if not os.path.exists(src_path):
            print(f"ERROR: {src_path} not found. Run steps 1 and 2 first.", file=sys.stderr)
            sys.exit(1)

        df = pd.read_csv(src_path)
        # Ensure language column is present
        if "language" not in df.columns:
            df["language"] = lang_code

        df_balanced = balance_language(df, lang_code, augmenter, report_rows)

        df_balanced.to_csv(dst_path, index=False, encoding="utf-8")
        print(f"  Saved -> {dst_path}  ({len(df_balanced)} rows)")

    # Save distribution report
    report_df = pd.DataFrame(report_rows)
    report_path = os.path.join(BAL_DIR, "label_distribution_report.csv")
    report_df.to_csv(report_path, index=False)
    print(f"\n{'=' * 60}")
    print(f"Label distribution report saved -> {report_path}")
    print("\n--- FULL REPORT ---")
    print(report_df.to_string(index=False))
    print("\nBalancing complete. âœ“")


if __name__ == "__main__":
    main()

