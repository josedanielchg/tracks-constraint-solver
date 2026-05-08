"""Simple black-and-white Pygame viewer for Tracks."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from tracks_solver.core import TracksInstance, TracksSolution


@dataclass(slots=True, frozen=True)
class ViewerLayout:
    """Drawing geometry for a Tracks grid."""

    cell_size: int
    margin_left: int
    margin_top: int
    board_width: int
    board_height: int


class TracksViewer:
    """Draw a Tracks instance and, optionally, a solution."""

    def __init__(self, *, width: int = 900, height: int = 900, clue_margin: int = 90) -> None:
        """Create a viewer with fixed window and clue spacing."""
        self.width = width
        self.height = height
        self.clue_margin = clue_margin
        self.background_color = (255, 255, 255)
        self.fixed_used_cell_color = (255, 244, 181)
        self.fixed_edge_cell_color = (183, 228, 255)
        self.fixed_pattern_cell_color = (203, 186, 255)
        self.fixed_empty_cell_color = (0, 0, 0)
        self.fixed_cell_color = self.fixed_used_cell_color
        self.foreground_color = (0, 0, 0)
        self.track_width = 4

    def render_to_surface(
        self,
        instance: TracksInstance,
        solution: TracksSolution | None = None,
    ) -> pygame.Surface:
        """Render the current state into an off-screen surface."""
        # Rendering to a surface makes the viewer easy to test without opening a window.
        pygame.font.init()
        surface = pygame.Surface((self.width, self.height))
        surface.fill(self.background_color)

        layout = self._build_layout(instance)
        font = pygame.font.Font(None, max(24, layout.cell_size // 2))

        self._draw_clues(surface, instance, layout, font)
        self._draw_grid(surface, instance, layout)
        if solution is not None:
            self._draw_tracks(surface, instance, solution, layout)
        self._draw_terminals(surface, instance, layout, font)
        return surface

    def run(
        self,
        instance: TracksInstance,
        solution: TracksSolution | None = None,
        *,
        solve_fn=None,
    ) -> None:
        """Open a window and let the user inspect the puzzle."""
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tracks Viewer")
        clock = pygame.time.Clock()

        base_solution = solution
        current_solution = solution
        show_solution = solution is not None
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        show_solution = not show_solution
                    elif event.key == pygame.K_r:
                        current_solution = base_solution
                        show_solution = current_solution is not None
                    elif event.key == pygame.K_s and solve_fn is not None:
                        current_solution = solve_fn(instance)
                        if current_solution is not None:
                            base_solution = current_solution
                            show_solution = True

            screen.blit(
                self.render_to_surface(instance, current_solution if show_solution else None),
                (0, 0),
            )
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def _build_layout(self, instance: TracksInstance) -> ViewerLayout:
        """Compute board geometry from the instance size."""
        board_width = self.width - 2 * self.clue_margin
        board_height = self.height - 2 * self.clue_margin
        cell_size = max(20, min(board_width // instance.cols, board_height // instance.rows))
        return ViewerLayout(
            cell_size=cell_size,
            margin_left=self.clue_margin,
            margin_top=self.clue_margin,
            board_width=cell_size * instance.cols,
            board_height=cell_size * instance.rows,
        )

    def _draw_grid(self, surface: pygame.Surface, instance: TracksInstance, layout: ViewerLayout) -> None:
        """Draw fixed backgrounds and grid lines."""
        # Fixed hints are shaded before drawing the grid lines.
        for (row, col), color in self._fixed_cell_colors(instance).items():
            cell_rect = pygame.Rect(
                layout.margin_left + col * layout.cell_size + 1,
                layout.margin_top + row * layout.cell_size + 1,
                layout.cell_size - 1,
                layout.cell_size - 1,
            )
            pygame.draw.rect(surface, color, cell_rect)

        for row in range(instance.rows + 1):
            y = layout.margin_top + row * layout.cell_size
            pygame.draw.line(
                surface,
                self.foreground_color,
                (layout.margin_left, y),
                (layout.margin_left + layout.board_width, y),
                1,
            )

        for col in range(instance.cols + 1):
            x = layout.margin_left + col * layout.cell_size
            pygame.draw.line(
                surface,
                self.foreground_color,
                (x, layout.margin_top),
                (x, layout.margin_top + layout.board_height),
                1,
            )

    def _draw_clues(
        self,
        surface: pygame.Surface,
        instance: TracksInstance,
        layout: ViewerLayout,
        font: pygame.font.Font,
    ) -> None:
        """Draw row and column clues around the board."""
        for row, clue in enumerate(instance.row_clues):
            label = font.render(str(clue), True, self.foreground_color)
            label_rect = label.get_rect()
            label_rect.center = (
                layout.margin_left // 2,
                layout.margin_top + row * layout.cell_size + layout.cell_size // 2,
            )
            surface.blit(label, label_rect)

        for col, clue in enumerate(instance.col_clues):
            label = font.render(str(clue), True, self.foreground_color)
            label_rect = label.get_rect()
            label_rect.center = (
                layout.margin_left + col * layout.cell_size + layout.cell_size // 2,
                layout.margin_top // 2,
            )
            surface.blit(label, label_rect)

    def _draw_terminals(
        self,
        surface: pygame.Surface,
        instance: TracksInstance,
        layout: ViewerLayout,
        font: pygame.font.Font,
    ) -> None:
        """Draw the start and end terminal labels."""
        for cell, label_text in ((instance.start, "A"), (instance.end, "B")):
            center = self._cell_center(cell, layout)
            label = font.render(label_text, True, self.foreground_color)
            label_rect = label.get_rect(center=center)
            surface.blit(label, label_rect)

    def _draw_tracks(
        self,
        surface: pygame.Surface,
        instance: TracksInstance,
        solution: TracksSolution,
        layout: ViewerLayout,
    ) -> None:
        """Draw all selected track segments from a solution."""
        # Tracks are drawn from the center of a cell to the selected neighboring cells.
        for cell in solution.used_cells:
            center = self._cell_center(cell, layout)
            for endpoint in self._track_endpoints(cell, solution, layout):
                pygame.draw.line(
                    surface,
                    self.foreground_color,
                    center,
                    endpoint,
                    self.track_width,
                )

    def _track_endpoints(
        self,
        cell: tuple[int, int],
        solution: TracksSolution,
        layout: ViewerLayout,
    ) -> list[tuple[int, int]]:
        """Return drawing endpoints for the selected edges touching a cell."""
        row, col = cell
        center_x, center_y = self._cell_center(cell, layout)
        endpoints: list[tuple[int, int]] = []

        for first, second in solution.selected_edges:
            if cell == first:
                neighbor = second
            elif cell == second:
                neighbor = first
            else:
                continue

            row_delta = neighbor[0] - row
            col_delta = neighbor[1] - col
            if row_delta == -1:
                endpoints.append((center_x, center_y - layout.cell_size // 2))
            elif row_delta == 1:
                endpoints.append((center_x, center_y + layout.cell_size // 2))
            elif col_delta == -1:
                endpoints.append((center_x - layout.cell_size // 2, center_y))
            elif col_delta == 1:
                endpoints.append((center_x + layout.cell_size // 2, center_y))

        return endpoints

    def _fixed_cells(self, instance: TracksInstance) -> set[tuple[int, int]]:
        """Return cells that have any fixed visual background."""
        return set(self._fixed_cell_colors(instance))

    def _fixed_cell_colors(self, instance: TracksInstance) -> dict[tuple[int, int], tuple[int, int, int]]:
        """Return the display color of each fixed cell."""
        colors: dict[tuple[int, int], tuple[int, int, int]] = {}

        # More specific fixed hints override the simpler fixed-used color.
        for cell in instance.fixed_used:
            colors[cell] = self.fixed_used_cell_color
        for cell in instance.fixed_empty:
            colors[cell] = self.fixed_empty_cell_color
        for first, second in instance.fixed_edges:
            colors.setdefault(first, self.fixed_edge_cell_color)
            colors.setdefault(second, self.fixed_edge_cell_color)
        for cell in instance.fixed_patterns:
            colors[cell] = self.fixed_pattern_cell_color

        return colors

    def _cell_center(self, cell: tuple[int, int], layout: ViewerLayout) -> tuple[int, int]:
        """Return the pixel center of a grid cell."""
        row, col = cell
        return (
            layout.margin_left + col * layout.cell_size + layout.cell_size // 2,
            layout.margin_top + row * layout.cell_size + layout.cell_size // 2,
        )
