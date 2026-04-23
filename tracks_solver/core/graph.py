"""Grid graph helpers for Tracks."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Cell, Edge, TracksInstance, canonical_edge

Arc = tuple[Cell, Cell]


@dataclass(slots=True, frozen=True)
class GridGraph:
    """Deterministic graph view of a Tracks instance."""

    cells: tuple[Cell, ...]
    horizontal_edges: tuple[Edge, ...]
    vertical_edges: tuple[Edge, ...]
    edges: tuple[Edge, ...]
    neighbors: dict[Cell, tuple[Cell, ...]]
    incident_edges: dict[Cell, tuple[Edge, ...]]
    arcs: tuple[Arc, ...]


def build_grid_graph(instance: TracksInstance) -> GridGraph:
    """Build the grid graph structures used by the mathematical model."""
    cells = tuple(
        (row, col)
        for row in range(instance.rows)
        for col in range(instance.cols)
    )

    neighbors: dict[Cell, list[Cell]] = {cell: [] for cell in cells}
    incident_edges: dict[Cell, list[Edge]] = {cell: [] for cell in cells}

    horizontal_edges = tuple(
        canonical_edge((row, col), (row, col + 1))
        for row in range(instance.rows)
        for col in range(instance.cols - 1)
    )
    vertical_edges = tuple(
        canonical_edge((row, col), (row + 1, col))
        for row in range(instance.rows - 1)
        for col in range(instance.cols)
    )
    edges = horizontal_edges + vertical_edges

    for first, second in edges:
        neighbors[first].append(second)
        neighbors[second].append(first)
        incident_edges[first].append((first, second))
        incident_edges[second].append((first, second))

    normalized_neighbors = {
        cell: tuple(sorted(adjacent_cells))
        for cell, adjacent_cells in neighbors.items()
    }
    normalized_incident_edges = {
        cell: tuple(sorted(cell_edges))
        for cell, cell_edges in incident_edges.items()
    }
    arcs = tuple(
        arc
        for first, second in edges
        for arc in ((first, second), (second, first))
    )

    return GridGraph(
        cells=cells,
        horizontal_edges=horizontal_edges,
        vertical_edges=vertical_edges,
        edges=edges,
        neighbors=normalized_neighbors,
        incident_edges=normalized_incident_edges,
        arcs=arcs,
    )
