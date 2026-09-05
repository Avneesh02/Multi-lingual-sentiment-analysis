"""
Step 2 â€” Downsample Marathi
============================
Marathi has ~14,638 rows vs ~5,000 for every other language.
This script downsamples it to 5,000 using STRATIFIED sampling
(proportional within each sentiment class) so rare classes like
`fear` are not accidentally wiped out before balancing.

Input:  data/standardized/marathi.csv  (read-only from Step 1)
Output: data/standardized/marathi.csv  (replaced â€” raw file untouched)

Usage:
    python scripts/02_downsample_marathi.py
"""

import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STD_DIR = os.path.join(PROJECT_ROOT, "data", "standardized")
MARATHI_FILE = os.path.join(STD_DIR, "marathi.csv")
TARGET_ROWS = 5_000
RANDOM_SEED = 42


def stratified_downsample(df: pd.DataFrame, target_n: int, seed: int) -> pd.DataFrame:
    """
    Downsample df to target_n rows proportionally within each `sentiment` class.
    Uses sklearn train_test_split with stratify= which handles small classes gracefully.
    """
    if len(df) <= target_n:
        return df  # already small enough
    # We want to KEEP `target_n` rows, so the "test" fraction = target_n / total
    keep_frac = target_n / len(df)
    _, keep_df = train_test_split(
        df,
        test_size=keep_frac,
        stratify=df["sentiment"],
        random_state=seed,
    )
    return keep_df.reset_index(drop=True)


def main():
    print("=" * 60)
    print("Step 2 â€” Stratified Downsample Marathi (14,638 â†’ 5,000)")
    print("=" * 60)

    if not os.path.exists(MARATHI_FILE):
        print(f"ERROR: {MARATHI_FILE} not found. Run 01_standardize.py first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(MARATHI_FILE)
    print(f"\nMarathi BEFORE downsampling: {len(df)} rows")
    print("Class distribution (before):")
    print(df["sentiment"].value_counts().to_string())

    df_downsampled = stratified_downsample(df, TARGET_ROWS, RANDOM_SEED)

    print(f"\nMarathi AFTER downsampling: {len(df_downsampled)} rows")
    print("Class distribution (after):")
    print(df_downsampled["sentiment"].value_counts().to_string())

    # Verify
    assert len(df_downsampled) == TARGET_ROWS, (
        f"Expected {TARGET_ROWS} rows, got {len(df_downsampled)}"
    )
    missing_classes = set(df["sentiment"].unique()) - set(df_downsampled["sentiment"].unique())
    if missing_classes:
        print(f"WARNING: These classes disappeared after downsampling: {missing_classes}")

    # Save (overwrites the standardized Marathi file; raw/cleaned_data_marathi.csv untouched)
    df_downsampled.to_csv(MARATHI_FILE, index=False, encoding="utf-8")
    print(f"\nSaved -> {MARATHI_FILE}")
    print("Marathi downsample complete. âœ“")


if __name__ == "__main__":
    main()

