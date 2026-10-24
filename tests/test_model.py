"""Test level 3: modell. Contract and reproducibility."""


import numpy as np
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from churn.data import FEATURES, create_features, load_data, split_features_and_target
from churn.model import SEED, train_and_evaluate


@pytest.fixture(scope="module")
def results():
    return train_and_evaluate()


def test_model_contract(results):
    model, _ = results
    features, _ = split_features_and_target(create_features(load_data().head(5)))
    assert list(features.columns) == FEATURES
    probabilities = model.predict_proba(features)
    assert probabilities.shape == (5, 2)
    assert np.all((probabilities >= 0) & (probabilities <= 1))


def test_reproducible(results):
    _, metrics = results
    _, again = train_and_evaluate()
    assert again == metrics

def test_roc_auc_at_least_070(results):
    _, metrics = results
    assert metrics["roc_auc"] >= 0.70


def test_beats_dummy(results):
    _, metrics = results
    X, y = split_features_and_target(create_features(load_data()))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )
    dummy = DummyClassifier(strategy="prior").fit(X_train, y_train)
    dummy_auc = roc_auc_score(y_test, dummy.predict_proba(X_test)[:, 1])
    assert metrics["roc_auc"] > dummy_auc
