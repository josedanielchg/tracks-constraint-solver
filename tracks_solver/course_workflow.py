"""Course-compatible workflow wrappers for the Tracks project.

The course statement uses Julia-style function names such as ``readInputFile``,
``cplexSolve`` and ``solveDataSet``.  This module keeps the existing Python
architecture intact while exposing equivalent entry points for the expected
project workflow.
"""

from __future__ import annotations

import csv
from ast import literal_eval
from pathlib import Path
from typing import Iterable

from tracks_solver.core import (
    TracksInstance,
    TracksSolution,
    format_tracks_board,
    parse_tracks_instance,
)
from tracks_solver.generation import generate_tracks_instance, save_tracks_instance
from tracks_solver.solver import solve_tracks_instance


DEFAULT_INSTANCE_PATH = Path("data") / "tracks" / "manual" / "instanceTest.txt"
DEFAULT_DATASET_DIR = Path("data") / "tracks" / "generated"
DEFAULT_RESULT_DIR = Path("res") / "tracks" / "cbc"
DEFAULT_RESULTS_TABLE = Path("res") / "tracks" / "array.tex"


def read_input_file(path: str | Path = DEFAULT_INSTANCE_PATH) -> TracksInstance:
    """Read one Tracks instance from ``path``."""
    return parse_tracks_instance(path)


def display_grid(instance: TracksInstance | str | Path) -> str:
    """Print and return an ASCII display of an unresolved Tracks instance."""
    normalized_instance = _ensure_instance(instance)
    rendered = format_tracks_board(normalized_instance)
    print(rendered)
    return rendered


def display_solution(
    instance: TracksInstance | str | Path,
    solution: TracksSolution,
) -> str:
    """Print and return an ASCII display of a solved Tracks instance."""
    normalized_instance = _ensure_instance(instance)
    rendered = format_tracks_board(normalized_instance, solution)
    print(rendered)
    return rendered


def milp_solve(
    instance: TracksInstance | str | Path,
    *,
    time_limit: float | None = None,
    msg: bool = False,
) -> tuple[bool, float, TracksSolution]:
    """Solve one instance with the exact MILP backend.

    Returns the same information expected by the course example: whether an
    optimal feasible solution was obtained, the solving time, and the solution
    object itself.
    """
    normalized_instance = _ensure_instance(instance)
    solution = solve_tracks_instance(normalized_instance, time_limit=time_limit, msg=msg)
    is_optimal = solution.status == "optimal"
    return is_optimal, solution.solve_time, solution


def cplex_solve(
    instance: TracksInstance | str | Path,
    *,
    time_limit: float | None = None,
    msg: bool = False,
) -> tuple[bool, float, TracksSolution]:
    """Course-name equivalent of ``milp_solve``.

    The implementation uses PuLP/CBC instead of CPLEX, but the returned values
    follow the same role as the course's ``cplexSolve`` function.
    """
    return milp_solve(instance, time_limit=time_limit, msg=msg)


def generate_instance(
    rows: int = 4,
    cols: int = 4,
    *,
    seed: int | None = None,
    min_path_length: int | None = None,
    output_path: str | Path | None = None,
) -> TracksInstance:
    """Generate one random feasible Tracks instance and optionally save it."""
    instance = generate_tracks_instance(
        rows,
        cols,
        seed=seed,
        min_path_length=min_path_length,
    )
    if output_path is not None:
        save_tracks_instance(instance, output_path)
    return instance


