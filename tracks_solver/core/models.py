"""Core data structures for Tracks."""

from __future__ import annotations

from dataclasses import dataclass, field

Cell = tuple[int, int]
Edge = tuple[Cell, Cell]


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

    def __post_init__(self) -> None:
        row_clues = tuple(int(value) for value in self.row_clues)
        col_clues = tuple(int(value) for value in self.col_clues)
        fixed_used = {tuple(cell) for cell in self.fixed_used}
        fixed_empty = {tuple(cell) for cell in self.fixed_empty}
        fixed_edges = {canonical_edge(*edge) for edge in self.fixed_edges}

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

        object.__setattr__(self, "fixed_used", frozenset(fixed_used))
        object.__setattr__(self, "fixed_empty", frozenset(fixed_empty))
        object.__setattr__(self, "fixed_edges", frozenset(fixed_edges))


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
