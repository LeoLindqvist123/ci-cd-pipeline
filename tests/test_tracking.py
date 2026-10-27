"""Testing tracking"""

import pytest

from churn.model import train_and_evaluate
from churn.tracking import log_training_run


@pytest.fixture(scope="module")
def results():
    return train_and_evaluate()


def test_tracking_disabled_returns_none(results, monkeypatch):
    """Without MLFLOW_TRACKING_URI, nothing is logged and None is returned."""
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    model, metrics = results
    params = {"seed": 42}

    result = log_training_run(model, metrics, params)

    assert result is None


def test_tracking_enabled_logs_run(results, tmp_path, monkeypatch):
    """With MLFLOW_TRACKING_URI set, a run is logged with tags, params and metrics."""
    mlflow = pytest.importorskip("mlflow")
    monkeypatch.chdir(tmp_path)
    db_path = (tmp_path / "mlflow.db").as_posix()
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{db_path}")

    model, metrics = results
    updated_metrics = {**metrics, "commit": "abc1234567"}
    params = {"seed": 42}

    run_id = log_training_run(model, updated_metrics, params)

    assert run_id is not None

    run = mlflow.MlflowClient().get_run(run_id)

    assert run.data.tags["commit"] == "abc1234567"
    assert run.data.params["seed"] == "42"
    assert run.data.metrics["roc_auc"] == pytest.approx(metrics["roc_auc"])
