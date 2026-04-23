"""Core utilities for the Tracks puzzle."""

from .graph import GridGraph, build_grid_graph
from .models import (
    Cell,
    Direction,
    Edge,
    TracksInstance,
    TracksSolution,
    are_orthogonally_adjacent,
    canonical_edge,
    cell_in_bounds,
    local_pattern_token,
    neighbor_in_direction,
    normalize_local_pattern,
    pattern_implied_edges,
)
from .display_ascii import format_tracks_board, print_tracks_board
from .parser import TracksInstanceFormatError, parse_tracks_instance, parse_tracks_instance_text
from .validation import ValidationResult, assert_valid_solution, validate_solution

__all__ = [
    "Cell",
    "Direction",
    "Edge",
    "GridGraph",
    "TracksInstance",
    "TracksInstanceFormatError",
    "TracksSolution",
    "ValidationResult",
    "are_orthogonally_adjacent",
    "assert_valid_solution",
    "build_grid_graph",
    "canonical_edge",
    "cell_in_bounds",
    "format_tracks_board",
    "local_pattern_token",
    "neighbor_in_direction",
    "normalize_local_pattern",
    "parse_tracks_instance",
    "parse_tracks_instance_text",
    "pattern_implied_edges",
    "print_tracks_board",
    "validate_solution",
]
