"""Playable Pygame interface for Tracks.

This module intentionally sits next to the simple viewer instead of replacing
it.  The solver, parser, generator, and validator remain independent from the
interactive UI.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from tracks_solver.core import (
    Cell,
    Direction,
    Edge,
    TracksInstance,
    TracksSolution,
    canonical_edge,
    cell_in_bounds,
    neighbor_in_direction,
    normalize_local_pattern,
    parse_tracks_instance,
    validate_solution,
)
from tracks_solver.generation import difficulty_generation_params, generate_tracks_instance
from tracks_solver.solver import SolverUnavailableError, solve_tracks_instance

from .pygame_viewer import TracksViewer, ViewerLayout


EMPTY_PATTERN: tuple[Direction, ...] = ()
PAIR_PATTERNS: tuple[tuple[Direction, ...], ...] = (
    ("L", "R"),
    ("U", "D"),
    ("U", "R"),
    ("U", "L"),
    ("D", "R"),
    ("D", "L"),
)
SINGLE_PATTERNS: tuple[tuple[Direction, ...], ...] = (
    ("U",),
    ("D",),
    ("L",),
    ("R",),
)
OPPOSITE_DIRECTIONS: dict[Direction, Direction] = {
    "U": "D",
    "D": "U",
    "L": "R",
    "R": "L",
}
GRID_SIZE_OPTIONS = ((4, 4), (5, 5), (6, 6), (8, 8), (10, 10))
DIFFICULTY_OPTIONS = ("Easy", "Medium", "Hard")
DATA_FOLDERS = (
    Path("data") / "tracks" / "manual",
    Path("data") / "tracks" / "datasets",
    Path("data") / "tracks" / "generated",
)
LEGEND_ENTRIES = (
    ("Required cell", "Must be used; you choose the shape.", "fixed_used"),
    ("Fixed connection", "Must keep one forced connection; rotation is limited.", "fixed_edges"),
    ("Fixed shape", "Exact piece; cannot be rotated.", "fixed_patterns"),
    ("Blocked cell", "Cannot be used or clicked.", "fixed_empty"),
)


@dataclass(slots=True)
class Button:
    """Clickable UI button."""

    label: str
    rect: pygame.Rect
    action: str


@dataclass(slots=True)
class PlayerBoardState:
    """Local editable route drawn by the player."""

    instance: TracksInstance
    patterns: dict[Cell, tuple[Direction, ...]] = field(default_factory=dict)

    @classmethod
    def from_instance(cls, instance: TracksInstance) -> "PlayerBoardState":
        patterns: dict[Cell, tuple[Direction, ...]] = {}
        # Start the player board with every fixed requirement already visible.
        for cell in sorted(instance.fixed_patterns):
            patterns[cell] = instance.fixed_patterns[cell]
        for cell in sorted(instance.fixed_used):
            patterns.setdefault(cell, _default_pattern_for_cell(instance, cell))
        for edge in sorted(instance.fixed_edges):
            for cell in edge:
                patterns[cell] = _default_pattern_for_cell(instance, cell)
        return cls(instance=instance, patterns=patterns)

    def cycle_cell(self, cell: Cell) -> None:
        """Move a cell to its next allowed local pattern."""
        if _is_locked_cell(self.instance, cell):
            return

        allowed = allowed_patterns_for_cell(self.instance, cell)
        if not allowed:
            return

        current = self.patterns.get(cell, EMPTY_PATTERN)
        next_index = 0
        if current in allowed:
            next_index = (allowed.index(current) + 1) % len(allowed)

        new_pattern = allowed[next_index]
        if new_pattern:
            self.patterns[cell] = new_pattern
        else:
            self.patterns.pop(cell, None)

    def clear_cell(self, cell: Cell) -> None:
        """Clear a cell when the fixed requirements allow an empty pattern."""
        if _is_locked_cell(self.instance, cell):
            return
        if EMPTY_PATTERN in allowed_patterns_for_cell(self.instance, cell):
            self.patterns.pop(cell, None)

    def to_solution(self) -> TracksSolution:
        """Convert local player patterns into a candidate solution."""
        used_cells = {cell for cell, pattern in self.patterns.items() if pattern}
        selected_edges: set[Edge] = set()

        # Two adjacent pieces connect only when both pieces point at each other.
        for cell, pattern in self.patterns.items():
            if not pattern:
                continue
            for direction in pattern:
                neighbor = neighbor_in_direction(cell, direction)
                if not cell_in_bounds(neighbor, self.instance.rows, self.instance.cols):
                    continue
                neighbor_pattern = self.patterns.get(neighbor, EMPTY_PATTERN)
                if OPPOSITE_DIRECTIONS[direction] in neighbor_pattern:
                    selected_edges.add(canonical_edge(cell, neighbor))

        return TracksSolution(
            used_cells=used_cells,
            selected_edges=selected_edges,
            status="player",
        )


class TracksGame:
    """Menu-driven playable Tracks UI."""

    def __init__(self, *, width: int = 1180, height: int = 820) -> None:
        self.width = width
        self.height = height
        self.board_size = min(height, 820)
        self.panel_left = self.board_size + 20
        self.viewer = TracksViewer(width=self.board_size, height=self.board_size, clue_margin=80)
        self.mode = "home"
        self.size_index = 1
        self.difficulty_index = 0
        self.map_index = 0
        self.map_paths = discover_map_files()
        self.instance: TracksInstance | None = None
        self.player_state: PlayerBoardState | None = None
        self.solution: TracksSolution | None = None
        self.show_solution = False
        self.status_message = ""
        self.buttons: list[Button] = []

    def run(self) -> None:
        """Open the playable UI window."""
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tracks")
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse(event.pos, event.button)

            screen.blit(self.render_to_surface(), (0, 0))
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def render_to_surface(self) -> pygame.Surface:
        """Render either the home screen or the active board."""
        pygame.font.init()
        surface = pygame.Surface((self.width, self.height))
        surface.fill((248, 248, 248))
        self.buttons = []

        # The game has only two screens: menu and active board.
        if self.mode == "board" and self.instance is not None and self.player_state is not None:
            self._draw_board_screen(surface)
        else:
            self._draw_home_screen(surface)

        return surface

    def handle_mouse(self, position: tuple[int, int], button: int) -> None:
        """Handle one mouse click."""
        for ui_button in self.buttons:
            if ui_button.rect.collidepoint(position):
                self._dispatch_action(ui_button.action)
                return

        if self.mode != "board" or self.instance is None or self.player_state is None:
            return

        cell = self._cell_at_position(position)
        if cell is None:
            return
        if button == 1:
            self.player_state.cycle_cell(cell)
            self.show_solution = False
            self.status_message = ""
        elif button == 3:
            self.player_state.clear_cell(cell)
            self.show_solution = False
            self.status_message = ""

    def start_board(self, instance: TracksInstance, *, status_message: str = "") -> None:
        """Open a playable board for ``instance``."""
        self.instance = instance
        self.player_state = PlayerBoardState.from_instance(instance)
        self.solution = None
        self.show_solution = False
        self.status_message = status_message
        self.mode = "board"

    def _draw_home_screen(self, surface: pygame.Surface) -> None:
        title_font = pygame.font.Font(None, 56)
        font = pygame.font.Font(None, 30)
        small_font = pygame.font.Font(None, 24)

        # The home screen keeps generation and map loading as separate panels.
        new_game_panel, load_map_panel = self._home_panel_rects()

        self._draw_centered_text(surface, title_font, "Tracks", (self.width // 2, 62))

        size_label = f"Size: {GRID_SIZE_OPTIONS[self.size_index][0]}x{GRID_SIZE_OPTIONS[self.size_index][1]}"
        difficulty = DIFFICULTY_OPTIONS[self.difficulty_index]

        self._draw_panel(surface, new_game_panel)
        self._draw_centered_text(surface, font, "New Game", (new_game_panel.centerx, new_game_panel.y + 34))
        size_row_x = _centered_row_x(new_game_panel.centerx, 130, 34, font.size(size_label)[0])
        self._add_button(surface, "Size", pygame.Rect(size_row_x, new_game_panel.y + 78, 130, 42), "cycle_size")
        self._draw_text(surface, font, size_label, (size_row_x + 164, new_game_panel.y + 86))
        difficulty_row_x = _centered_row_x(new_game_panel.centerx, 130, 34, font.size("Difficulty")[0])
        self._add_button(
            surface,
            difficulty,
            pygame.Rect(difficulty_row_x, new_game_panel.y + 132, 130, 42),
            "cycle_difficulty",
        )
        self._draw_text(surface, font, "Difficulty", (difficulty_row_x + 164, new_game_panel.y + 140))
        self._add_button(
            surface,
            "New Game",
            pygame.Rect(new_game_panel.centerx - 90, new_game_panel.y + 184, 180, 46),
            "new_game",
        )

        self._draw_panel(surface, load_map_panel)
        self._draw_centered_text(surface, font, "Load Map", (load_map_panel.centerx, load_map_panel.y + 34))
        if self.map_paths:
            selected = self.map_paths[self.map_index]
            label = _shorten_label(selected.name)
            self._draw_centered_text(surface, small_font, label, (load_map_panel.centerx, load_map_panel.y + 78))
            previous_rect = pygame.Rect(load_map_panel.centerx - 145, load_map_panel.y + 112, 130, 42)
            next_rect = pygame.Rect(load_map_panel.centerx + 15, load_map_panel.y + 112, 130, 42)
            self._add_button(surface, "Previous", previous_rect, "previous_map")
            self._add_button(surface, "Next", next_rect, "next_map")
            self._add_button(
                surface,
                "Load Map",
                pygame.Rect(load_map_panel.centerx - 90, load_map_panel.y + 172, 180, 46),
                "load_map",
            )
        else:
            self._draw_centered_text(
                surface,
                small_font,
                "No maps found",
                (load_map_panel.centerx, load_map_panel.y + 92),
            )

        if self.status_message:
            self._draw_centered_text(surface, small_font, self.status_message, (self.width // 2, self.height - 45))

    def _draw_board_screen(self, surface: pygame.Surface) -> None:
        assert self.instance is not None
        assert self.player_state is not None

        # The board can show either the exact solution or the player's current attempt.
        if self.show_solution and self.solution is not None:
            board_surface = self.viewer.render_to_surface(self.instance, self.solution)
        else:
            board_surface = self.viewer.render_to_surface(self.instance)
            self._draw_player_tracks(board_surface, self.player_state)
        surface.blit(board_surface, (0, 0))

        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 23)

        self._add_button(surface, "Show Solution", pygame.Rect(self.panel_left, 60, 220, 44), "show_solution")
        self._add_button(surface, "Check", pygame.Rect(self.panel_left, 118, 220, 44), "check")
        self._add_button(surface, "Back Home", pygame.Rect(self.panel_left, 176, 220, 44), "back_home")

        self._draw_text(surface, font, "Legend", (self.panel_left, 270))
        self._draw_legend(surface, small_font, self.panel_left, 315)

        if self.status_message:
            self._draw_wrapped_text(surface, small_font, self.status_message, (self.panel_left, 650), 300)

    def _draw_legend(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None:
        # Legend colors explain what each fixed hint means during play.
        colors = {
            "fixed_used": self.viewer.fixed_used_cell_color,
            "fixed_edges": self.viewer.fixed_edge_cell_color,
            "fixed_patterns": self.viewer.fixed_pattern_cell_color,
            "fixed_empty": self.viewer.fixed_empty_cell_color,
        }
        for index, (label, description, key) in enumerate(LEGEND_ENTRIES):
            color = colors[key]
            row_y = y + index * 78
            swatch = pygame.Rect(x, row_y, 24, 24)
            pygame.draw.rect(surface, color, swatch)
            pygame.draw.rect(surface, (0, 0, 0), swatch, 1)
            text_color = (255, 255, 255) if color == self.viewer.fixed_empty_cell_color else (0, 0, 0)
            if color == self.viewer.fixed_empty_cell_color:
                pygame.draw.line(surface, text_color, swatch.topleft, swatch.bottomright, 2)
            self._draw_text(surface, font, label, (x + 36, row_y + 1))
            self._draw_wrapped_text(surface, font, description, (x + 36, row_y + 23), 280)

    def _draw_player_tracks(self, surface: pygame.Surface, player_state: PlayerBoardState) -> None:
        layout = self.viewer._build_layout(player_state.instance)
        for cell, pattern in player_state.patterns.items():
            if not pattern:
                continue
            center = self.viewer._cell_center(cell, layout)
            for direction in pattern:
                endpoint = _direction_endpoint(center, direction, layout)
                pygame.draw.line(
                    surface,
                    self.viewer.foreground_color,
                    center,
                    endpoint,
                    self.viewer.track_width,
                )

        font = pygame.font.Font(None, max(24, layout.cell_size // 2))
        self.viewer._draw_terminals(surface, player_state.instance, layout, font)

    def _dispatch_action(self, action: str) -> None:
        # Menu and board buttons are routed through one small dispatcher.
        if action == "cycle_size":
            self.size_index = (self.size_index + 1) % len(GRID_SIZE_OPTIONS)
        elif action == "cycle_difficulty":
            self.difficulty_index = (self.difficulty_index + 1) % len(DIFFICULTY_OPTIONS)
        elif action == "previous_map" and self.map_paths:
            self.map_index = (self.map_index - 1) % len(self.map_paths)
        elif action == "next_map" and self.map_paths:
            self.map_index = (self.map_index + 1) % len(self.map_paths)
        elif action == "new_game":
            self._start_generated_game()
        elif action == "load_map":
            self._load_selected_map()
        elif action == "back_home":
            self.mode = "home"
            self.status_message = ""
        elif action == "check":
            self._check_player_solution()
        elif action == "show_solution":
            self._show_exact_solution()

    def _start_generated_game(self) -> None:
        rows, cols = GRID_SIZE_OPTIONS[self.size_index]
        difficulty = DIFFICULTY_OPTIONS[self.difficulty_index]
        params = difficulty_generation_params(rows, cols, difficulty)
        seed = random.randint(0, 10**9)
        try:
            # The UI reuses the same difficulty profile as the benchmark generator.
            instance = generate_tracks_instance(rows, cols, seed=seed, **params)
        except RuntimeError:
            instance = generate_tracks_instance(rows, cols, seed=seed)
        self.start_board(instance, status_message=f"Generated {difficulty} {rows}x{cols}")

    def _load_selected_map(self) -> None:
        if not self.map_paths:
            self.status_message = "No maps available"
            return
        path = self.map_paths[self.map_index]
        try:
            self.start_board(parse_tracks_instance(path), status_message=f"Loaded {path.name}")
        except ValueError as exc:
            self.status_message = f"Could not load map: {exc}"

    def _check_player_solution(self) -> None:
        assert self.instance is not None
        assert self.player_state is not None
        result = validate_solution(self.instance, self.player_state.to_solution())
        if result.is_valid:
            self.status_message = "Valid solution"
        elif result.errors:
            self.status_message = result.errors[0]
        else:
            self.status_message = "Invalid solution"

    def _show_exact_solution(self) -> None:
        assert self.instance is not None
        if self.solution is None:
            # Large loaded boards get a longer limit because they can be harder.
            time_limit = 30 if self.instance.rows * self.instance.cols <= 100 else 120
            try:
                candidate = solve_tracks_instance(self.instance, time_limit=time_limit, msg=False)
            except SolverUnavailableError as exc:
                self.status_message = str(exc)
                return
            if candidate.status not in {"optimal", "feasible", "invalid"}:
                self.status_message = f"No solution available: {candidate.status}"
                return
            self.solution = candidate
        self.show_solution = not self.show_solution
        self.status_message = "Showing solution" if self.show_solution else "Showing your board"

    def _cell_at_position(self, position: tuple[int, int]) -> Cell | None:
        assert self.instance is not None
        x, y = position
        layout = self.viewer._build_layout(self.instance)
        if not (
            layout.margin_left <= x < layout.margin_left + layout.board_width
            and layout.margin_top <= y < layout.margin_top + layout.board_height
        ):
            return None

        row = (y - layout.margin_top) // layout.cell_size
        col = (x - layout.margin_left) // layout.cell_size
        cell = (int(row), int(col))
        if cell_in_bounds(cell, self.instance.rows, self.instance.cols):
            return cell
        return None

    def _add_button(self, surface: pygame.Surface, label: str, rect: pygame.Rect, action: str) -> None:
        self.buttons.append(Button(label=label, rect=rect, action=action))
        pygame.draw.rect(surface, (245, 245, 245), rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 2)
        font = pygame.font.Font(None, 26)
        text = font.render(label, True, (0, 0, 0))
        surface.blit(text, text.get_rect(center=rect.center))

    def _home_panel_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        panel_width = min(680, max(320, self.width - 120))
        panel_x = (self.width - panel_width) // 2
        new_game_panel = pygame.Rect(panel_x, 115, panel_width, 250)
        load_map_panel = pygame.Rect(panel_x, 395, panel_width, 245)
        return new_game_panel, load_map_panel

    def _draw_panel(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (255, 255, 255), rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 2)

    def _draw_centered_text(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        center: tuple[int, int],
        *,
        color: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        rendered = font.render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=center))

    def _draw_text(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        position: tuple[int, int],
        *,
        color: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        rendered = font.render(text, True, color)
        surface.blit(rendered, position)

    def _draw_wrapped_text(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        position: tuple[int, int],
        width: int,
    ) -> None:
        x, y = position
        line = ""
        for word in text.split():
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] <= width:
                line = candidate
            else:
                self._draw_text(surface, font, line, (x, y))
                y += font.get_linesize()
                line = word
        if line:
            self._draw_text(surface, font, line, (x, y))


def discover_map_files() -> list[Path]:
    """Return known map files from the project data folders."""
    files: list[Path] = []
    for folder in DATA_FOLDERS:
        if folder.exists():
            files.extend(sorted(folder.glob("*.txt")))
    return files


def allowed_patterns_for_cell(instance: TracksInstance, cell: Cell) -> list[tuple[Direction, ...]]:
    """Return local patterns allowed by fixed hints for one cell."""
    # Fixed hints reduce the list of patterns the player can cycle through.
    if cell in instance.fixed_empty:
        return [EMPTY_PATTERN]
    if cell in instance.fixed_patterns:
        return [instance.fixed_patterns[cell]]

    candidates = list(SINGLE_PATTERNS if cell in {instance.start, instance.end} else PAIR_PATTERNS)
    candidates = [
        normalize_local_pattern(pattern)
        for pattern in candidates
        if _pattern_stays_inside(instance, cell, pattern)
    ]

    required = _required_directions_from_fixed_edges(instance, cell)
    if required:
        candidates = [pattern for pattern in candidates if required.issubset(set(pattern))]

    if cell not in instance.fixed_used and not required and cell not in {instance.start, instance.end}:
        candidates.insert(0, EMPTY_PATTERN)

    return candidates


def _default_pattern_for_cell(instance: TracksInstance, cell: Cell) -> tuple[Direction, ...]:
    allowed = [pattern for pattern in allowed_patterns_for_cell(instance, cell) if pattern]
    return allowed[0] if allowed else EMPTY_PATTERN


def _is_locked_cell(instance: TracksInstance, cell: Cell) -> bool:
    return cell in instance.fixed_empty or cell in instance.fixed_patterns


def _pattern_stays_inside(
    instance: TracksInstance,
    cell: Cell,
    pattern: tuple[Direction, ...],
) -> bool:
    return all(
        cell_in_bounds(neighbor_in_direction(cell, direction), instance.rows, instance.cols)
        for direction in pattern
    )


def _required_directions_from_fixed_edges(instance: TracksInstance, cell: Cell) -> set[Direction]:
    directions: set[Direction] = set()
    for first, second in instance.fixed_edges:
        if cell == first:
            directions.add(_direction_between(first, second))
        elif cell == second:
            directions.add(_direction_between(second, first))
    return directions


def _direction_between(origin: Cell, target: Cell) -> Direction:
    row_delta = target[0] - origin[0]
    col_delta = target[1] - origin[1]
    if row_delta == -1:
        return "U"
    if row_delta == 1:
        return "D"
    if col_delta == -1:
        return "L"
    if col_delta == 1:
        return "R"
    raise ValueError(f"cells {origin} and {target} are not adjacent")


def _direction_endpoint(
    center: tuple[int, int],
    direction: Direction,
    layout: ViewerLayout,
) -> tuple[int, int]:
    center_x, center_y = center
    half_cell = layout.cell_size // 2
    if direction == "U":
        return (center_x, center_y - half_cell)
    if direction == "D":
        return (center_x, center_y + half_cell)
    if direction == "L":
        return (center_x - half_cell, center_y)
    if direction == "R":
        return (center_x + half_cell, center_y)
    raise ValueError(f"invalid direction {direction!r}")


def _shorten_label(label: str, *, max_length: int = 56) -> str:
    if len(label) <= max_length:
        return label
    return f"{label[: max_length - 3]}..."


def _centered_row_x(center_x: int, left_width: int, gap: int, right_width: int) -> int:
    return center_x - (left_width + gap + right_width) // 2


__all__ = [
    "Button",
    "LEGEND_ENTRIES",
    "PlayerBoardState",
    "TracksGame",
    "allowed_patterns_for_cell",
    "discover_map_files",
]
