"""Tests for model artifact integrity verification."""

import pytest

from churn.artifact_integrity import (
    verify_checksum,
    write_checksum,
)


def test_valid_model_passes_verification(tmp_path):
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"example model content")

    checksum_path = write_checksum(model_path)

    assert checksum_path.exists()
    verify_checksum(model_path)


def test_modified_model_fails_verification(tmp_path):
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"original model content")

    write_checksum(model_path)

    # Simulate the model file being modified.
    model_path.write_bytes(b"modified model content")

    with pytest.raises(ValueError, match="integrity check failed"):
        verify_checksum(model_path)


def test_missing_model_fails_verification(tmp_path):
    model_path = tmp_path / "missing.joblib"

    with pytest.raises(FileNotFoundError, match="Model file not found"):
        verify_checksum(model_path)


def test_missing_checksum_fails_verification(tmp_path):
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"example model content")

    with pytest.raises(FileNotFoundError, match="Checksum file not found"):
        verify_checksum(model_path)
