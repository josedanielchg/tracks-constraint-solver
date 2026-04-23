"""Helpers to solve one Tracks instance."""

from __future__ import annotations

from pathlib import Path

from tracks_solver.core import TracksInstance, TracksSolution, parse_tracks_instance

from .milp import solve_tracks_instance


def solve_tracks_file(
    path: str | Path,
    *,
    time_limit: float | None = None,
    msg: bool = False,
) -> tuple[TracksInstance, TracksSolution]:
    """Parse a Tracks instance file and solve it."""
    instance = parse_tracks_instance(path)
    solution = solve_tracks_instance(instance, time_limit=time_limit, msg=msg)
    return instance, solution
