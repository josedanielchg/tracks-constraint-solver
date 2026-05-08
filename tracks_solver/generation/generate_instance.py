"""Generate valid Tracks instances from random simple paths."""

from __future__ import annotations

import random
from pathlib import Path

from tracks_solver.core import (
    TracksInstance,
    are_orthogonally_adjacent,
    canonical_edge,
    cell_in_bounds,
    local_pattern_token,
)


def generate_random_path(
    rows: int,
    cols: int,
    *,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
    seed: int | None = None,
    min_length: int | None = None,
    max_attempts: int = 200,
) -> list[tuple[int, int]]:
    """Generate a random simple path that can become a solvable instance."""
    rng = random.Random(seed)
    # By default, generated boards connect the top-left and bottom-right cells.
    start = start or (0, 0)
    end = end or (rows - 1, cols - 1)

    if not cell_in_bounds(start, rows, cols):
        raise ValueError("start cell must lie inside the grid")
    if not cell_in_bounds(end, rows, cols):
        raise ValueError("end cell must lie inside the grid")
    if start == end:
        raise ValueError("start and end cells must be different")

    shortest_possible = abs(start[0] - end[0]) + abs(start[1] - end[1]) + 1
    min_length = min_length or shortest_possible
    if min_length > rows * cols:
        raise ValueError("min_length cannot exceed the number of cells in the grid")

    # Short paths can be generated directly as randomized Manhattan routes.
    if min_length == shortest_possible:
        return _generate_manhattan_path(start, end, rng)

    # Long corner-to-corner paths are easier to build with a serpentine shape.
    if start == (0, 0) and end == (rows - 1, cols - 1) and min_length > shortest_possible:
        return _generate_serpentine_path(rows, cols, rng, min_length)

    def neighbor_cells(cell: tuple[int, int]) -> list[tuple[int, int]]:
        """Return candidate neighbor cells inside the grid."""
        row, col = cell
        candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        return [candidate for candidate in candidates if cell_in_bounds(candidate, rows, cols)]

    def search(current: tuple[int, int], path: list[tuple[int, int]], visited: set[tuple[int, int]]) -> bool:
        """Try to extend the current simple path until it reaches the end."""
        if current == end:
            return len(path) >= min_length

        # The backtracking search keeps the path simple by avoiding visited cells.
        candidates = [candidate for candidate in neighbor_cells(current) if candidate not in visited]
        rng.shuffle(candidates)

        # Avoid finishing too early when the requested path length is longer.
        if len(path) < min_length and end in candidates and len(candidates) > 1:
            candidates.remove(end)
            candidates.append(end)

        for candidate in candidates:
            visited.add(candidate)
            path.append(candidate)
            if search(candidate, path, visited):
                return True
            path.pop()
            visited.remove(candidate)
        return False

    for _ in range(max_attempts):
        path = [start]
        if search(start, path, {start}):
            return path.copy()

    raise RuntimeError("Could not generate a valid random path after several attempts")


def _generate_manhattan_path(
    start: tuple[int, int],
    end: tuple[int, int],
    rng: random.Random,
) -> list[tuple[int, int]]:
    """Generate a randomized shortest monotone path between two cells."""
    # The moves are shuffled, but every move still goes closer to the end cell.
    row_delta = end[0] - start[0]
    col_delta = end[1] - start[1]
    row_step = 1 if row_delta >= 0 else -1
    col_step = 1 if col_delta >= 0 else -1
    moves = [(row_step, 0)] * abs(row_delta) + [(0, col_step)] * abs(col_delta)
    rng.shuffle(moves)

    path = [start]
    current = start
    for delta_row, delta_col in moves:
        current = (current[0] + delta_row, current[1] + delta_col)
        path.append(current)
    return path


def _generate_serpentine_path(
    rows: int,
    cols: int,
    rng: random.Random,
    min_length: int,
) -> list[tuple[int, int]]:
    """Generate a long simple path from the top-left to the bottom-right cell."""
    # We choose how many rows or columns to sweep before going to the end.
    row_candidates = [
        swept_rows
        for swept_rows in range(1, rows + 1, 2)
        if swept_rows * cols + (rows - swept_rows) >= min_length
    ]
    col_candidates = [
        swept_cols
        for swept_cols in range(1, cols + 1, 2)
        if swept_cols * rows + (cols - swept_cols) >= min_length
    ]

    choices: list[tuple[str, int]] = [("rows", value) for value in row_candidates]
    choices.extend(("cols", value) for value in col_candidates)
    if not choices:
        raise RuntimeError("Could not construct a long enough serpentine path")

    orientation, sweep_count = rng.choice(choices)
    if orientation == "rows":
        return _row_serpentine_path(rows, cols, sweep_count)
    return _column_serpentine_path(rows, cols, sweep_count)


def _row_serpentine_path(rows: int, cols: int, swept_rows: int) -> list[tuple[int, int]]:
    """Build a long path by sweeping complete rows first."""
    path: list[tuple[int, int]] = []
    for row in range(swept_rows):
        col_range = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
        path.extend((row, col) for col in col_range)
    path.extend((row, cols - 1) for row in range(swept_rows, rows))
    return path


def _column_serpentine_path(rows: int, cols: int, swept_cols: int) -> list[tuple[int, int]]:
    """Build a long path by sweeping complete columns first."""
    path: list[tuple[int, int]] = []
    for col in range(swept_cols):
        row_range = range(rows) if col % 2 == 0 else range(rows - 1, -1, -1)
        path.extend((row, col) for row in row_range)
    path.extend((rows - 1, col) for col in range(swept_cols, cols))
    return path


