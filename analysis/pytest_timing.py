"""Run the test suite several times and summarize the timings.

Usage:
    uv run python analysis/pytest_timing.py [RUNS] [TOP]

Example:
    uv run python analysis/pytest_timing.py 3 5
"""

import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def run_once(report: Path) -> tuple[float, dict[str, float]]:
    """Run pytest once. Return total wall time and time per test."""
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         f"--junitxml={report}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    total = time.perf_counter() - start

    if result.returncode != 0:
        sys.exit(f"ERROR: pytest failed (exit code {result.returncode}). Fix the tests first.")

    # JUnit XML stores the time for each test (setup + call + teardown).
    per_test = {
        f"{case.get('classname')}::{case.get('name')}": float(case.get("time", 0))
        for case in ET.parse(report).getroot().iter("testcase")
    }
    return total, per_test


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    totals: list[float] = []
    per_test: dict[str, list[float]] = {}

    with tempfile.TemporaryDirectory() as tmp:
        for i in range(1, runs + 1):
            total, times = run_once(Path(tmp) / f"run{i}.xml")
            totals.append(total)
            for name, seconds in times.items():
                per_test.setdefault(name, []).append(seconds)
            print(f"Run {i}/{runs}: {total:.1f} s")

    print(f"\nTotal: median {statistics.median(totals):.1f} s "
          f"(min {min(totals):.1f}, max {max(totals):.1f}) over {runs} runs")

    slowest = sorted(per_test.items(), key=lambda item: statistics.median(item[1]), reverse=True)
    suite_median = sum(statistics.median(t) for t in per_test.values())

    print(f"\nSlowest {top} tests (median):")
    print(f"{'seconds':>8} {'share':>6}  test")
    for name, times in slowest[:top]:
        median = statistics.median(times)
        print(f"{median:8.2f} {median / suite_median:6.0%}  {name}")


if __name__ == "__main__":
    main()
