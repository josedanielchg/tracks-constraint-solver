"""Tests for the playable Pygame Tracks UI helpers."""

from __future__ import annotations

import pygame

from tracks_solver.core import TracksInstance, canonical_edge
from tracks_solver.ui import PlayerBoardState, TracksGame
from tracks_solver.ui.pygame_game import LEGEND_ENTRIES, allowed_patterns_for_cell


def _base_instance(**kwargs) -> TracksInstance:
    defaults = {
        "rows": 3,
        "cols": 3,
        "start": (0, 0),
        "end": (2, 2),
        "row_clues": (1, 1, 1),
        "col_clues": (1, 1, 1),
    }
    defaults.update(kwargs)
    return TracksInstance(**defaults)


def test_player_can_cycle_regular_cell_patterns() -> None:
    instance = _base_instance()
    state = PlayerBoardState.from_instance(instance)

    assert (1, 1) not in state.patterns

    state.cycle_cell((1, 1))

    assert state.patterns[(1, 1)] in allowed_patterns_for_cell(instance, (1, 1))


def test_fixed_empty_cell_cannot_be_changed() -> None:
    instance = _base_instance(fixed_empty=frozenset({(1, 1)}))
    state = PlayerBoardState.from_instance(instance)

    state.cycle_cell((1, 1))

    assert (1, 1) not in state.patterns


def test_fixed_pattern_cell_is_locked() -> None:
    instance = _base_instance(
        row_clues=(1, 2, 1),
        col_clues=(1, 1, 2),
        fixed_patterns={(1, 1): ("L", "R")},
    )
    state = PlayerBoardState.from_instance(instance)

    state.cycle_cell((1, 1))
    state.clear_cell((1, 1))

    assert state.patterns[(1, 1)] == ("L", "R")


def test_fixed_used_cell_cannot_be_cleared() -> None:
    instance = _base_instance(
        row_clues=(1, 2, 1),
        col_clues=(1, 2, 1),
        fixed_used=frozenset({(1, 1)}),
    )
    state = PlayerBoardState.from_instance(instance)

    state.clear_cell((1, 1))

    assert state.patterns[(1, 1)]


def test_fixed_edge_cell_keeps_required_connection() -> None:
    fixed_edge = canonical_edge((1, 1), (1, 2))
    instance = _base_instance(
        row_clues=(1, 2, 1),
        col_clues=(1, 1, 2),
        fixed_edges=frozenset({fixed_edge}),
    )
    state = PlayerBoardState.from_instance(instance)

    for _ in range(5):
        state.cycle_cell((1, 1))
        state.cycle_cell((1, 2))

    assert fixed_edge in state.to_solution().selected_edges


def test_player_patterns_convert_to_solution_edges() -> None:
    instance = _base_instance(row_clues=(3, 0, 0), col_clues=(1, 1, 1), end=(0, 2))
    state = PlayerBoardState(
        instance=instance,
        patterns={
            (0, 0): ("R",),
            (0, 1): ("L", "R"),
            (0, 2): ("L",),
        },
    )

    solution = state.to_solution()

    assert solution.used_cells == {(0, 0), (0, 1), (0, 2)}
    assert solution.selected_edges == {
        canonical_edge((0, 0), (0, 1)),
        canonical_edge((0, 1), (0, 2)),
    }


def test_one_sided_player_patterns_do_not_create_connections() -> None:
    instance = _base_instance(row_clues=(0, 2, 1), col_clues=(1, 1, 1))
    state = PlayerBoardState(
        instance=instance,
        patterns={
            (1, 0): ("R",),
            (1, 1): ("U", "D"),
        },
    )

    solution = state.to_solution()

    assert solution.used_cells == {(1, 0), (1, 1)}
    assert canonical_edge((1, 0), (1, 1)) not in solution.selected_edges
    assert solution.selected_edges == set()


def test_legend_entries_are_human_readable() -> None:
    labels = [label for label, _, _ in LEGEND_ENTRIES]
    descriptions = [description for _, description, _ in LEGEND_ENTRIES]

    assert labels == ["Required cell", "Fixed connection", "Fixed shape", "Blocked cell"]
    assert all("_" not in label for label in labels)
    assert any("rotated" in description for description in descriptions)
    assert any("clicked" in description for description in descriptions)


def test_playable_home_screen_renders_without_errors() -> None:
    game = TracksGame(width=900, height=700)

    pygame.init()
    try:
        surface = game.render_to_surface()
        assert surface.get_width() == 900
        assert surface.get_height() == 700
        assert game.buttons
    finally:
        pygame.quit()


def test_home_screen_uses_centered_black_bordered_panels() -> None:
    game = TracksGame(width=900, height=700)

    pygame.init()
    try:
        surface = game.render_to_surface()
        new_game_panel, load_map_panel = game._home_panel_rects()

        assert new_game_panel.centerx == game.width // 2
        assert load_map_panel.centerx == game.width // 2
        assert load_map_panel.y > new_game_panel.bottom
        assert surface.get_at(new_game_panel.topleft)[:3] == (0, 0, 0)
        assert surface.get_at(load_map_panel.topleft)[:3] == (0, 0, 0)
    finally:
        pygame.quit()


def test_playable_board_renders_legend_and_fixed_empty_black() -> None:
    instance = _base_instance(fixed_empty=frozenset({(1, 1)}))
    game = TracksGame(width=900, height=700)
    game.start_board(instance)

    pygame.init()
    try:
        surface = game.render_to_surface()
        layout = game.viewer._build_layout(instance)
        fixed_empty_center = game.viewer._cell_center((1, 1), layout)

        assert surface.get_at(fixed_empty_center)[:3] == game.viewer.fixed_empty_cell_color
        assert game.viewer.fixed_empty_cell_color == (0, 0, 0)
        assert any(button.label == "Show Solution" for button in game.buttons)
    finally:
        pygame.quit()


def test_clicking_regular_cell_changes_player_state() -> None:
    instance = _base_instance()
    game = TracksGame(width=900, height=700)
    game.start_board(instance)

    pygame.init()
    try:
        game.render_to_surface()
        layout = game.viewer._build_layout(instance)
        click_position = game.viewer._cell_center((1, 1), layout)

        assert game.player_state is not None
        assert (1, 1) not in game.player_state.patterns

        game.handle_mouse(click_position, 1)

        assert (1, 1) in game.player_state.patterns
    finally:
        pygame.quit()
