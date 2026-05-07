"""Smoke entrypoint for verifying the initial project setup."""

from __future__ import annotations

import argparse
import importlib.util
import sys

import pygame

from tracks_solver.core import format_tracks_board, parse_tracks_instance
from tracks_solver.solver import SolverUnavailableError, solve_tracks_instance
from tracks_solver.ui import TracksGame, TracksViewer


def build_status_report() -> str:
    """Return a short setup report for the local environment."""
    pulp_available = importlib.util.find_spec("pulp") is not None
    return "\n".join(
        [
            "Tracks solver setup check",
            f"Python: {sys.version.split()[0]}",
            f"Pygame: {pygame.version.ver}",
            f"PuLP: {'available' if pulp_available else 'not installed'}",
            "Status: environment is ready.",
        ]
    )


def main(argv: list[str] | None = None) -> None:
    """Print the setup report or solve an instance from the command line."""
    parser = argparse.ArgumentParser(description="Tracks solver bootstrap entrypoint.")
    parser.add_argument("instance", nargs="?", help="Path to a Tracks instance file.")
    parser.add_argument("--ui", action="store_true", help="Open the Pygame viewer.")
    parser.add_argument("--play", action="store_true", help="Open the playable Pygame UI.")
    parser.add_argument(
        "--time-limit",
        type=float,
        default=None,
        help="Optional CBC time limit in seconds.",
    )
    parser.add_argument(
        "--solver-output",
        action="store_true",
        help="Show the MILP solver log in the terminal.",
    )
    args = parser.parse_args(argv)

    if args.play:
        game = TracksGame()
        if args.instance:
            game.start_board(parse_tracks_instance(args.instance))
        game.run()
        return

    if not args.instance:
        print(build_status_report())
        return

    instance = parse_tracks_instance(args.instance)
    print(build_status_report())

    try:
        solution = solve_tracks_instance(
            instance,
            time_limit=args.time_limit,
            msg=args.solver_output,
        )
    except SolverUnavailableError as exc:
        print(str(exc))
        return

    show_solution = solution.status in {"optimal", "feasible", "invalid"}
    print()
    print(format_tracks_board(instance, solution if show_solution else None))
    print()
    print(f"Solver status: {solution.status}")
    if show_solution:
        print(f"Validation passed: {solution.metadata.get('validation_passed', False)}")
        for error in solution.metadata.get("validation_errors", []):
            print(f"- {error}")

    if args.ui:
        viewer = TracksViewer()
        viewer.run(instance, solution if show_solution else None)


if __name__ == "__main__":
    main()
