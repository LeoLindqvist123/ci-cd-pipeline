import hashlib
import json

import numpy as np
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from churn.data import DATAKATALOG, FEATURES, dela_upp, las_data, skapa_features
from churn.evaluate import STANDARDTROSKEL
from churn.evaluate import main as evaluate_main
from churn.model import DATAFIL, SEED, trana_och_utvardera
from churn.model import main as train_main


@pytest.fixture(scope="module")
def resultat():
    return trana_och_utvardera()


def test_modellkontrakt(resultat):
    modell, _ = resultat
    X, _ = dela_upp(skapa_features(las_data().head(5)))
    assert list(X.columns) == FEATURES
    sannolikhet = modell.predict_proba(X)
    assert sannolikhet.shape == (5, 2)
    assert np.all((sannolikhet >= 0) & (sannolikhet <= 1))


def test_reproducerbar(resultat):
    _, matvarden = resultat
    _, igen = trana_och_utvardera()
    assert igen == matvarden


def test_roc_auc_meets_threshold(resultat):
    _, metrics = resultat
    assert metrics["roc_auc"] >= STANDARDTROSKEL


def test_slar_dummy(resultat):
    _, matvarden = resultat
    X, y = dela_upp(skapa_features(las_data()))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=SEED, stratify=y
    )
    dummy = DummyClassifier(strategy="prior").fit(X_train, y_train)
    dummy_auc = roc_auc_score(y_test, dummy.predict_proba(X_test)[:, 1])
    assert matvarden["roc_auc"] > dummy_auc


def test_model_versioning_metadata(tmp_path, monkeypatch):
    """Verify that model training saves versioned artifacts and full lineage metadata."""
    monkeypatch.setenv("GITHUB_SHA", "test-sha-12345")
    train_main(tmp_path)

    model_file = tmp_path / "modell.joblib"
    metrics_file = tmp_path / "matvarden.json"

    assert model_file.exists(), "Model artifact file was not created"
    assert metrics_file.exists(), "Metadata and metrics file was not created"

    expected_sha256 = hashlib.sha256((DATAKATALOG / DATAFIL).read_bytes()).hexdigest()

    metadata = json.loads(metrics_file.read_text())
    assert metadata["commit"] == "test-sha-12345"
    assert metadata["datafil"] == DATAFIL
    assert metadata["data_sha256"] == expected_sha256
    assert "roc_auc" in metadata
    assert "accuracy" in metadata


@pytest.mark.parametrize(
    ("roc_auc", "expected_exit_code"),
    [
        (0.50, 1),  # Well below threshold -> fail
        (STANDARDTROSKEL - 0.01, 1),  # Just below threshold (edge case) -> fail
        (STANDARDTROSKEL, 0),  # Exactly at threshold (edge case) -> pass
        (STANDARDTROSKEL + 0.01, 0),  # Just above threshold (edge case) -> pass
        (0.85, 0),  # Well above threshold -> pass
    ],
)
def test_evaluate_gate_blocks_low_roc_auc(tmp_path, roc_auc, expected_exit_code):
    """Verify evaluation gate behavior around the threshold using parametrization."""
    metrics_file = tmp_path / f"metrics_{roc_auc}.json"
    metrics_file.write_text(json.dumps({"roc_auc": roc_auc, "accuracy": 0.80}))
    assert evaluate_main([str(metrics_file)]) == expected_exit_code
