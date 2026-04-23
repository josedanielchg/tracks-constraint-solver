"""Parser for the text-based Tracks instance format."""

from __future__ import annotations

from pathlib import Path

from .models import Cell, Edge, TracksInstance, canonical_edge


class TracksInstanceFormatError(ValueError):
    """Raised when a Tracks instance file is malformed."""


def parse_tracks_instance(path: str | Path) -> TracksInstance:
    """Parse a Tracks instance file from disk."""
    file_path = Path(path)
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TracksInstanceFormatError(f"Could not read instance file: {file_path}") from exc

    return parse_tracks_instance_text(raw_text, source=str(file_path))


def parse_tracks_instance_text(text: str, *, source: str = "<memory>") -> TracksInstance:
    """Parse a Tracks instance from its textual representation."""
    raw_fields: dict[str, str] = {}

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        if "=" not in line:
            raise TracksInstanceFormatError(
                f"{source}:{line_number}: expected a 'key=value' line, got {raw_line!r}"
            )

        key, value = (part.strip() for part in line.split("=", 1))
        if not key:
            raise TracksInstanceFormatError(f"{source}:{line_number}: empty key is not allowed")
        if key in raw_fields:
            raise TracksInstanceFormatError(
                f"{source}:{line_number}: duplicate field {key!r} is not allowed"
            )
        raw_fields[key] = value

    required_keys = {"rows", "cols", "start", "end", "row_clues", "col_clues"}
    missing_keys = sorted(required_keys - raw_fields.keys())
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise TracksInstanceFormatError(f"{source}: missing required field(s): {missing}")

    try:
        rows = _parse_integer(raw_fields["rows"], field_name="rows", source=source)
        cols = _parse_integer(raw_fields["cols"], field_name="cols", source=source)
        start = _parse_cell(raw_fields["start"], field_name="start", source=source)
        end = _parse_cell(raw_fields["end"], field_name="end", source=source)
        row_clues = tuple(
            _parse_integer_list(raw_fields["row_clues"], field_name="row_clues", source=source)
        )
        col_clues = tuple(
            _parse_integer_list(raw_fields["col_clues"], field_name="col_clues", source=source)
        )
        fixed_used = frozenset(
            _parse_cell_list(raw_fields.get("fixed_used", ""), field_name="fixed_used", source=source)
        )
        fixed_empty = frozenset(
            _parse_cell_list(
                raw_fields.get("fixed_empty", ""), field_name="fixed_empty", source=source
            )
        )
        fixed_edges = frozenset(
            _parse_edge_list(raw_fields.get("fixed_edges", ""), field_name="fixed_edges", source=source)
        )
    except ValueError as exc:
        raise TracksInstanceFormatError(str(exc)) from exc

    try:
        return TracksInstance(
            rows=rows,
            cols=cols,
            start=start,
            end=end,
            row_clues=row_clues,
            col_clues=col_clues,
            fixed_used=fixed_used,
            fixed_empty=fixed_empty,
            fixed_edges=fixed_edges,
        )
    except ValueError as exc:
        raise TracksInstanceFormatError(f"{source}: {exc}") from exc


def _parse_integer(raw_value: str, *, field_name: str, source: str) -> int:
    if not raw_value:
        raise ValueError(f"{source}: field {field_name!r} cannot be empty")

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{source}: field {field_name!r} must be an integer, got {raw_value!r}"
        ) from exc


def _parse_integer_list(raw_value: str, *, field_name: str, source: str) -> list[int]:
    if not raw_value:
        raise ValueError(f"{source}: field {field_name!r} cannot be empty")

    values: list[int] = []
    for part in raw_value.split(","):
        value = part.strip()
        if not value:
            raise ValueError(f"{source}: field {field_name!r} contains an empty item")
        values.append(_parse_integer(value, field_name=field_name, source=source))
    return values


def _parse_cell(raw_value: str, *, field_name: str, source: str) -> Cell:
    parts = [part.strip() for part in raw_value.split(",")]
    if len(parts) != 2 or not all(parts):
        raise ValueError(
            f"{source}: field {field_name!r} must have the form 'row,col', got {raw_value!r}"
        )

    row = _parse_integer(parts[0], field_name=field_name, source=source)
    col = _parse_integer(parts[1], field_name=field_name, source=source)
    return (row, col)


def _parse_cell_list(raw_value: str, *, field_name: str, source: str) -> list[Cell]:
    if not raw_value.strip():
        return []

    cells: list[Cell] = []
    for item in raw_value.split(";"):
        value = item.strip()
        if not value:
            raise ValueError(f"{source}: field {field_name!r} contains an empty cell item")
        cells.append(_parse_cell(value, field_name=field_name, source=source))
    return cells


def _parse_edge_list(raw_value: str, *, field_name: str, source: str) -> list[Edge]:
    if not raw_value.strip():
        return []

    edges: list[Edge] = []
    for item in raw_value.split(";"):
        value = item.strip()
        if not value:
            raise ValueError(f"{source}: field {field_name!r} contains an empty edge item")

        endpoints = [part.strip() for part in value.split("-", 1)]
        if len(endpoints) != 2 or not all(endpoints):
            raise ValueError(
                f"{source}: edge {value!r} in field {field_name!r} must have the form "
                "'row1,col1-row2,col2'"
            )

        first = _parse_cell(endpoints[0], field_name=field_name, source=source)
        second = _parse_cell(endpoints[1], field_name=field_name, source=source)
        edges.append(canonical_edge(first, second))

    return edges
