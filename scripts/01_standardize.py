"""
Step 1 â€” Schema Standardization
================================
Reads each of the 9 raw CSV files and writes a standardized copy to
/data/standardized/ with exactly 3 columns: text, sentiment, language.

Renames:
  - label  -> sentiment  (Gujarati)
  - translated_comment -> text  (English, Malayalam)

Adds language ISO code column to every row.
Never modifies anything under /data/raw/.

Usage:
    python scripts/01_standardize.py
"""

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
STD_DIR = os.path.join(PROJECT_ROOT, "data", "standardized")
VALID_LABELS = {"angry", "neutral", "happy", "sad", "fear"}

# Map: (raw filename, text_col, label_col, language_code, output_filename)
RAW_FILE_CONFIGS = [
    ("cleaned_data_hindi.csv",          "text",               "sentiment", "hi", "hindi.csv"),
    ("cleaned_data_bengali.csv",         "text",               "sentiment", "bn", "bengali.csv"),
    ("cleaned_data_kannada.csv",         "text",               "sentiment", "kn", "kannada.csv"),
    ("cleaned_data_telugu.csv",          "text",               "sentiment", "te", "telugu.csv"),
    ("translated_data_tamil.csv",        "text",               "sentiment", "ta", "tamil.csv"),
    ("gujarati_sentiment_dataset.csv",   "text",               "label",     "gu", "gujarati.csv"),
    ("cleaned_data_marathi.csv",         "text",               "sentiment", "mr", "marathi.csv"),
    ("english_dataset.csv",             "translated_comment", "sentiment", "en", "english.csv"),
    ("malayalam_dataset.csv",           "translated_comment", "sentiment", "ml", "malayalam.csv"),
]


def standardize_file(raw_filename, text_col, label_col, lang_code, out_filename):
    raw_path = os.path.join(RAW_DIR, raw_filename)
    out_path = os.path.join(STD_DIR, out_filename)

    print(f"\n[{lang_code.upper()}] Reading {raw_filename} ...", flush=True)
    df = pd.read_csv(raw_path)
    print(f"  Raw shape: {df.shape} | Columns: {list(df.columns)}")

    # -- Rename text column if needed
    if text_col != "text":
        df = df.rename(columns={text_col: "text"})
    # -- Rename label column if needed
    if label_col != "sentiment":
        df = df.rename(columns={label_col: "sentiment"})

    # -- Keep only the 3 required columns
    df = df[["text", "sentiment"]].copy()

    # -- Add language column
    df["language"] = lang_code

    # -- Normalise label strings (lowercase, strip whitespace)
    df["sentiment"] = df["sentiment"].astype(str).str.lower().str.strip()

    # -- Validation: assert only valid labels
    unique_labels = set(df["sentiment"].unique())
    unknown = unique_labels - VALID_LABELS
    if unknown:
        print(f"  WARNING: Unknown labels found and will be dropped: {unknown}", flush=True)
        df = df[df["sentiment"].isin(VALID_LABELS)]

    # -- Drop rows with null text or sentiment
    before = len(df)
    df = df.dropna(subset=["text", "sentiment"])
    dropped = before - len(df)
    if dropped:
        print(f"  Dropped {dropped} rows with null text/sentiment.")

    # -- Final validation
    assert len(df) > 0, f"No rows remain after standardization for {lang_code}!"
    remaining_labels = set(df["sentiment"].unique())
    print(f"  Output rows: {len(df)} | Labels present: {remaining_labels}")

    # -- Write output (never touches data/raw)
    os.makedirs(STD_DIR, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"  Saved -> {out_path}")
    return len(df)


def main():
    print("=" * 60)
    print("Step 1 â€” Schema Standardization")
    print("=" * 60)
    print(f"RAW_DIR : {RAW_DIR}")
    print(f"STD_DIR : {STD_DIR}")

    total_rows = 0
    for config in RAW_FILE_CONFIGS:
        n = standardize_file(*config)
        total_rows += n

    print(f"\n{'=' * 60}")
    print(f"Standardization complete. Total rows written: {total_rows}")
    print(f"Output files in: {STD_DIR}")

    # Final sanity: verify all 9 output files exist
    outputs = [c[4] for c in RAW_FILE_CONFIGS]
    missing = [f for f in outputs if not os.path.exists(os.path.join(STD_DIR, f))]
    if missing:
        print(f"ERROR: Missing output files: {missing}", file=sys.stderr)
        sys.exit(1)
    print("All 9 standardized files verified. âœ“")


if __name__ == "__main__":
    main()

