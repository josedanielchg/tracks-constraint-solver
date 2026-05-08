"""Course-compatible workflow wrappers for the Tracks project.

The course statement uses Julia-style function names such as ``readInputFile``,
``cplexSolve`` and ``solveDataSet``.  This module keeps the existing Python
architecture intact while exposing equivalent entry points for the expected
project workflow.
"""

from __future__ import annotations

import argparse
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
from tracks_solver.solver import SolverUnavailableError, solve_tracks_instance


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


def _parse_sizes(raw_sizes: str) -> list[tuple[int, int]]:
    sizes: list[tuple[int, int]] = []
    for raw_size in raw_sizes.split(","):
        token = raw_size.strip().lower()
        if not token:
            continue
        if "x" not in token:
            raise argparse.ArgumentTypeError(
                f"Invalid size {raw_size!r}; expected a format such as 5x5."
            )
        raw_rows, raw_cols = token.split("x", 1)
        try:
            rows = int(raw_rows)
            cols = int(raw_cols)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid size {raw_size!r}; rows and columns must be integers."
            ) from exc
        if rows <= 0 or cols <= 0:
            raise argparse.ArgumentTypeError(
                f"Invalid size {raw_size!r}; rows and columns must be positive."
            )
        sizes.append((rows, cols))

    if not sizes:
        raise argparse.ArgumentTypeError("At least one size must be provided.")
    return sizes


