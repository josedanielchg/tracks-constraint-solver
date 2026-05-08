"""Collect generated-instance benchmark results for the English Tracks report."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tracks_solver.core import TracksInstance, parse_tracks_instance
from tracks_solver.generation import (
    difficulty_generation_params,
    generate_tracks_instance,
    save_tracks_instance,
)
from tracks_solver.solver import solve_tracks_instance

DEFAULT_OUTPUT = ROOT / "res" / "tracks" / "report" / "generated_benchmark_results.csv"
DEFAULT_INSTANCE_DIR = ROOT / "data" / "tracks" / "generated"
DEFAULT_SIZES = ",".join(f"{size}x{size}" for size in range(5, 17))
DEFAULT_DIFFICULTIES = "Easy,Medium,Hard"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Collect generated Tracks benchmark rows.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--instance-dir", type=Path, default=DEFAULT_INSTANCE_DIR)
    parser.add_argument("--sizes", default=DEFAULT_SIZES)
    parser.add_argument("--difficulties", default=DEFAULT_DIFFICULTIES)
    parser.add_argument("--attempts", type=int, default=10)
    parser.add_argument("--seed", type=int, default=203)
    parser.add_argument("--solve-time-limit", type=float, default=120.0)
    parser.add_argument("--max-generation-retries", type=int, default=50)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--solver-output", action="store_true")
    args = parser.parse_args(argv)

    instance_dir = absolute_path(args.instance_dir)
    instance_dir.mkdir(parents=True, exist_ok=True)

    output_path = absolute_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = result_fieldnames()

    written_count = 0
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        # The benchmark grid is size x difficulty x attempt.
        for rows_count, cols_count in parse_sizes(args.sizes):
            for difficulty in parse_difficulties(args.difficulties):
                for attempt in range(1, args.attempts + 1):
                    row = collect_one_row(
                        rows_count,
                        cols_count,
                        difficulty,
                        attempt,
                        args.seed,
                        instance_dir,
                        force=args.force,
                        solve_time_limit=args.solve_time_limit,
                        max_generation_retries=args.max_generation_retries,
                        solver_output=args.solver_output,
                    )
                    writer.writerow(row)
                    csv_file.flush()
                    written_count += 1
                    print(
                        f"{row['difficulty']} {row['size']} #{row['attempt']}: "
                        f"{row['status']} in {row['solve_time'] or '-'} s",
                        flush=True,
                    )

    print(f"Wrote {written_count} generated benchmark rows to {output_path}")


def collect_one_row(
    rows: int,
    cols: int,
    difficulty: str,
    attempt: int,
    base_seed: int,
    instance_dir: Path,
    *,
    force: bool,
    solve_time_limit: float,
    max_generation_retries: int,
    solver_output: bool,
) -> dict[str, object]:
    size = f"{rows}x{cols}"
    filename = f"{difficulty.lower()}_{size}_{attempt:02d}.txt"
    instance_path = instance_dir / filename
    seed = base_seed + rows * 100_000 + cols * 1_000 + difficulty_seed_offset(difficulty) + attempt

    generation_started = perf_counter()
    generation_status = "generated"
    generation_error = ""
    try:
        # Existing generated files can be reused to keep experiments reproducible.
        if instance_path.exists() and not force:
            instance = parse_tracks_instance(instance_path)
            generation_time = ""
            generation_status = "reused"
        else:
            instance = generate_with_retries(
                rows,
                cols,
                difficulty,
                seed,
                max_generation_retries=max_generation_retries,
            )
            generation_time = perf_counter() - generation_started
            save_tracks_instance(instance, instance_path)
    except Exception as exc:  # pragma: no cover - robustness path for long benchmark runs
        generation_time = perf_counter() - generation_started
        generation_status = "error"
        generation_error = str(exc)
        return base_row(
            instance_path,
            rows,
            cols,
            difficulty,
            attempt,
            seed,
            generation_time,
            generation_status,
            solve_time_limit,
            generation_error=generation_error,
        )

    row = base_row(
        instance_path,
        rows,
        cols,
        difficulty,
        attempt,
        seed,
        generation_time,
        generation_status,
        solve_time_limit,
    )
    row.update(instance_metadata(instance))

    try:
        # Every generated row is solved with the exact flow MILP.
        solution = solve_tracks_instance(instance, time_limit=solve_time_limit, msg=solver_output)
    except Exception as exc:  # pragma: no cover - robustness path for long benchmark runs
        row.update(
            {
                "used_cells": "",
                "status": "error",
                "is_feasible": False,
                "is_optimal": False,
                "validation_passed": False,
                "solve_time": "",
                "error": str(exc),
            }
        )
        return row

    row.update(
        {
            "used_cells": len(solution.used_cells),
            "status": solution.status,
            "is_feasible": solution.status in {"optimal", "feasible"},
            "is_optimal": solution.status == "optimal",
            "validation_passed": bool(solution.metadata.get("validation_passed", False)),
            "solve_time": solution.solve_time,
            "error": "",
        }
    )
    return row


def generate_with_retries(
    rows: int,
    cols: int,
    difficulty: str,
    seed: int,
    *,
    max_generation_retries: int,
) -> TracksInstance:
    params = difficulty_generation_params(rows, cols, difficulty)
    last_error: Exception | None = None
    # Some random seeds can fail, so the benchmark retries deterministically.
    for retry in range(max_generation_retries):
        try:
            return generate_tracks_instance(rows, cols, seed=seed + retry, **params)
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(
        f"could not generate {difficulty} {rows}x{cols} after {max_generation_retries} retries"
    ) from last_error


def base_row(
    instance_path: Path,
    rows: int,
    cols: int,
    difficulty: str,
    attempt: int,
    seed: int,
    generation_time: float | str,
    generation_status: str,
    time_limit: float,
    *,
    generation_error: str = "",
) -> dict[str, object]:
    return {
        "instance_name": instance_path.name,
        "instance_path": relative_path(instance_path),
        "difficulty": difficulty,
        "size": f"{rows}x{cols}",
        "attempt": attempt,
        "seed": seed,
        "rows": rows,
        "cols": cols,
        "num_cells": rows * cols,
        "generation_time": generation_time,
        "generation_status": generation_status,
        "generation_error": generation_error,
        "time_limit": time_limit,
        "row_clue_total": "",
        "fixed_used_count": "",
        "fixed_empty_count": "",
        "fixed_edge_count": "",
        "fixed_pattern_count": "",
        "used_cells": "",
        "status": "generation_error" if generation_status == "error" else "",
        "is_feasible": False,
        "is_optimal": False,
        "validation_passed": False,
        "solve_time": "",
        "error": generation_error,
    }


def instance_metadata(instance: TracksInstance) -> dict[str, object]:
    return {
        "row_clue_total": sum(instance.row_clues),
        "fixed_used_count": len(instance.fixed_used),
        "fixed_empty_count": len(instance.fixed_empty),
        "fixed_edge_count": len(instance.fixed_edges),
        "fixed_pattern_count": len(instance.fixed_patterns),
    }


def parse_sizes(raw_sizes: str) -> list[tuple[int, int]]:
    sizes: list[tuple[int, int]] = []
    for token in raw_sizes.split(","):
        raw_rows, raw_cols = token.strip().lower().split("x", 1)
        sizes.append((int(raw_rows), int(raw_cols)))
    return sizes


def parse_difficulties(raw_difficulties: str) -> list[str]:
    valid = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
    difficulties: list[str] = []
    for token in raw_difficulties.split(","):
        normalized = token.strip().lower()
        if normalized not in valid:
            raise ValueError("difficulties must be chosen from Easy, Medium, Hard")
        difficulties.append(valid[normalized])
    return difficulties


def difficulty_seed_offset(difficulty: str) -> int:
    return {"Easy": 10, "Medium": 20, "Hard": 30}[difficulty]


def absolute_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def result_fieldnames() -> list[str]:
    return [
        "instance_name",
        "instance_path",
        "difficulty",
        "size",
        "attempt",
        "seed",
        "rows",
        "cols",
        "num_cells",
        "generation_time",
        "generation_status",
        "generation_error",
        "time_limit",
        "row_clue_total",
        "fixed_used_count",
        "fixed_empty_count",
        "fixed_edge_count",
        "fixed_pattern_count",
        "used_cells",
        "status",
        "is_feasible",
        "is_optimal",
        "validation_passed",
        "solve_time",
        "error",
    ]


if __name__ == "__main__":
    main()
