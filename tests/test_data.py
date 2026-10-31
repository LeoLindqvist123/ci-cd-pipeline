"""Test level 2: data. Does the data look as expected?"""

import pandas as pd

from churn.data import DATA_DIR, FEATURES, TARGET, create_features, load_data
from churn.drift import check_delivery_drift

REFERENCE_FILE = DATA_DIR / "kundbas.csv"


def test_expected_columns_exist():
    df = create_features(load_data())
    assert set(FEATURES + [TARGET]) <= set(df.columns)


def test_target_variable_is_binary():
    assert set(load_data()[TARGET].unique()) <= {0, 1}


def test_drift_check_passes_on_identical_reference():
    """Reference data compared against itself should produce zero drift errors."""
    errors = check_delivery_drift(REFERENCE_FILE, REFERENCE_FILE)
    assert errors == []


def test_drift_check_catches_mean_drift(tmp_path):
    """Detect when an incoming delivery has a drifted numeric feature."""
    df = pd.read_csv(REFERENCE_FILE)

    # Simulate extreme drift by artificially increasing monthly cost by 300 SEK
    df["manadskostnad"] = df["manadskostnad"] + 300.0
    drifted_file = tmp_path / "drifted_kundbas.csv"
    df.to_csv(drifted_file, index=False)

    errors = check_delivery_drift(drifted_file, REFERENCE_FILE)
    assert any("manadskostnad" in err for err in errors)


def test_drift_check_catches_volume_drop(tmp_path):
    """Detect when an incoming delivery drops significantly in row count."""
    df = pd.read_csv(REFERENCE_FILE).head(10)  # Only 10 rows
    small_file = tmp_path / "small_kundbas.csv"
    df.to_csv(small_file, index=False)

    errors = check_delivery_drift(small_file, REFERENCE_FILE)
    assert any("Volume drop" in err for err in errors)


def test_drift_check_catches_target_drift(tmp_path):
    """Detect when churn target rate ('avslutat') shifts beyond threshold."""
    df = pd.read_csv(REFERENCE_FILE)
    df[TARGET] = 1  # 100% churn rate
    target_drifted_file = tmp_path / "target_drifted.csv"
    df.to_csv(target_drifted_file, index=False)

    errors = check_delivery_drift(target_drifted_file, REFERENCE_FILE)
    assert any(TARGET in err for err in errors)
