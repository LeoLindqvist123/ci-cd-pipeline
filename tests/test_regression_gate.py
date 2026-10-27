"""Tests for the model regression gate."""

import json

from churn.regression_gate import main


def write_json(path, data):
    """Write test data to a JSON file."""
    path.write_text(json.dumps(data), encoding="utf-8")


def test_candidate_better_than_baseline_passes(tmp_path, capsys):
    metrics = tmp_path / "metrics.json"
    baseline = tmp_path / "baseline.json"

    write_json(metrics, {"roc_auc": 0.800})
    write_json(baseline, {"roc_auc": 0.789})

    result = main([str(metrics), str(baseline)])

    assert result == 0
    assert "passes the regression gate" in capsys.readouterr().out


def test_candidate_at_allowed_boundary_passes(tmp_path):
    metrics = tmp_path / "metrics.json"
    baseline = tmp_path / "baseline.json"

    write_json(metrics, {"roc_auc": 0.769})
    write_json(baseline, {"roc_auc": 0.789})

    assert main([str(metrics), str(baseline)]) == 0


def test_candidate_below_allowed_boundary_fails(tmp_path, capsys):
    metrics = tmp_path / "metrics.json"
    baseline = tmp_path / "baseline.json"

    write_json(metrics, {"roc_auc": 0.768})
    write_json(baseline, {"roc_auc": 0.789})

    result = main([str(metrics), str(baseline)])

    assert result == 1
    assert "exceeds the allowed drop" in capsys.readouterr().out


def test_missing_roc_auc_fails(tmp_path, capsys):
    metrics = tmp_path / "metrics.json"
    baseline = tmp_path / "baseline.json"

    write_json(metrics, {"accuracy": 0.90})
    write_json(baseline, {"roc_auc": 0.789})

    result = main([str(metrics), str(baseline)])

    assert result == 1
    assert "Invalid or missing ROC AUC" in capsys.readouterr().err


def test_missing_metrics_file_fails(tmp_path, capsys):
    metrics = tmp_path / "missing.json"
    baseline = tmp_path / "baseline.json"

    write_json(baseline, {"roc_auc": 0.789})

    result = main([str(metrics), str(baseline)])

    assert result == 1
    assert "Metrics file not found" in capsys.readouterr().err
