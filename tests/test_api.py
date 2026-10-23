
import numpy as np
import pytest
from fastapi.testclient import TestClient

from churn import api
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
