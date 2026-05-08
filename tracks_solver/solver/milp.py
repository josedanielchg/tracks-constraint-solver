"""MILP model for the Tracks puzzle."""

from __future__ import annotations

from time import perf_counter

from tracks_solver.core import TracksInstance, TracksSolution, build_grid_graph, validate_solution

try:
    import pulp
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    pulp = None


class SolverUnavailableError(RuntimeError):
    """Raised when the MILP backend is not available."""


def solve_tracks_instance(
    instance: TracksInstance,
    *,
    time_limit: float | None = None,
    msg: bool = False,
) -> TracksSolution:
    """Solve a Tracks instance with the flow-based MILP model from the report."""
    if pulp is None:
        raise SolverUnavailableError(
            "PuLP is not installed. Install the 'pulp' package to use the MILP solver."
        )

    # Build the graph objects that match the notation from the report.
    graph = build_grid_graph(instance)
    edge_by_arc = {
        arc: tuple(sorted(arc))
        for arc in graph.arcs
    }
    max_flow = len(graph.cells) - 1

    # The objective is constant because Tracks is solved as a feasibility problem.
    problem = pulp.LpProblem("tracks_feasibility", pulp.LpMinimize)
    # y[cell] says if a grid cell is used by the railway path.
    y = {
        cell: pulp.LpVariable(f"y_{cell[0]}_{cell[1]}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for cell in graph.cells
    }
    # x[edge] says if the path connects two adjacent cells.
    x = {
        edge: pulp.LpVariable(
            f"x_{edge[0][0]}_{edge[0][1]}__{edge[1][0]}_{edge[1][1]}",
            lowBound=0,
            upBound=1,
            cat=pulp.LpBinary,
        )
        for edge in graph.edges
    }
    # f[arc] is only used to prove that every selected cell is connected.
    f = {
        arc: pulp.LpVariable(
            f"f_{arc[0][0]}_{arc[0][1]}__{arc[1][0]}_{arc[1][1]}",
            lowBound=0,
            cat=pulp.LpContinuous,
        )
        for arc in graph.arcs
    }
    problem += 0

    # Row clues count how many cells are used in each row.
    for row in range(instance.rows):
        problem += (
            pulp.lpSum(y[(row, col)] for col in range(instance.cols)) == instance.row_clues[row],
            f"row_clue_{row}",
        )

    # Column clues are the same count, but by column.
    for col in range(instance.cols):
        problem += (
            pulp.lpSum(y[(row, col)] for row in range(instance.rows)) == instance.col_clues[col],
            f"col_clue_{col}",
        )

    # A selected edge cannot enter a cell that is not used.
    for edge in graph.edges:
        first, second = edge
        problem += (x[edge] <= y[first], f"edge_cell_first_{first}_{second}")
        problem += (x[edge] <= y[second], f"edge_cell_second_{first}_{second}")

    # The two terminals are used and have exactly one track connection.
    problem += (y[instance.start] == 1, "start_used")
    problem += (y[instance.end] == 1, "end_used")
    problem += (
        pulp.lpSum(x[edge] for edge in graph.incident_edges[instance.start]) == 1,
        "start_degree",
    )
    problem += (
        pulp.lpSum(x[edge] for edge in graph.incident_edges[instance.end]) == 1,
        "end_degree",
    )

    # Non-terminal cells either have degree 0 or degree 2, so branches are impossible.
    for cell in graph.cells:
        if cell in {instance.start, instance.end}:
            continue
        problem += (
            pulp.lpSum(x[edge] for edge in graph.incident_edges[cell]) == 2 * y[cell],
            f"degree_{cell}",
        )

    # Fixed cells and fixed edges come directly from the puzzle hints.
    for cell in instance.fixed_used:
        problem += (y[cell] == 1, f"fixed_used_{cell}")

    for cell in instance.fixed_empty:
        problem += (y[cell] == 0, f"fixed_empty_{cell}")

    for edge in instance.fixed_edges:
        problem += (x[edge] == 1, f"fixed_edge_{edge}")

    # Flow can only move through edges that are selected by x.
    for arc in graph.arcs:
        problem += (
            f[arc] <= max_flow * x[edge_by_arc[arc]],
            f"flow_capacity_{arc}",
        )

    # The source sends one unit of flow to every other used cell.
    source_outgoing = pulp.lpSum(f[(instance.start, neighbor)] for neighbor in graph.neighbors[instance.start])
    source_incoming = pulp.lpSum(f[(neighbor, instance.start)] for neighbor in graph.neighbors[instance.start])
    problem += (
        source_outgoing - source_incoming
        == pulp.lpSum(y[cell] for cell in graph.cells if cell != instance.start),
        "flow_source",
    )

    # Each used non-source cell consumes one unit of flow.
    for cell in graph.cells:
        if cell == instance.start:
            continue
        incoming = pulp.lpSum(f[(neighbor, cell)] for neighbor in graph.neighbors[cell])
        outgoing = pulp.lpSum(f[(cell, neighbor)] for neighbor in graph.neighbors[cell])
        problem += (incoming - outgoing == y[cell], f"flow_balance_{cell}")

    # CBC is the MILP engine that solves the PuLP model.
    solver = pulp.PULP_CBC_CMD(msg=msg, timeLimit=time_limit)
    started_at = perf_counter()
    status_code = problem.solve(solver)
    solve_time = perf_counter() - started_at

    raw_status = pulp.LpStatus.get(status_code, str(status_code))
    mapped_status = _normalize_status(raw_status)
    objective_value = pulp.value(problem.objective)

    # Convert solver variable values back into the project solution object.
    if mapped_status in {"optimal", "feasible"}:
        used_cells = {cell for cell in graph.cells if pulp.value(y[cell]) and pulp.value(y[cell]) > 0.5}
        selected_edges = {
            edge for edge in graph.edges if pulp.value(x[edge]) and pulp.value(x[edge]) > 0.5
        }
    else:
        used_cells = set()
        selected_edges = set()

    solution = TracksSolution(
        used_cells=used_cells,
        selected_edges=selected_edges,
        status=mapped_status,
        solve_time=solve_time,
        objective_value=objective_value,
        metadata={
            "raw_status": raw_status,
            "status_code": status_code,
            "num_variables": len(problem.variables()),
            "num_constraints": len(problem.constraints),
        },
    )

    # The validator checks the extracted route independently from PuLP.
    if mapped_status in {"optimal", "feasible"}:
        validation = validate_solution(instance, solution)
        solution.metadata["validation_passed"] = validation.is_valid
        solution.metadata["validation_errors"] = list(validation.errors)
        if not validation.is_valid:
            solution.status = "invalid"
    else:
        solution.metadata["validation_passed"] = False
        solution.metadata["validation_errors"] = []

    return solution


def _normalize_status(raw_status: str) -> str:
    normalized = raw_status.strip().lower().replace(" ", "_")
    mapping = {
        "optimal": "optimal",
        "integer_feasible": "feasible",
        "infeasible": "infeasible",
        "not_solved": "not_solved",
        "undefined": "undefined",
        "unbounded": "unbounded",
    }
    return mapping.get(normalized, normalized)
