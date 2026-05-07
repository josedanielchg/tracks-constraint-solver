"""Smoke test for the Pygame viewer."""

from __future__ import annotations

from pathlib import Path

import pygame

from tracks_solver.core import TracksInstance, TracksSolution, canonical_edge, parse_tracks_instance
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


def test_viewer_shades_fixed_cells_with_darker_background() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_5x5.txt")
    viewer = TracksViewer(width=480, height=480)

    pygame.init()
    surface = viewer.render_to_surface(instance)
    try:
        layout = viewer._build_layout(instance)
        fixed_cell_center = viewer._cell_center((2, 1), layout)
        free_cell_center = viewer._cell_center((2, 2), layout)

        assert surface.get_at(fixed_cell_center)[:3] == viewer.fixed_cell_color
        assert surface.get_at(free_cell_center)[:3] == viewer.background_color
    finally:
        pygame.quit()


def test_viewer_uses_different_backgrounds_for_fixed_used_and_patterns() -> None:
    instance = TracksInstance(
        rows=3,
        cols=4,
        start=(0, 0),
        end=(2, 3),
        row_clues=(1, 2, 1),
        col_clues=(1, 1, 1, 1),
        fixed_used=frozenset({(1, 1)}),
        fixed_patterns={(1, 2): ("L", "R")},
    )
    viewer = TracksViewer(width=480, height=480)

    pygame.init()
    surface = viewer.render_to_surface(instance)
    try:
        layout = viewer._build_layout(instance)
        used_cell_center = viewer._cell_center((1, 1), layout)
        pattern_cell_center = viewer._cell_center((1, 2), layout)

        assert surface.get_at(used_cell_center)[:3] == viewer.fixed_used_cell_color
        assert surface.get_at(pattern_cell_center)[:3] == viewer.fixed_pattern_cell_color
        assert viewer.fixed_pattern_cell_color != viewer.fixed_used_cell_color
    finally:
        pygame.quit()
