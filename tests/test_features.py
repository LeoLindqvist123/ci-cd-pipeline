"""Test level 1: code. Unit tests for feature engineering, without a model or real data."""

import pandas as pd
import pytest

from churn.data import create_features


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "manadskostnad": [299.0, 149.0],
            "data_gb_per_manad": [9.0, 0.0],
            "region": [" stockholm", "Väst"],
        }
    )


def test_cost_per_gb(sample_df):
    result = create_features(sample_df)
    assert result["kostnad_per_gb"].tolist() == pytest.approx([29.9, 149.0])


def test_region_is_normalized(sample_df):
    assert create_features(sample_df)["region"].tolist() == ["Stockholm", "Väst"]


def test_input_data_is_not_modified(sample_df):
    original = sample_df.copy()
    create_features(sample_df)
    pd.testing.assert_frame_equal(sample_df, original)

def test_uppercase_regions_are_normalized():
    df = pd.DataFrame( #random data för kod test
        {
            "manadskostnad": [199.0, 199.0],
            "data_gb_per_manad": [5.0, 5.0],
            "region": ["STOCKHOLM", "  VÄST  "],
        }
    )
    assert create_features(df)["region"].tolist() == ["Stockholm", "Väst"]
