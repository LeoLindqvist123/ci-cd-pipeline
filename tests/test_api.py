
from unittest.mock import Mock

import numpy as np
import pytest
from fastapi.testclient import TestClient

from churn import api
from churn.artifact_integrity import write_checksum
from churn.data import FEATURES

client = TestClient(api.app)


class FakeModel:
    """A simple fake model for testing the API."""

    def predict(self, features):
        assert list(features.columns) == list(FEATURES)
        return [1]

    def predict_proba(self, features):
        assert list(features.columns) == list(FEATURES)
        return np.array([[0.2, 0.8]])


@pytest.fixture(autouse=True)
def reset_model(monkeypatch):
    """Reset the model before each test."""
    monkeypatch.setattr(api, "_model", None)


def test_health_returns_ok_when_model_is_loaded(monkeypatch):
    monkeypatch.setattr(api, "_model", FakeModel())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": True,
    }


def test_health_returns_503_when_model_is_missing(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        api, "MODEL_PATH", tmp_path / "missing-model.joblib"
    )

    response = client.get("/health")

    assert response.status_code == 503


def test_predict_returns_prediction_and_probability(monkeypatch):
    monkeypatch.setattr(api, "_model", FakeModel())

    response = client.post(
        "/predict",
        json={
            "age": 35,
            "months_as_customer": 34,
            "monthly_cost": 340.29,
            "data_gb_per_month": 15.8,
            "support_tickets_12m": 2,
            "region": "Väst",
            "subscription": "Standard",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "prediction": 1,
        "churn_probability": 0.8,
    }


def test_predict_rejects_invalid_age(monkeypatch):
    monkeypatch.setattr(api, "_model", FakeModel())

    response = client.post(
        "/predict",
        json={
            "age": 101,
            "months_as_customer": 34,
            "monthly_cost": 340.29,
            "data_gb_per_month": 15.8,
            "support_tickets_12m": 2,
            "region": "Väst",
            "subscription": "Standard",
        },
    )

    assert response.status_code == 422

def test_predict_maps_api_fields_to_training_columns(monkeypatch):
    captured = {}

    class CapturingModel:
        def predict(self, features):
            captured["features"] = features.copy()
            return [1]

        def predict_proba(self, features):
            captured["features"] = features.copy()
            return np.array([[0.2, 0.8]])

    monkeypatch.setattr(api, "_model", CapturingModel())

    response = client.post(
        "/predict",
        json={
            "age": 35,
            "months_as_customer": 18,
            "monthly_cost": 249.0,
            "data_gb_per_month": 7.5,
            "support_tickets_12m": 4,
            "region": "Väst",
            "subscription": "Standard",
        },
    )

    assert response.status_code == 200

    mapped = captured["features"].iloc[0]

    assert mapped["alder"] == 35
    assert mapped["manader_som_kund"] == 18
    assert mapped["manadskostnad"] == 249.0
    assert mapped["data_gb_per_manad"] == 7.5
    assert mapped["supportarenden_12m"] == 4
    assert mapped["region"] == "Väst"
    assert mapped["abonnemang"] == "Standard"

def test_health_returns_503_when_model_checksum_is_invalid(
    monkeypatch, tmp_path, caplog
):
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"original model")

    write_checksum(model_path)

    # Simulate corruption after the checksum was created.
    model_path.write_bytes(b"modified model")

    monkeypatch.setattr(api, "MODEL_PATH", model_path)
    monkeypatch.setattr(api, "_model", None)

    # Track whether the API attempts to load the corrupted model.
    load_mock = Mock()
    monkeypatch.setattr(api.joblib, "load", load_mock)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The trained model could not be loaded."
    )

    # Integrity verification must fail before joblib.load() is called.
    load_mock.assert_not_called()
    assert "Could not load model from" in caplog.text
