"""Tests for the Tracks instance parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from tracks_solver.core import (
    TracksInstanceFormatError,
    canonical_edge,
    parse_tracks_instance,
    parse_tracks_instance_text,
)

MANUAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "tracks" / "manual"


def test_parse_manual_instance_file() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_4x4.txt")

    assert instance.rows == 4
    assert instance.cols == 4
    assert instance.start == (0, 0)
    assert instance.end == (3, 3)
    assert instance.row_clues == (4, 1, 1, 1)
    assert instance.col_clues == (1, 1, 1, 4)
    assert instance.fixed_used == frozenset({(0, 0), (3, 3)})
    assert instance.fixed_empty == frozenset()
    assert instance.fixed_edges == frozenset()


def test_parse_manual_instance_with_optional_fields() -> None:
    instance = parse_tracks_instance(MANUAL_DATA_DIR / "small_5x5.txt")

    assert instance.rows == 5
    assert instance.cols == 5
    assert instance.fixed_used == frozenset({(4, 0), (0, 4), (2, 1)})
    assert instance.fixed_empty == frozenset({(4, 4)})
    assert instance.fixed_edges == frozenset(
        {
            canonical_edge((2, 0), (2, 1)),
            canonical_edge((0, 3), (0, 4)),
        }
    )


def test_parser_rejects_missing_required_field() -> None:
    text = "\n".join(
        [
            "rows=4",
            "cols=4",
            "start=0,0",
            "row_clues=1,1,1,1",
            "col_clues=1,1,1,1",
        ]
    )

    with pytest.raises(TracksInstanceFormatError, match="missing required field"):
        parse_tracks_instance_text(text)


def test_parser_rejects_wrong_row_clue_length() -> None:
    text = "\n".join(
        [
            "rows=4",
            "cols=4",
            "start=0,0",
            "end=3,3",
            "row_clues=1,1,1",
            "col_clues=1,1,1,0",
        ]
    )

    with pytest.raises(TracksInstanceFormatError, match="row clue count must match"):
        parse_tracks_instance_text(text)


def test_parser_rejects_wrong_column_clue_length() -> None:
    text = "\n".join(
        [
            "rows=4",
            "cols=4",
            "start=0,0",
            "end=3,3",
            "row_clues=1,1,1,1",
            "col_clues=1,1,1",
        ]
    )

    with pytest.raises(TracksInstanceFormatError, match="column clue count must match"):
        parse_tracks_instance_text(text)


def test_parser_rejects_start_outside_grid() -> None:
    text = "\n".join(
        [
            "rows=4",
            "cols=4",
            "start=4,0",
            "end=3,3",
            "row_clues=1,1,1,1",
            "col_clues=1,1,1,1",
        ]
    )

    with pytest.raises(TracksInstanceFormatError, match="start cell must lie inside the grid"):
        parse_tracks_instance_text(text)


def test_parser_rejects_conflicting_fixed_cells() -> None:
    text = "\n".join(
        [
            "rows=4",
            "cols=4",
            "start=0,0",
            "end=3,3",
            "row_clues=1,1,1,1",
            "col_clues=1,1,1,1",
            "fixed_used=1,1",
            "fixed_empty=1,1",
        ]
    )

    with pytest.raises(TracksInstanceFormatError, match="must be disjoint"):
        parse_tracks_instance_text(text)


def test_parser_rejects_non_adjacent_fixed_edge() -> None:
    text = "\n".join(
        [
            "rows=4",
            "cols=4",
            "start=0,0",
            "end=3,3",
            "row_clues=1,1,1,1",
            "col_clues=1,1,1,1",
            "fixed_edges=0,0-2,2",
        ]
    )

    with pytest.raises(TracksInstanceFormatError, match="orthogonally adjacent"):
        parse_tracks_instance_text(text)
