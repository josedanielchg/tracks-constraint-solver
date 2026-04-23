"""Tests for Tracks solution validation."""

from __future__ import annotations

from pathlib import Path

from tracks_solver.core import TracksSolution, canonical_edge, parse_tracks_instance, validate_solution

MANUAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tracks" / "manual"


def _solution_from_path(path: list[tuple[int, int]]) -> TracksSolution:
    return TracksSolution(
        used_cells=set(path),
        selected_edges={canonical_edge(first, second) for first, second in zip(path, path[1:])},
        status="optimal",
    )


def test_validator_accepts_a_valid_solution() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")
    solution = _solution_from_path(
        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
    )

    result = validate_solution(instance, solution)

    assert result.is_valid
    assert result.errors == ()


def test_validator_rejects_a_disconnected_solution() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")
    solution = TracksSolution(
        used_cells={(0, 0), (0, 1), (0, 2), (0, 3), (2, 3), (3, 3)},
        selected_edges={
            canonical_edge((0, 0), (0, 1)),
            canonical_edge((0, 1), (0, 2)),
            canonical_edge((0, 2), (0, 3)),
            canonical_edge((2, 3), (3, 3)),
        },
        status="optimal",
    )

    result = validate_solution(instance, solution)

    assert not result.is_valid
    assert any("Disconnected component or isolated loop detected" in error for error in result.errors)


def test_validator_rejects_a_branching_solution() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")
    solution = TracksSolution(
        used_cells={(0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 3), (3, 3)},
        selected_edges={
            canonical_edge((0, 0), (0, 1)),
            canonical_edge((0, 1), (0, 2)),
            canonical_edge((0, 2), (0, 3)),
            canonical_edge((0, 1), (1, 1)),
            canonical_edge((0, 3), (1, 3)),
            canonical_edge((1, 3), (2, 3)),
            canonical_edge((2, 3), (3, 3)),
        },
        status="optimal",
    )

    result = validate_solution(instance, solution)

    assert not result.is_valid
    assert any("degree 3" in error for error in result.errors)


def test_validator_rejects_wrong_row_counts() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")
    solution = _solution_from_path([(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3)])

    result = validate_solution(instance, solution)

    assert not result.is_valid
    assert any("Row 3 uses 0 cells" in error for error in result.errors)


def test_validator_rejects_wrong_column_counts() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_5x5.txt")
    solution = _solution_from_path(
        [(4, 0), (3, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 3), (0, 4)]
    )
    solution.used_cells.add((4, 1))
    solution.selected_edges.add(canonical_edge((4, 0), (4, 1)))

    result = validate_solution(instance, solution)

    assert not result.is_valid
    assert any("Column 1 uses 2 cells" in error for error in result.errors)


def test_validator_rejects_fixed_information_violations() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_5x5.txt")
    solution = _solution_from_path(
        [(4, 0), (3, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 3), (0, 4)]
    )
    solution.selected_edges.remove(canonical_edge((2, 0), (2, 1)))

    result = validate_solution(instance, solution)

    assert not result.is_valid
    assert any("Fixed edge ((2, 0), (2, 1)) is missing" in error for error in result.errors)
