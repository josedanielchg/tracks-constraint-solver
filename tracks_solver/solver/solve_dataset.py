"""Batch solving helpers for Tracks datasets."""

from __future__ import annotations

import csv
from pathlib import Path

from tracks_solver.core import parse_tracks_instance

from .milp import solve_tracks_instance


def solve_dataset(
    input_dir: str | Path,
    *,
    output_path: str | Path | None = None,
    time_limit: float | None = None,
    msg: bool = False,
) -> tuple[list[dict[str, object]], Path]:
    """Solve every ``.txt`` instance inside ``input_dir`` and write a CSV summary."""
    dataset_dir = Path(input_dir)
    instance_paths = sorted(dataset_dir.rglob("*.txt"))

    if output_path is None:
        output_path = Path("res") / "tracks" / "datasets" / f"{dataset_dir.name}_results.csv"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for instance_path in instance_paths:
        try:
            instance = parse_tracks_instance(instance_path)
            solution = solve_tracks_instance(instance, time_limit=time_limit, msg=msg)
            row = {
                "instance_name": instance_path.name,
                "rows": instance.rows,
                "cols": instance.cols,
                "num_cells": instance.rows * instance.cols,
                "num_used_cells": len(solution.used_cells),
                "status": solution.status,
                "is_feasible": solution.status in {"optimal", "feasible"},
                "solve_time": solution.solve_time,
                "objective_value": solution.objective_value,
                "validator_passed": solution.metadata.get("validation_passed", False),
                "error": "",
            }
        except Exception as exc:  # pragma: no cover - exercised in failure paths only
            row = {
                "instance_name": instance_path.name,
                "rows": "",
                "cols": "",
                "num_cells": "",
                "num_used_cells": "",
                "status": "error",
                "is_feasible": False,
                "solve_time": "",
                "objective_value": "",
                "validator_passed": False,
                "error": str(exc),
            }
        rows.append(row)

    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "instance_name",
                "rows",
                "cols",
                "num_cells",
                "num_used_cells",
                "status",
                "is_feasible",
                "solve_time",
                "objective_value",
                "validator_passed",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return rows, output_file
