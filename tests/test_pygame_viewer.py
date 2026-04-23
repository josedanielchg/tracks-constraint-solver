"""Smoke test for the Pygame viewer."""

from __future__ import annotations

from pathlib import Path

import pygame

from tracks_solver.core import TracksSolution, canonical_edge, parse_tracks_instance
from tracks_solver.ui import TracksViewer

MANUAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tracks" / "manual"


def test_viewer_renders_one_frame_without_errors() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")
    solution = TracksSolution(
        used_cells={(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3)},
        selected_edges={
            canonical_edge((0, 0), (0, 1)),
            canonical_edge((0, 1), (0, 2)),
            canonical_edge((0, 2), (0, 3)),
            canonical_edge((0, 3), (1, 3)),
            canonical_edge((1, 3), (2, 3)),
            canonical_edge((2, 3), (3, 3)),
        },
        status="optimal",
    )
    viewer = TracksViewer(width=480, height=480)

    pygame.init()
    surface = viewer.render_to_surface(instance, solution)
    try:
        assert surface.get_width() == 480
        assert surface.get_height() == 480
    finally:
        pygame.quit()
