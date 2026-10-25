"""Test level 3: modell. Contract and reproducibility."""

import hashlib
import json

import numpy as np
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from churn.data import DATA_DIR, FEATURES, create_features, load_data, split_features_and_target
from churn.evaluate import DEFAULT_THRESHOLD
from churn.evaluate import main as evaluate_main
from churn.model import DATA_FILE, SEED, train_and_evaluate
from churn.model import main as train_main


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

def test_roc_auc_meets_threshold(results):
    _, metrics = results

    assert metrics["roc_auc"] >= DEFAULT_THRESHOLD


def test_model_performs_better_than_dummy(results):
    _, metrics = results
    X, y = split_features_and_target(create_features(load_data()))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )
    dummy = DummyClassifier(strategy="prior").fit(X_train, y_train)
    dummy_auc = roc_auc_score(y_test, dummy.predict_proba(X_test)[:, 1])

    assert metrics["roc_auc"] > dummy_auc


def test_model_versioning_metadata(tmp_path, monkeypatch):
    """Verify that model training saves versioned artifacts and full lineage metadata."""
    monkeypatch.setenv("GITHUB_SHA", "test-sha-12345")

    train_main(tmp_path)

    model_file = tmp_path / "model.joblib"
    metrics_file = tmp_path / "metrics.json"

    assert model_file.exists(), "Model artifact file was not created"
    assert metrics_file.exists(), "Metadata and metrics file was not created"

    expected_sha256 = hashlib.sha256((DATA_DIR / DATA_FILE).read_bytes()).hexdigest()

    metadata = json.loads(metrics_file.read_text())

    assert metadata["commit"] == "test-sha-12345"
    assert metadata["data_file"] == DATA_FILE
    assert metadata["data_sha256"] == expected_sha256
    assert "roc_auc" in metadata
    assert "accuracy" in metadata


@pytest.mark.parametrize(
    ("roc_auc", "expected_exit_code"),
    [
        (0.50, 1),  # Well below threshold -> fail
        (DEFAULT_THRESHOLD - 0.01, 1),  # Just below threshold (edge case) -> fail
        (DEFAULT_THRESHOLD, 0),  # Exactly at threshold (edge case) -> pass
        (DEFAULT_THRESHOLD + 0.01, 0),  # Just above threshold (edge case) -> pass
        (0.85, 0),  # Well above threshold -> pass
    ],
)
def test_evaluate_gate_respects_roc_auc_threshold(
    tmp_path, monkeypatch, roc_auc, expected_exit_code
):
    """Verify evaluation gate behavior around the threshold using parametrization."""
    monkeypatch.setenv("MIN_ROC_AUC", str(DEFAULT_THRESHOLD))

    metrics_file = tmp_path / f"metrics_{roc_auc}.json"
    metrics_file.write_text(
        json.dumps({"roc_auc": roc_auc, "accuracy": 0.80})
    )

    assert evaluate_main([str(metrics_file)]) == expected_exit_code

