"""Core data structures for Tracks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

Cell = tuple[int, int]
Edge = tuple[Cell, Cell]
Direction = str

_DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}
_DIRECTION_ORDER = {"U": 0, "D": 1, "L": 2, "R": 3}
_PATTERN_ALIASES = {
    "H": ("L", "R"),
    "V": ("U", "D"),
}


def cell_in_bounds(cell: Cell, rows: int, cols: int) -> bool:
    """Return whether ``cell`` lies inside a ``rows`` x ``cols`` grid."""
    row, col = cell
    return 0 <= row < rows and 0 <= col < cols


def are_orthogonally_adjacent(first: Cell, second: Cell) -> bool:
    """Return whether two cells are adjacent by one horizontal or vertical step."""
    row_distance = abs(first[0] - second[0])
    col_distance = abs(first[1] - second[1])
    return row_distance + col_distance == 1


def canonical_edge(first: Cell, second: Cell) -> Edge:
    """Return an undirected edge in a deterministic lexicographic order."""
    return (first, second) if first <= second else (second, first)


def normalize_local_pattern(pattern: str | Iterable[str]) -> tuple[Direction, ...]:
    """Return a normalized 1-edge or 2-edge local track pattern."""
    if isinstance(pattern, str):
        token = pattern.strip().upper().replace(" ", "")
        directions = _PATTERN_ALIASES.get(token, tuple(token))
    else:
        directions = tuple(str(direction).strip().upper() for direction in pattern)

    if not directions:
        raise ValueError("local pattern cannot be empty")

    invalid = sorted({direction for direction in directions if direction not in _DIRECTION_DELTAS})
    if invalid:
        raise ValueError(
            "local pattern directions must be chosen from U, D, L, R; "
            f"got invalid direction(s): {invalid}"
        )

    if len(set(directions)) != len(directions):
        raise ValueError("local pattern directions must be distinct")

    normalized = tuple(sorted(directions, key=_DIRECTION_ORDER.__getitem__))
    if len(normalized) not in {1, 2}:
        raise ValueError("local patterns must contain exactly one or two directions")
    return normalized


def local_pattern_token(pattern: str | Iterable[str]) -> str:
    """Serialize a local pattern using a compact human-readable token."""
    normalized = normalize_local_pattern(pattern)
    if normalized == ("L", "R"):
        return "H"
    if normalized == ("U", "D"):
        return "V"
    return "".join(normalized)


def neighbor_in_direction(cell: Cell, direction: Direction) -> Cell:
    """Return the neighboring cell reached from ``cell`` in ``direction``."""
    delta_row, delta_col = _DIRECTION_DELTAS[direction]
    return (cell[0] + delta_row, cell[1] + delta_col)


def pattern_implied_edges(cell: Cell, pattern: str | Iterable[str]) -> tuple[Edge, ...]:
    """Return the in-grid edges selected by a local pattern at ``cell``."""
    return tuple(
        canonical_edge(cell, neighbor_in_direction(cell, direction))
        for direction in normalize_local_pattern(pattern)
    )


@dataclass(slots=True, frozen=True)
class TracksInstance:
    """Normalized Tracks puzzle instance."""

    rows: int
    cols: int
    start: Cell
    end: Cell
    row_clues: tuple[int, ...]
    col_clues: tuple[int, ...]
    fixed_used: frozenset[Cell] = field(default_factory=frozenset)
    fixed_empty: frozenset[Cell] = field(default_factory=frozenset)
    fixed_edges: frozenset[Edge] = field(default_factory=frozenset)
    fixed_patterns: dict[Cell, tuple[Direction, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        row_clues = tuple(int(value) for value in self.row_clues)
        col_clues = tuple(int(value) for value in self.col_clues)
        fixed_used = {tuple(cell) for cell in self.fixed_used}
        fixed_empty = {tuple(cell) for cell in self.fixed_empty}
        fixed_edges = {canonical_edge(*edge) for edge in self.fixed_edges}
        fixed_patterns = {
            tuple(cell): normalize_local_pattern(pattern)
            for cell, pattern in dict(self.fixed_patterns).items()
        }

        object.__setattr__(self, "row_clues", row_clues)
        object.__setattr__(self, "col_clues", col_clues)

        if self.rows <= 0:
            raise ValueError("rows must be positive")
        if self.cols <= 0:
            raise ValueError("cols must be positive")

        if not cell_in_bounds(self.start, self.rows, self.cols):
            raise ValueError("start cell must lie inside the grid")
        if not cell_in_bounds(self.end, self.rows, self.cols):
            raise ValueError("end cell must lie inside the grid")
        if self.start == self.end:
            raise ValueError("start and end cells must be different")

        if len(row_clues) != self.rows:
            raise ValueError("row clue count must match the number of rows")
        if len(col_clues) != self.cols:
            raise ValueError("column clue count must match the number of columns")
        if any(value < 0 for value in row_clues):
            raise ValueError("row clues must be non-negative")
        if any(value < 0 for value in col_clues):
            raise ValueError("column clues must be non-negative")
        if sum(row_clues) != sum(col_clues):
            raise ValueError("row clues and column clues must have the same total")

        for cell in fixed_used | fixed_empty:
            if not cell_in_bounds(cell, self.rows, self.cols):
                raise ValueError(f"fixed cell {cell} must lie inside the grid")

        if self.start in fixed_empty or self.end in fixed_empty:
            raise ValueError("start and end cells cannot be fixed as empty")

        fixed_used.update({self.start, self.end})

        if fixed_used & fixed_empty:
            raise ValueError("fixed used cells and fixed empty cells must be disjoint")

        user_fixed_edges = set(fixed_edges)

        for edge in fixed_edges:
            first, second = edge
            if not cell_in_bounds(first, self.rows, self.cols):
                raise ValueError(f"fixed edge endpoint {first} must lie inside the grid")
            if not cell_in_bounds(second, self.rows, self.cols):
                raise ValueError(f"fixed edge endpoint {second} must lie inside the grid")
            if not are_orthogonally_adjacent(first, second):
                raise ValueError(f"fixed edge {edge} must connect orthogonally adjacent cells")
            if first in fixed_empty or second in fixed_empty:
                raise ValueError("fixed edges cannot touch cells fixed as empty")

        pattern_edges_by_cell: dict[Cell, frozenset[Edge]] = {}
        for cell, pattern in fixed_patterns.items():
            if not cell_in_bounds(cell, self.rows, self.cols):
                raise ValueError(f"fixed pattern cell {cell} must lie inside the grid")
            if cell in fixed_empty:
                raise ValueError(f"fixed pattern cell {cell} cannot be fixed as empty")

            if cell in {self.start, self.end}:
                if len(pattern) != 1:
                    raise ValueError(
                        f"terminal pattern at {cell} must contain exactly one internal direction"
                    )
            elif len(pattern) != 2:
                raise ValueError(
                    f"non-terminal pattern at {cell} must contain exactly two directions"
                )

            implied_edges: set[Edge] = set()
            for direction in pattern:
                neighbor = neighbor_in_direction(cell, direction)
                if not cell_in_bounds(neighbor, self.rows, self.cols):
                    raise ValueError(
                        f"fixed pattern {local_pattern_token(pattern)!r} at {cell} points outside the grid"
                    )
                if neighbor in fixed_empty:
                    raise ValueError(
                        f"fixed pattern at {cell} cannot connect to cell {neighbor} fixed as empty"
                    )
                implied_edges.add(canonical_edge(cell, neighbor))

            conflicting_fixed_edges = sorted(
                edge for edge in user_fixed_edges if cell in edge and edge not in implied_edges
            )
            if conflicting_fixed_edges:
                raise ValueError(
                    f"fixed pattern at {cell} conflicts with fixed edge(s) {conflicting_fixed_edges}"
                )

            pattern_edges_by_cell[cell] = frozenset(implied_edges)
            fixed_used.add(cell)
            fixed_edges.update(implied_edges)

        for cell, implied_edges in pattern_edges_by_cell.items():
            for edge in implied_edges:
                neighbor = edge[1] if edge[0] == cell else edge[0]
                neighbor_pattern_edges = pattern_edges_by_cell.get(neighbor)
                if neighbor_pattern_edges is not None and edge not in neighbor_pattern_edges:
                    raise ValueError(
                        "adjacent fixed patterns must agree on their shared edge; "
                        f"conflict between {cell} and {neighbor}"
                    )

        object.__setattr__(self, "fixed_used", frozenset(fixed_used))
        object.__setattr__(self, "fixed_empty", frozenset(fixed_empty))
        object.__setattr__(self, "fixed_edges", frozenset(fixed_edges))
        object.__setattr__(
            self,
            "fixed_patterns",
            {cell: fixed_patterns[cell] for cell in sorted(fixed_patterns)},
        )


@dataclass(slots=True)
class TracksSolution:
    """Solution container shared by the solver, validator, and UI."""

    used_cells: set[Cell] = field(default_factory=set)
    selected_edges: set[Edge] = field(default_factory=set)
    status: str = "unknown"
    solve_time: float = 0.0
    objective_value: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.used_cells = {tuple(cell) for cell in self.used_cells}
        self.selected_edges = {canonical_edge(*edge) for edge in self.selected_edges}
