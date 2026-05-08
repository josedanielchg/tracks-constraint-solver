"""Shared helpers for Tracks report benchmark figures."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_CSV = ROOT / "res" / "tracks" / "report" / "generated_benchmark_results.csv"
IMAGE_DIR = ROOT / "report" / "sections" / "images"
DIFFICULTIES = ("Easy", "Medium", "Hard")
DIFFICULTY_COLORS = {
    "Easy": "#4C78A8",
    "Medium": "#F58518",
    "Hard": "#E45756",
}


def load_rows(path: str | Path = BENCHMARK_CSV) -> list[dict[str, str]]:
    """Load benchmark rows from CSV."""
    with Path(path).open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def as_float(value: object, default: float = 0.0) -> float:
    """Parse a numeric value exported by the benchmark collector."""
    if value in {None, ""}:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_true(value: object) -> bool:
    """Interpret CSV boolean values."""
    return str(value).strip().lower() in {"1", "true", "yes"}


def grouped(rows: Iterable[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    """Group CSV rows by one key."""
    output: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        output[row.get(key, "")].append(row)
    return dict(output)


def mean_solve_time(rows: Iterable[dict[str, str]]) -> float:
    """Return average solve time over rows with numeric solve times."""
    # Failed generations are excluded because they are not solver observations.
    values = [effective_solve_time(row) for row in rows if row.get("generation_status") != "error"]
    return mean(values) if values else 0.0


def effective_solve_time(row: dict[str, str]) -> float:
    """Return solve time, using the time limit for unsolved timeout-like rows."""
    solve_time = row.get("solve_time")
    if solve_time not in {None, ""}:
        return as_float(solve_time)
    return as_float(row.get("time_limit"))


def mean_numeric(rows: Iterable[dict[str, str]], key: str) -> float:
    """Return the mean of numeric values present for one CSV key."""
    values = [as_float(row.get(key)) for row in rows if row.get(key) not in {None, ""}]
    return mean(values) if values else 0.0


def benchmark_summary(rows: Iterable[dict[str, str]]) -> dict[str, object]:
    """Compute one aggregate summary over the generated benchmark CSV."""
    row_list = list(rows)
    # The summary is reused by the README, docs, and report text.
    valid_rows = [row for row in row_list if row.get("generation_status") != "error"]
    hard_rows = [row for row in valid_rows if row.get("difficulty") == "Hard"]

    summary: dict[str, object] = {
        "total_instances": len(row_list),
        "generated_instances": len(valid_rows),
        "solved_instances": sum(1 for row in valid_rows if is_true(row.get("is_optimal"))),
        "validated_instances": sum(1 for row in valid_rows if is_true(row.get("validation_passed"))),
        "average_solve_time_by_difficulty": {},
        "average_generation_time_by_difficulty": {},
        "hard_generation_min_ms": 0.0,
        "hard_generation_max_ms": 0.0,
    }

    for difficulty in DIFFICULTIES:
        difficulty_rows = [row for row in valid_rows if row.get("difficulty") == difficulty]
        summary["average_solve_time_by_difficulty"][difficulty] = mean_solve_time(difficulty_rows)
        summary["average_generation_time_by_difficulty"][difficulty] = (
            mean_numeric(difficulty_rows, "generation_time") * 1000.0
        )

    if hard_rows:
        hard_generation_times = [as_float(row.get("generation_time")) * 1000.0 for row in hard_rows]
        summary["hard_generation_min_ms"] = min(hard_generation_times)
        summary["hard_generation_max_ms"] = max(hard_generation_times)

    return summary


def configure_matplotlib() -> None:
    """Use a deterministic non-interactive plot style."""
    import matplotlib

    # Agg lets the scripts run without opening a GUI window.
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 160,
            "axes.edgecolor": "black",
            "axes.grid": True,
            "grid.alpha": 0.25,
            "font.size": 10,
        }
    )


def save_figure(fig, output_path: str | Path) -> Path:
    """Save one report figure and close it."""
    import matplotlib.pyplot as plt

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(target, bbox_inches="tight")
    plt.close(fig)
    return target
