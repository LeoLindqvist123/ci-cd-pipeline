"""Data loading and feature engineering. Pure functions that can be unit tested.

Do not change this file during the exercises. The work focuses on the pipeline, not the model.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

TARGET = "avslutat"
NUMERIC_FEATURES = [
    "alder",
    "manader_som_kund",
    "manadskostnad",
    "data_gb_per_manad",
    "supportarenden_12m",
    "kostnad_per_gb",
]
CATEGORICAL_FEATURES = ["region", "abonnemang"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_data(filename: str = "kundbas.csv") -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / filename)


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns without modifying the input data."""
    result = df.copy()
    # Add 1 so customers with zero data usage do not cause division by zero.
    result["kostnad_per_gb"] = result["manadskostnad"] / (result["data_gb_per_manad"] + 1)
    result["region"] = result["region"].str.strip().str.title()
    return result


def split_features_and_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[FEATURES], df[TARGET]
