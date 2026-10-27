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


def test_tracking_enabled_logs_run():
    pass
