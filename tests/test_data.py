"""Test level 2: data validation and statistical drift checks."""

from pathlib import Path

import pandas as pd

from churn.data import load_data
from churn.drift import check_delivery_drift


def test_kundbas_structure():
    """Verify raw dataset can be read and contains required rows and columns."""
    df = load_data()
    assert not df.empty
    assert len(df.columns) > 5


def test_drift_check_passes_on_identical_reference():
    """Reference data compared against itself should produce zero drift errors."""
    ref_file = Path("data/kundbas.csv")
    errors = check_delivery_drift(ref_file, ref_file)
    assert errors == []


def test_drift_check_catches_mean_drift(tmp_path):
    """Detect when an incoming delivery has a drifted numeric feature."""
    ref_file = Path("data/kundbas.csv")
    df = pd.read_csv(ref_file)

    # Simulate extreme drift by artificially increasing monthly cost by 300 SEK
    df["manadskostnad"] = df["manadskostnad"] + 300.0
    drifted_file = tmp_path / "drifted_kundbas.csv"
    df.to_csv(drifted_file, index=False)

    errors = check_delivery_drift(drifted_file, ref_file)
    assert any("manadskostnad" in err for err in errors)


def test_drift_check_catches_volume_drop(tmp_path):
    """Detect when an incoming delivery drops significantly in row count."""
    ref_file = Path("data/kundbas.csv")
    df = pd.read_csv(ref_file).head(10)  # Only 10 rows
    small_file = tmp_path / "small_kundbas.csv"
    df.to_csv(small_file, index=False)

    errors = check_delivery_drift(small_file, ref_file)
    assert any("Volume drop" in err for err in errors)