def generate_data_set(
    output_dir: str | Path = DEFAULT_DATASET_DIR,
    *,
    sizes: Iterable[tuple[int, int]] = ((4, 4), (5, 5), (6, 6)),
    count_per_size: int = 3,
    seed: int = 0,
    force: bool = False,
) -> list[Path]:
    """Generate a course-style dataset in ``output_dir``."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    serial = 1
    for rows, cols in sizes:
        for instance_id in range(1, count_per_size + 1):
            path = target_dir / f"instance_t{rows}x{cols}_{instance_id}.txt"
            if path.exists() and not force:
                written.append(path)
                serial += 1
                continue
            instance = generate_instance(
                rows,
                cols,
                seed=seed + serial,
                min_path_length=rows + cols - 1,
            )
            written.append(save_tracks_instance(instance, path))
            serial += 1

    return written


def solve_data_set(
    input_dir: str | Path = DEFAULT_DATASET_DIR,
    *,
    result_dir: str | Path = DEFAULT_RESULT_DIR,
    csv_output: str | Path | None = None,
    time_limit: float | None = None,
    msg: bool = False,
    force: bool = False,
) -> list[dict[str, object]]:
    """Solve all ``.txt`` instances in ``input_dir`` and write course-style results."""
    source_dir = Path(input_dir)
    output_dir = Path(result_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    instance_paths = sorted(source_dir.rglob("*.txt"))
    rows: list[dict[str, object]] = []

    for instance_path in instance_paths:
        output_path = output_dir / instance_path.name
        if output_path.exists() and not force:
            row = _read_result_file(output_path)
            row["instance_name"] = instance_path.name
            rows.append(row)
            continue

        instance = read_input_file(instance_path)
        is_optimal, solve_time, solution = milp_solve(
            instance,
            time_limit=time_limit,
            msg=msg,
        )
        row = {
            "instance_name": instance_path.name,
            "rows": instance.rows,
            "cols": instance.cols,
            "solveTime": solve_time,
            "isOptimal": is_optimal,
            "status": solution.status,
            "numUsedCells": len(solution.used_cells),
            "validationPassed": solution.metadata.get("validation_passed", False),
        }
        _write_result_file(output_path, row, solution)
        rows.append(row)

    if csv_output is not None:
        _write_csv_summary(csv_output, rows)

    return rows


def results_array(
    output_file: str | Path = DEFAULT_RESULTS_TABLE,
    *,
    result_dir: str | Path = DEFAULT_RESULT_DIR,
) -> Path:
    """Create a small LaTeX table summarizing result files."""
    source_dir = Path(result_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for result_path in sorted(source_dir.glob("*.txt")):
        row = _read_result_file(result_path)
        row["instance_name"] = result_path.name
        rows.append(row)

    lines = [
        r"\documentclass{article}",
        r"\usepackage{booktabs}",
        r"\usepackage[margin=2cm]{geometry}",
        r"\begin{document}",
        r"\begin{center}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"\textbf{Instance} & \textbf{Rows} & \textbf{Cols} & \textbf{Time (s)} & \textbf{Optimal?} \\",
        r"\midrule",
    ]

    for row in rows:
        instance_name = str(row.get("instance_name", "")).replace("_", r"\_")
        solve_time = _format_float(row.get("solveTime", ""))
        optimal = r"$\times$" if bool(row.get("isOptimal", False)) else "-"
        lines.append(
            f"{instance_name} & {row.get('rows', '-')} & {row.get('cols', '-')} "
            f"& {solve_time} & {optimal} \\\\"
        )

    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{center}",
            r"\end{document}",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _ensure_instance(instance: TracksInstance | str | Path) -> TracksInstance:
    if isinstance(instance, TracksInstance):
        return instance
    return read_input_file(instance)


def _write_result_file(path: Path, row: dict[str, object], solution: TracksSolution) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used_cells = sorted(solution.used_cells)
    selected_edges = sorted(solution.selected_edges)
    lines = [
        f"solveTime = {row['solveTime']}",
        f"isOptimal = {row['isOptimal']}",
        f"status = {row['status']!r}",
        f"rows = {row['rows']}",
        f"cols = {row['cols']}",
        f"numUsedCells = {row['numUsedCells']}",
        f"validationPassed = {row['validationPassed']}",
        f"usedCells = {used_cells!r}",
        f"selectedEdges = {selected_edges!r}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _read_result_file(path: Path) -> dict[str, object]:
    row: dict[str, object] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line:
            continue
        key, value = (part.strip() for part in raw_line.split("=", 1))
        try:
            row[key] = literal_eval(value)
        except (ValueError, SyntaxError):
            row[key] = value
    return row


def _write_csv_summary(path: str | Path, rows: list[dict[str, object]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "instance_name",
        "rows",
        "cols",
        "solveTime",
        "isOptimal",
        "status",
        "numUsedCells",
        "validationPassed",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _format_float(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.3f}"
    return str(value)


readInputFile = read_input_file
displayGrid = display_grid
displaySolution = display_solution
cplexSolve = cplex_solve
generateInstance = generate_instance
generateDataSet = generate_data_set
solveDataSet = solve_data_set
resultsArray = results_array


__all__ = [
    "cplexSolve",
    "cplex_solve",
    "displayGrid",
    "displaySolution",
    "display_grid",
    "display_solution",
    "generateDataSet",
    "generateInstance",
    "generate_data_set",
    "generate_instance",
    "milp_solve",
    "readInputFile",
    "read_input_file",
    "resultsArray",
    "results_array",
    "solveDataSet",
    "solve_data_set",
]
