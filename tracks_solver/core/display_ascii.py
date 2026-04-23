"""ASCII rendering utilities for Tracks."""

from __future__ import annotations

from .models import Cell, TracksInstance, TracksSolution


def format_tracks_board(instance: TracksInstance, solution: TracksSolution | None = None) -> str:
    """Return an ASCII view of a Tracks instance and, optionally, a solution."""
    used_cells = set(solution.used_cells) if solution is not None else set()
    selected_edges = set(solution.selected_edges) if solution is not None else set()

    lines: list[str] = []
    top_clues = "    " + " ".join(f"{clue:>2}" for clue in instance.col_clues)
    lines.append(top_clues)

    for row in range(instance.rows):
        cells_as_text: list[str] = []
        for col in range(instance.cols):
            cell = (row, col)
            symbol = _cell_symbol(cell, instance, used_cells, selected_edges)
            cells_as_text.append(f"{symbol:>2}")
        lines.append(f"{instance.row_clues[row]:>2} " + " ".join(cells_as_text))

    return "\n".join(lines)


def print_tracks_board(instance: TracksInstance, solution: TracksSolution | None = None) -> None:
    """Print the ASCII view of a Tracks instance."""
    print(format_tracks_board(instance, solution))


def _cell_symbol(
    cell: Cell,
    instance: TracksInstance,
    used_cells: set[Cell],
    selected_edges: set[tuple[Cell, Cell]],
) -> str:
    if cell == instance.start:
        return "A"
    if cell == instance.end:
        return "B"
    if cell not in used_cells:
        return "."

    directions = _selected_directions(cell, selected_edges)
    if directions == {"L", "R"}:
        return "-"
    if directions == {"U", "D"}:
        return "|"
    if len(directions) == 2:
        return "+"
    return "?"


def _selected_directions(cell: Cell, selected_edges: set[tuple[Cell, Cell]]) -> set[str]:
    row, col = cell
    directions: set[str] = set()

    for first, second in selected_edges:
        if cell == first:
            target = second
        elif cell == second:
            target = first
        else:
            continue

        row_delta = target[0] - row
        col_delta = target[1] - col
        if row_delta == -1:
            directions.add("U")
        elif row_delta == 1:
            directions.add("D")
        elif col_delta == -1:
            directions.add("L")
        elif col_delta == 1:
            directions.add("R")

    return directions
