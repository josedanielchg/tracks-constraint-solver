"""Generate valid Tracks instances from random simple paths."""

from __future__ import annotations

import random
from pathlib import Path

from tracks_solver.core import TracksInstance, are_orthogonally_adjacent, canonical_edge, cell_in_bounds


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
    """Generate a random simple path inside a grid."""
    rng = random.Random(seed)
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

    def neighbor_cells(cell: tuple[int, int]) -> list[tuple[int, int]]:
        row, col = cell
        candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        return [candidate for candidate in candidates if cell_in_bounds(candidate, rows, cols)]

    def search(current: tuple[int, int], path: list[tuple[int, int]], visited: set[tuple[int, int]]) -> bool:
        if current == end:
            return len(path) >= min_length

        candidates = [candidate for candidate in neighbor_cells(current) if candidate not in visited]
        rng.shuffle(candidates)

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
    """Generate a Tracks instance with at least one valid solution."""
    rng = random.Random(seed)
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

    hint_used = set(rng.sample(internal_cells, k=min(fixed_used_hints, len(internal_cells))))
    hint_edges = set(rng.sample(path_edges, k=min(fixed_edge_hints, len(path_edges))))

    return build_instance_from_path(
        path,
        rows,
        cols,
        fixed_used=hint_used,
        fixed_edges=hint_edges,
    )


def serialize_tracks_instance(instance: TracksInstance) -> str:
    """Serialize a Tracks instance using the parser format."""
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

    return "\n".join(lines) + "\n"


def save_tracks_instance(instance: TracksInstance, path: str | Path) -> Path:
    """Write a Tracks instance to disk and return the target path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_tracks_instance(instance), encoding="utf-8")
    return output_path
