"""Tests for the Tracks grid graph helpers."""

from __future__ import annotations

from tracks_solver.core import TracksInstance, build_grid_graph


def _make_instance(rows: int, cols: int) -> TracksInstance:
    row_clues = tuple(1 for _ in range(rows))
    col_clues = [0 for _ in range(cols)]
    for index in range(min(rows, cols)):
        col_clues[index] += 1

    return TracksInstance(
        rows=rows,
        cols=cols,
        start=(0, 0),
        end=(rows - 1, cols - 1),
        row_clues=row_clues,
        col_clues=tuple(col_clues),
    )


def test_build_graph_counts_for_2x2_grid() -> None:
    graph = build_grid_graph(_make_instance(2, 2))

    assert len(graph.cells) == 4
    assert len(graph.horizontal_edges) == 2
    assert len(graph.vertical_edges) == 2
    assert len(graph.edges) == 4
    assert len(graph.arcs) == 8


def test_build_graph_neighbor_counts_for_3x3_grid() -> None:
    graph = build_grid_graph(_make_instance(3, 3))

    assert len(graph.neighbors[(1, 1)]) == 4
    assert len(graph.neighbors[(0, 0)]) == 2
    assert len(graph.neighbors[(0, 1)]) == 3
    assert set(graph.neighbors[(1, 1)]) == {(0, 1), (1, 0), (1, 2), (2, 1)}


def test_build_graph_incident_edge_counts_match_cell_type() -> None:
    graph = build_grid_graph(_make_instance(3, 3))

    assert len(graph.incident_edges[(1, 1)]) == 4
    assert len(graph.incident_edges[(0, 0)]) == 2
    assert len(graph.incident_edges[(0, 1)]) == 3


def test_directed_arc_count_is_twice_the_edge_count() -> None:
    graph = build_grid_graph(_make_instance(4, 5))

    assert len(graph.arcs) == 2 * len(graph.edges)
