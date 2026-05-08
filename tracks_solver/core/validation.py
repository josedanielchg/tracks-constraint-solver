"""Validation helpers for candidate Tracks solutions."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .graph import build_grid_graph
from .models import (
    Cell,
    TracksInstance,
    TracksSolution,
    canonical_edge,
    local_pattern_token,
    pattern_implied_edges,
)


@dataclass(slots=True, frozen=True)
class ValidationResult:
    """Structured result for solution validation."""

    is_valid: bool
    errors: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        """Allow validation results to be used directly in conditions."""
        return self.is_valid


def validate_solution(instance: TracksInstance, solution: TracksSolution) -> ValidationResult:
    """Validate a candidate solution against the Tracks rules."""
    # The validator rebuilds the graph instead of trusting the solver output.
    graph = build_grid_graph(instance)
    known_cells = set(graph.cells)
    known_edges = set(graph.edges)

    used_cells = set(solution.used_cells)
    selected_edges = {canonical_edge(*edge) for edge in solution.selected_edges}
    errors: list[str] = []

    unknown_cells = sorted(used_cells - known_cells)
    if unknown_cells:
        errors.append(f"Unknown used cells: {unknown_cells}")

    unknown_edges = sorted(selected_edges - known_edges)
    if unknown_edges:
        errors.append(f"Unknown selected edges: {unknown_edges}")

    degrees = {cell: 0 for cell in graph.cells}
    adjacency = {cell: set() for cell in graph.cells}

    # Degrees and adjacency are reconstructed from the selected edges.
    for edge in selected_edges:
        if edge not in known_edges:
            continue

        first, second = edge
        if first not in used_cells or second not in used_cells:
            errors.append(f"Selected edge {edge} must connect two used cells")

        degrees[first] += 1
        degrees[second] += 1
        adjacency[first].add(second)
        adjacency[second].add(first)

    if instance.start not in used_cells:
        errors.append("The start terminal must be used")
    if instance.end not in used_cells:
        errors.append("The end terminal must be used")

    # Row and column clues count used cells, not edge segments.
    for row in range(instance.rows):
        used_in_row = sum((row, col) in used_cells for col in range(instance.cols))
        expected = instance.row_clues[row]
        if used_in_row != expected:
            errors.append(
                f"Row {row} uses {used_in_row} cells, but the clue requires {expected}"
            )

    for col in range(instance.cols):
        used_in_col = sum((row, col) in used_cells for row in range(instance.rows))
        expected = instance.col_clues[col]
        if used_in_col != expected:
            errors.append(
                f"Column {col} uses {used_in_col} cells, but the clue requires {expected}"
            )

    # Degree checks enforce the local path shape and reject branches.
    for cell in graph.cells:
        degree = degrees[cell]
        if cell == instance.start or cell == instance.end:
            expected_degree = 1
            if degree != expected_degree:
                errors.append(f"Terminal {cell} has degree {degree}, expected {expected_degree}")
            continue

        if cell in used_cells:
            if degree != 2:
                errors.append(f"Used cell {cell} has degree {degree}, expected 2")
        elif degree != 0:
            errors.append(f"Empty cell {cell} has degree {degree}, expected 0")

    for cell in sorted(instance.fixed_used):
        if cell not in used_cells:
            errors.append(f"Fixed used cell {cell} is missing from the solution")

    for cell in sorted(instance.fixed_empty):
        if cell in used_cells:
            errors.append(f"Fixed empty cell {cell} must not be used")

    for edge in sorted(instance.fixed_edges):
        if edge not in selected_edges:
            errors.append(f"Fixed edge {edge} is missing from the solution")

    for cell, pattern in instance.fixed_patterns.items():
        expected_edges = set(pattern_implied_edges(cell, pattern))
        actual_edges = {edge for edge in selected_edges if cell in edge}
        if actual_edges != expected_edges:
            errors.append(
                f"Fixed pattern {local_pattern_token(pattern)!r} at {cell} is violated; "
                f"expected incident edges {sorted(expected_edges)}, got {sorted(actual_edges)}"
            )

    # A BFS from the start detects disconnected loops or detached pieces.
    if instance.start in used_cells and instance.end in used_cells:
        visited = _reachable_used_cells(instance.start, adjacency, used_cells)
        if visited != used_cells:
            missing = sorted(used_cells - visited)
            errors.append(
                "Disconnected component or isolated loop detected; "
                f"unreachable used cells: {missing}"
            )

    # A simple path with k used cells must have exactly k - 1 selected edges.
    if used_cells and len(selected_edges) != len(used_cells) - 1:
        errors.append(
            "A valid single path must satisfy |selected_edges| = |used_cells| - 1, "
            f"but got {len(selected_edges)} edges and {len(used_cells)} used cells"
        )

    return ValidationResult(is_valid=not errors, errors=tuple(errors))


def assert_valid_solution(instance: TracksInstance, solution: TracksSolution) -> None:
    """Raise a ``ValueError`` if the candidate solution is invalid."""
    result = validate_solution(instance, solution)
    if not result.is_valid:
        raise ValueError("\n".join(result.errors))


def _reachable_used_cells(
    start: Cell,
    adjacency: dict[Cell, set[Cell]],
    used_cells: set[Cell],
) -> set[Cell]:
    """Return all used cells reachable from the start cell."""
    visited: set[Cell] = set()
    queue: deque[Cell] = deque([start])

    while queue:
        cell = queue.popleft()
        if cell in visited or cell not in used_cells:
            continue
        visited.add(cell)
        for neighbor in adjacency[cell]:
            if neighbor not in visited:
                queue.append(neighbor)

    return visited