def _cmd_generate_instance(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    instance = generate_instance(
        args.rows,
        args.cols,
        seed=args.seed,
        min_path_length=args.min_path_length,
        output_path=output_path,
    )
    print(f"instancePath = {output_path}")
    print(f"rows = {instance.rows}")
    print(f"cols = {instance.cols}")
    print(f"start = {instance.start}")
    print(f"end = {instance.end}")
    return 0


def _cmd_display_grid(args: argparse.Namespace) -> int:
    display_grid(args.instance)
    return 0


def _cmd_solve_instance(args: argparse.Namespace) -> int:
    try:
        is_optimal, solve_time, solution = milp_solve(
            args.instance,
            time_limit=args.time_limit,
            msg=args.solver_output,
        )
    except SolverUnavailableError as exc:
        print(str(exc))
        return 2

    print(f"isOptimal = {is_optimal}")
    print(f"solveTime = {solve_time}")
    print(f"status = {solution.status!r}")
    print(f"validationPassed = {solution.metadata.get('validation_passed', False)}")

    if args.display_solution:
        if solution.status in {"optimal", "feasible", "invalid"}:
            display_solution(args.instance, solution)
        else:
            display_grid(args.instance)

    return 0 if solution.status in {"optimal", "feasible"} else 1


def _cmd_open_ui(args: argparse.Namespace) -> int:
    try:
        _, _, solution = milp_solve(
            args.instance,
            time_limit=args.time_limit,
            msg=args.solver_output,
        )
    except SolverUnavailableError as exc:
        print(str(exc))
        return 2

    from tracks_solver.ui import TracksViewer

    shown_solution = solution if solution.status in {"optimal", "feasible", "invalid"} else None
    viewer = TracksViewer()
    viewer.run(read_input_file(args.instance), shown_solution)
    return 0


def _cmd_generate_dataset(args: argparse.Namespace) -> int:
    generated = generate_data_set(
        args.output_dir,
        sizes=args.sizes,
        count_per_size=args.count_per_size,
        seed=args.seed,
        force=args.force,
    )
    print(f"generatedCount = {len(generated)}")
    for path in generated:
        print(path)
    return 0


def _cmd_solve_dataset(args: argparse.Namespace) -> int:
    try:
        rows = solve_data_set(
            args.input_dir,
            result_dir=args.result_dir,
            csv_output=args.csv_output,
            time_limit=args.time_limit,
            msg=args.solver_output,
            force=args.force,
        )
    except SolverUnavailableError as exc:
        print(str(exc))
        return 2

    optimal_count = sum(bool(row.get("isOptimal", False)) for row in rows)
    print(f"instanceCount = {len(rows)}")
    print(f"optimalCount = {optimal_count}")
    print(f"resultDir = {Path(args.result_dir)}")
    if args.csv_output is not None:
        print(f"csvOutput = {Path(args.csv_output)}")
    return 0


def _cmd_results_table(args: argparse.Namespace) -> int:
    output_path = results_array(args.output, result_dir=args.result_dir)
    print(f"tablePath = {output_path}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the course-workflow command-line parser."""
    parser = argparse.ArgumentParser(
        description="Course-compatible Tracks workflow commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_instance_parser = subparsers.add_parser(
        "generate-instance",
        help="Create and save one generated Tracks instance.",
    )
    generate_instance_parser.add_argument("--rows", type=int, default=5)
    generate_instance_parser.add_argument("--cols", type=int, default=5)
    generate_instance_parser.add_argument("--seed", type=int, default=None)
    generate_instance_parser.add_argument("--min-path-length", type=int, default=None)
    generate_instance_parser.add_argument("--output", required=True)
    generate_instance_parser.set_defaults(func=_cmd_generate_instance)

    display_grid_parser = subparsers.add_parser(
        "display-grid",
        help="Print one unresolved instance in the terminal.",
    )
    display_grid_parser.add_argument("instance")
    display_grid_parser.set_defaults(func=_cmd_display_grid)

    solve_instance_parser = subparsers.add_parser(
        "solve-instance",
        help="Solve one instance with the exact MILP backend.",
    )
    solve_instance_parser.add_argument("instance")
    solve_instance_parser.add_argument("--time-limit", type=float, default=None)
    solve_instance_parser.add_argument("--solver-output", action="store_true")
    solve_instance_parser.add_argument("--display-solution", action="store_true")
    solve_instance_parser.set_defaults(func=_cmd_solve_instance)

    open_ui_parser = subparsers.add_parser(
        "open-ui",
        help="Solve one instance and open it in the Pygame viewer.",
        description="Solve one instance and open it in the Pygame viewer.",
    )
    open_ui_parser.add_argument("instance")
    open_ui_parser.add_argument("--time-limit", type=float, default=None)
    open_ui_parser.add_argument("--solver-output", action="store_true")
    open_ui_parser.set_defaults(func=_cmd_open_ui)

    generate_dataset_parser = subparsers.add_parser(
        "generate-dataset",
        help="Create several generated instances.",
    )
    generate_dataset_parser.add_argument("--output-dir", default=DEFAULT_DATASET_DIR)
    generate_dataset_parser.add_argument(
        "--sizes",
        type=_parse_sizes,
        default=_parse_sizes("4x4,5x5,6x6"),
        help="Comma-separated board sizes, for example 5x5,6x6,7x7.",
    )
    generate_dataset_parser.add_argument("--count-per-size", type=int, default=3)
    generate_dataset_parser.add_argument("--seed", type=int, default=0)
    generate_dataset_parser.add_argument("--force", action="store_true")
    generate_dataset_parser.set_defaults(func=_cmd_generate_dataset)

    solve_dataset_parser = subparsers.add_parser(
        "solve-dataset",
        help="Solve all .txt instances in a directory and write result files.",
    )
    solve_dataset_parser.add_argument("input_dir")
    solve_dataset_parser.add_argument("--result-dir", default=DEFAULT_RESULT_DIR)
    solve_dataset_parser.add_argument("--csv-output", default=None)
    solve_dataset_parser.add_argument("--time-limit", type=float, default=None)
    solve_dataset_parser.add_argument("--solver-output", action="store_true")
    solve_dataset_parser.add_argument("--force", action="store_true")
    solve_dataset_parser.set_defaults(func=_cmd_solve_dataset)

    results_table_parser = subparsers.add_parser(
        "results-table",
        help="Create a LaTeX table from course-style result files.",
    )
    results_table_parser.add_argument("--result-dir", default=DEFAULT_RESULT_DIR)
    results_table_parser.add_argument("--output", default=DEFAULT_RESULTS_TABLE)
    results_table_parser.set_defaults(func=_cmd_results_table)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the course-compatible command-line interface."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


readInputFile = read_input_file
displayGrid = display_grid
displaySolution = display_solution
cplexSolve = cplex_solve
generateInstance = generate_instance
generateDataSet = generate_data_set
solveDataSet = solve_data_set
resultsArray = results_array


__all__ = [
    "build_arg_parser",
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
    "main",
    "milp_solve",
    "readInputFile",
    "read_input_file",
    "resultsArray",
    "results_array",
    "solveDataSet",
    "solve_data_set",
]


if __name__ == "__main__":
    raise SystemExit(main())
