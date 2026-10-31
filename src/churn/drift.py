"""Statistical data drift and delivery gate comparing incoming data against reference data.

Usage:
    uv run python -m churn.drift [incoming_csv] [reference_csv]
"""

import os
import sys
from pathlib import Path

import pandas as pd

from churn.data import CATEGORICAL_FEATURES, DATA_DIR, NUMERIC_FEATURES, TARGET

# Exclude derived feature 'kostnad_per_gb' which is computed after raw CSV loading
RAW_NUMERIC_COLS = [col for col in NUMERIC_FEATURES if col != "kostnad_per_gb"]
DEFAULT_REFERENCE = DATA_DIR / "kundbas.csv"

MAX_MEAN_SHIFT_STD = 0.50  # Maximum allowed shift in mean (relative to reference std)
MAX_TARGET_DIFF = 0.15  # Maximum allowed absolute shift in churn rate (15 percentage points)


def check_delivery_drift(
    incoming_path: Path, reference_path: Path = DEFAULT_REFERENCE
) -> list[str]:
    """Compare an incoming dataset against reference data and return any drift errors."""
    if not incoming_path.is_file():
        return [f"Incoming file not found: {incoming_path}"]
    if not reference_path.is_file():
        return [f"Reference file not found: {reference_path}"]

    ref_df = pd.read_csv(reference_path)
    inc_df = pd.read_csv(incoming_path)
    errors: list[str] = []

    # 1. Volume sanity check (guards against drops > 50%)
    min_expected_rows = int(0.5 * len(ref_df))
    if len(inc_df) < min_expected_rows:
        errors.append(
            f"Volume drop: incoming data has {len(inc_df)} rows, expected >= {min_expected_rows}"
        )

    # 2. Numeric distribution drift check (Z-score shift)
    for col in RAW_NUMERIC_COLS:
        if col not in inc_df.columns or col not in ref_df.columns:
            errors.append(f"Missing column: {col}")
            continue

        ref_mean = ref_df[col].dropna().mean()
        ref_std = ref_df[col].dropna().std()
        inc_mean = inc_df[col].dropna().mean()

        if ref_std > 0:
            normalized_shift = abs(inc_mean - ref_mean) / ref_std
            if normalized_shift > MAX_MEAN_SHIFT_STD:
                errors.append(
                    f"Data drift in '{col}': mean shifted from {ref_mean:.2f} to {inc_mean:.2f} "
                    f"({normalized_shift:.2f} std > {MAX_MEAN_SHIFT_STD:.2f} threshold)"
                )

    # 3. Categorical distribution check (flags unseen categories)
    for col in CATEGORICAL_FEATURES:
        if col not in inc_df.columns or col not in ref_df.columns:
            errors.append(f"Missing column: {col}")
            continue

        ref_cats = set(ref_df[col].dropna().unique())
        inc_cats = set(inc_df[col].dropna().unique())
        unseen = inc_cats - ref_cats
        if unseen:
            errors.append(f"Unseen categories in '{col}': {sorted(unseen)}")

    # 4. Target rate shift check
    if TARGET in inc_df.columns and TARGET in ref_df.columns:
        ref_rate = ref_df[TARGET].dropna().mean()
        inc_rate = inc_df[TARGET].dropna().mean()
        if abs(inc_rate - ref_rate) > MAX_TARGET_DIFF:
            shift_msg = f"rate shifted from {ref_rate:.2%} to {inc_rate:.2%}"
            errors.append(f"Target drift in '{TARGET}': {shift_msg}")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    incoming = Path(args[0]) if len(args) >= 1 else DEFAULT_REFERENCE
    reference = Path(args[1]) if len(args) >= 2 else DEFAULT_REFERENCE
    expect_drift = os.environ.get("EXPECT_DRIFT", "pass")

    lines = [f"Running data drift check: '{incoming}' against reference '{reference}'..."]
    errors = check_delivery_drift(incoming, reference)

    if errors:
        lines.append(f"DRIFT CHECK FAILED ({len(errors)} error(s) detected):")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append(f"OK: Dataset '{incoming}' passed all statistical drift checks.")

    output = "\n".join(lines)
    print(output)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(
                f"### Drift Check: `{incoming}` (expected: {expect_drift})\n```\n{output}\n```\n"
            )

    passed = len(errors) == 0
    if expect_drift == "pass" and not passed:
        return 1
    if expect_drift == "fail" and passed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
