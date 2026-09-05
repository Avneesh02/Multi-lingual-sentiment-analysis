"""
Step 5 â€” Merge All Languages and Create Train/Val/Test Splits
==============================================================
Merges all 9 cleaned per-language CSVs from data/balanced/ into one
combined dataset, then splits into:
  - Train: 80%
  - Validation: 10%
  - Test: 10%

Stratification is done jointly on (language, sentiment) so every
language Ã— emotion combination is proportionally represented in all splits.

Output: data/final/train.csv, val.csv, test.csv  (and .json equivalents)

Usage:
    python scripts/05_merge_split.py
"""

import os
import sys
import json
import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAL_DIR = os.path.join(PROJECT_ROOT, "data", "balanced")
FINAL_DIR = os.path.join(PROJECT_ROOT, "data", "final")
RANDOM_SEED = 42
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


def stratified_split(df: pd.DataFrame, test_size: float = 0.1, val_size: float = 0.1,
                     seed: int = 42):
    """
    Two-stage stratified split on combined language+sentiment key:
      Stage 1: df -> train_val (90%) + test (10%)
      Stage 2: train_val -> train (88.9%) + val (11.1%) => giving ~80/10/10 overall
    """
    strat_key = df["language"] + "_" + df["sentiment"]

    # Stage 1: hold out test
    train_val, test = train_test_split(
        df, test_size=test_size, stratify=strat_key, random_state=seed
    )

    # Stage 2: hold out val from train_val
    strat_key_tv = train_val["language"] + "_" + train_val["sentiment"]
    # val_size as fraction of train_val: val_size / (1 - test_size)
    val_frac = val_size / (1.0 - test_size)
    train, val = train_test_split(
        train_val, test_size=val_frac, stratify=strat_key_tv, random_state=seed
    )

    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)


def print_split_distribution(name: str, df: pd.DataFrame):
    print(f"\n  {name} ({len(df)} rows):")
    pivot = df.groupby(["language", "sentiment"]).size().unstack(fill_value=0)
    print(pivot.to_string())


def save_split(df: pd.DataFrame, base_name: str):
    csv_path = os.path.join(FINAL_DIR, f"{base_name}.csv")
    json_path = os.path.join(FINAL_DIR, f"{base_name}.json")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"  Saved {csv_path}  ({len(df)} rows)")
    print(f"  Saved {json_path}")


def main():
    print("=" * 60)
    print("Step 5 â€” Merge and Split (80/10/10)")
    print("=" * 60)

    # -- Load and merge all balanced/cleaned CSVs
    frames = []
    for lang_code, filename in LANG_FILES:
        path = os.path.join(BAL_DIR, filename)
        if not os.path.exists(path):
            print(f"ERROR: {path} not found. Run steps 3 and 4 first.", file=sys.stderr)
            sys.exit(1)
        df = pd.read_csv(path)
        if "language" not in df.columns:
            df["language"] = lang_code
        frames.append(df)
        print(f"  Loaded {filename}: {len(df)} rows")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\nCombined dataset: {len(combined)} rows")
    print(f"Languages: {sorted(combined['language'].unique())}")
    print(f"Labels:    {sorted(combined['sentiment'].unique())}")

    # -- Stratified split
    train, val, test = stratified_split(combined, test_size=0.1, val_size=0.1,
                                        seed=RANDOM_SEED)

    print(f"\nSplit sizes:  train={len(train)}, val={len(val)}, test={len(test)}")
    total_check = len(train) + len(val) + len(test)
    assert total_check == len(combined), (
        f"Row count mismatch: {total_check} != {len(combined)}"
    )

    # -- Show per-split distribution
    print_split_distribution("TRAIN", train)
    print_split_distribution("VAL", val)
    print_split_distribution("TEST", test)

    # -- Save
    os.makedirs(FINAL_DIR, exist_ok=True)
    save_split(train, "train")
    save_split(val, "val")
    save_split(test, "test")

    print("\nMerge & split complete. âœ“")


if __name__ == "__main__":
    main()

