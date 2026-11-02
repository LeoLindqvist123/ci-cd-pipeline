"""Tests for the optional MLflow tracking module."""

from importlib.metadata import version

import pytest

from churn.model import train_and_evaluate
from churn.tracking import MODEL_PACKAGES, log_training_run, model_requirements


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

    # The logged model uses our explicit requirements instead of inferred ones.
    requirements_file = mlflow.pyfunc.get_model_dependencies(f"runs:/{run_id}/model")
    with open(requirements_file, encoding="utf-8") as file:
        logged = {line.strip() for line in file if line.strip()}

    assert set(model_requirements()) <= logged

def test_model_requirements_pin_installed_versions():
    """Each model package is pinned to the version installed in this environment."""
    expected = [f"{name}=={version(name)}" for name in MODEL_PACKAGES]

    assert model_requirements() == expected


def test_model_requirements_include_packages_needed_to_load_model():
    """The model cannot be loaded without these packages."""
    names = {requirement.split("==")[0] for requirement in model_requirements()}

    assert {"scikit-learn", "skops"} <= names
