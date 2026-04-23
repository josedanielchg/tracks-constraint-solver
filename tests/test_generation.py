"""Tests for Tracks instance generation."""

from __future__ import annotations

from tracks_solver.core import parse_tracks_instance_text
from tracks_solver.generation import (
    generate_random_path,
    generate_tracks_instance,
    serialize_tracks_instance,
)
from tracks_solver.solver import solve_tracks_instance


def test_generate_random_path_returns_a_simple_adjacent_path() -> None:
    path = generate_random_path(4, 4, seed=7, min_length=7)

    assert len(path) >= 7
    assert len(path) == len(set(path))
    assert path[0] == (0, 0)
    assert path[-1] == (3, 3)

    for first, second in zip(path, path[1:]):
        assert abs(first[0] - second[0]) + abs(first[1] - second[1]) == 1


def test_generated_instance_round_trips_through_the_parser() -> None:
    instance = generate_tracks_instance(4, 4, seed=11, min_path_length=7, fixed_used_hints=1)

    serialized = serialize_tracks_instance(instance)
    reparsed = parse_tracks_instance_text(serialized)

    assert reparsed == instance


def test_solver_can_solve_a_generated_instance() -> None:
    instance = generate_tracks_instance(4, 4, seed=13, min_path_length=7)

    solution = solve_tracks_instance(instance, msg=False)

    assert solution.status == "optimal"
    assert solution.metadata["validation_passed"] is True
