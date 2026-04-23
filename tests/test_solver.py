"""Tests for the Tracks MILP solver."""

from __future__ import annotations

from pathlib import Path

from tracks_solver.core import parse_tracks_instance
from tracks_solver.solver import solve_tracks_instance

MANUAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tracks" / "manual"


def test_solver_finds_a_valid_solution_for_small_instance() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")

    solution = solve_tracks_instance(instance, msg=False)

    assert solution.status == "optimal"
    assert solution.metadata["validation_passed"] is True
    assert len(solution.used_cells) == sum(instance.row_clues)
    assert len(solution.selected_edges) == len(solution.used_cells) - 1


def test_solver_reports_infeasible_for_unsatisfiable_instance() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "unsat_2x2.txt")

    solution = solve_tracks_instance(instance, msg=False)

    assert solution.status == "infeasible"
    assert solution.used_cells == set()
    assert solution.selected_edges == set()