def build_instance_from_path(
    path: list[tuple[int, int]],
    rows: int,
    cols: int,
    *,
    fixed_used: set[tuple[int, int]] | None = None,
    fixed_empty: set[tuple[int, int]] | None = None,
    fixed_edges: set[tuple[tuple[int, int], tuple[int, int]]] | None = None,
) -> TracksInstance:
    """Build a normalized instance from a valid path."""
    if len(path) < 2:
        raise ValueError("A valid path must contain at least two cells")
    if len(set(path)) != len(path):
        raise ValueError("The path must be simple")

    for cell in path:
        if not cell_in_bounds(cell, rows, cols):
            raise ValueError(f"path cell {cell} lies outside the grid")

    for first, second in zip(path, path[1:]):
        if not are_orthogonally_adjacent(first, second):
            raise ValueError("Consecutive path cells must be orthogonally adjacent")

    # Clues are derived from the path, so the generated instance is solvable.
    used_cells = set(path)
    row_clues = tuple(sum((row, col) in used_cells for col in range(cols)) for row in range(rows))
    col_clues = tuple(sum((row, col) in used_cells for row in range(rows)) for col in range(cols))
    return TracksInstance(
        rows=rows,
        cols=cols,
        start=path[0],
        end=path[-1],
        row_clues=row_clues,
        col_clues=col_clues,
        fixed_used=frozenset(fixed_used or set()),
        fixed_empty=frozenset(fixed_empty or set()),
        fixed_edges=frozenset(fixed_edges or set()),
    )


def generate_tracks_instance(
    rows: int,
    cols: int,
    *,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
    seed: int | None = None,
    min_path_length: int | None = None,
    fixed_used_hints: int = 0,
    fixed_edge_hints: int = 0,
) -> TracksInstance:
    """Generate a Tracks instance by hiding a valid path in the clues."""
    rng = random.Random(seed)
    # Generate the hidden valid route first, then turn it into puzzle data.
    path = generate_random_path(
        rows,
        cols,
        start=start,
        end=end,
        seed=seed,
        min_length=min_path_length,
    )

    internal_cells = [cell for cell in path[1:-1]]
    path_edges = [canonical_edge(first, second) for first, second in zip(path, path[1:])]

    # Hints reveal part of the hidden route without changing the solution path.
    hint_used = set(rng.sample(internal_cells, k=min(fixed_used_hints, len(internal_cells))))
    hint_edges = set(rng.sample(path_edges, k=min(fixed_edge_hints, len(path_edges))))

    return build_instance_from_path(
        path,
        rows,
        cols,
        fixed_used=hint_used,
        fixed_edges=hint_edges,
    )


def difficulty_generation_params(rows: int, cols: int, difficulty: str) -> dict[str, int]:
    """Return generation parameters for a named Tracks difficulty."""
    normalized = difficulty.strip().lower()
    area = rows * cols
    shortest_path_length = rows + cols - 1

    # Easy boards use a short route and expose more fixed hints.
    if normalized == "easy":
        return {
            "min_path_length": shortest_path_length,
            "fixed_used_hints": max(1, area // 8),
            "fixed_edge_hints": max(1, area // 10),
        }
    # Medium boards ask for a longer path and reveal fewer hints.
    if normalized == "medium":
        return {
            "min_path_length": max(shortest_path_length, area // 3),
            "fixed_used_hints": max(1, area // 16),
            "fixed_edge_hints": max(1, area // 18),
        }
    # Hard boards use the longest routes and the fewest hints.
    if normalized == "hard":
        return {
            "min_path_length": max(shortest_path_length, area // 2),
            "fixed_used_hints": max(1, area // 32),
            "fixed_edge_hints": max(1, area // 40),
        }
    raise ValueError("difficulty must be one of Easy, Medium, or Hard")


def serialize_tracks_instance(instance: TracksInstance) -> str:
    """Serialize a Tracks instance using the parser format."""
    # The text format is simple on purpose so maps can be edited by hand.
    lines = [
        f"rows={instance.rows}",
        f"cols={instance.cols}",
        f"start={instance.start[0]},{instance.start[1]}",
        f"end={instance.end[0]},{instance.end[1]}",
        "row_clues=" + ",".join(str(value) for value in instance.row_clues),
        "col_clues=" + ",".join(str(value) for value in instance.col_clues),
    ]

    if instance.fixed_used:
        used_cells = ";".join(f"{row},{col}" for row, col in sorted(instance.fixed_used))
        lines.append(f"fixed_used={used_cells}")
    if instance.fixed_empty:
        empty_cells = ";".join(f"{row},{col}" for row, col in sorted(instance.fixed_empty))
        lines.append(f"fixed_empty={empty_cells}")
    if instance.fixed_edges:
        edges = ";".join(
            f"{first[0]},{first[1]}-{second[0]},{second[1]}"
            for first, second in sorted(instance.fixed_edges)
        )
        lines.append(f"fixed_edges={edges}")
    if instance.fixed_patterns:
        patterns = ";".join(
            f"{cell[0]},{cell[1]}:{local_pattern_token(pattern)}"
            for cell, pattern in sorted(instance.fixed_patterns.items())
        )
        lines.append(f"fixed_patterns={patterns}")

    return "\n".join(lines) + "\n"


def save_tracks_instance(instance: TracksInstance, path: str | Path) -> Path:
    """Write a Tracks instance to disk and return the target path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_tracks_instance(instance), encoding="utf-8")
    return output_path
