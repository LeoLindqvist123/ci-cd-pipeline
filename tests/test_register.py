"""Tests for model registration in the MLflow Model Registry."""

import json

import pytest

from churn.model import train_and_evaluate
from churn.register import main as register_main
from churn.tracking import REGISTERED_MODEL_NAME, log_training_run, register_model


@pytest.fixture
def tracking_uri(tmp_path, monkeypatch):
    """Point MLflow at a temporary SQLite database and run inside tmp_path."""
    pytest.importorskip("mlflow")
    monkeypatch.chdir(tmp_path)
    db_path = (tmp_path / "mlflow.db").as_posix()
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{db_path}")


def test_register_model_returns_none_when_tracking_is_disabled(monkeypatch):
    """Without MLFLOW_TRACKING_URI, nothing is registered and None is returned."""
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    result = register_model("any-run-id")

    assert result is None


def test_register_model_sets_champion_as_alias(tracking_uri):
    """A registered model gets a version, and the champion alias points to its run."""
    import mlflow

    model, metrics = train_and_evaluate()
    params = {"seed": 42}
    run_id = log_training_run(model, metrics, params)

    new_model_version = register_model(run_id)

    assert new_model_version == "1"
    champion = mlflow.MlflowClient().get_model_version_by_alias(
        REGISTERED_MODEL_NAME, "champion"
    )
    assert champion.run_id == run_id


def test_register_cli_fails_without_run_id(tmp_path):
    """The CLI exits with 1 if metrics.json has no mlflow_run_id."""
    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text(json.dumps({"roc_auc": 0.8}))

    exit_code = register_main([str(metrics_file)])

    assert exit_code == 1


def test_register_cli_fails_when_tracking_is_disabled(tmp_path, monkeypatch):
    """The CLI exits with 1 if it has a run id but tracking is disabled."""
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    metrics_file = tmp_path / "metrics.json"
    metrics_file.write_text(json.dumps({"mlflow_run_id": "any-run-id"}))

    exit_code = register_main([str(metrics_file)])

    assert exit_code == 1
