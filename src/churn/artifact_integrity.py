"""Verify the integrity of saved model artifacts."""

import hashlib
import sys
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def write_checksum(model_path: Path) -> Path:
    """Calculate and save a model's checksum."""
    checksum_path = Path(f"{model_path}.sha256")
    checksum = calculate_sha256(model_path)

    checksum_path.write_text(f"{checksum}\n", encoding="utf-8")

    return checksum_path


def verify_checksum(model_path: Path) -> None:
    """Raise an error if the model does not match its saved checksum."""
    checksum_path = Path(f"{model_path}.sha256")

    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not checksum_path.is_file():
        raise FileNotFoundError(
            f"Checksum file not found: {checksum_path}"
        )

    expected = checksum_path.read_text(encoding="utf-8").strip()
    actual = calculate_sha256(model_path)

    if actual != expected:
        raise ValueError(
            f"Model integrity check failed: {model_path}"
        )

    print(f"Model integrity verified: {model_path}")


def main() -> None:
    """Verify a model file supplied on the command line."""
    if len(sys.argv) != 2:
        print(
            "Usage: python -m churn.artifact_integrity MODEL_PATH",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        verify_checksum(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
