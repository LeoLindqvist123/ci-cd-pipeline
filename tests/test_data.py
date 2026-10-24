"""Test level 2: data. Does the data look as expected?"""

from churn.data import FEATURES, TARGET, create_features, load_data


def test_expected_columns_exist():
    df = create_features(load_data())
    assert set(FEATURES + [TARGET]) <= set(df.columns)


def test_target_variable_is_binary():
    assert set(load_data()[TARGET].unique()) <= {0, 1}
