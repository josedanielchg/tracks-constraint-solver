# Validation, Testing, and Results

Why this matters:

Optimization projects often fail in a subtle way: the solver returns something that looks plausible
but does not actually satisfy the intended model. This page explains how the project protects
itself against that failure mode.

## 1. Why Validation Is a Separate Layer

The project intentionally separates:

- **solving**
- **validating**

The solver answers:

> "Can the MILP backend find a candidate solution?"

The validator answers:

> "Does this candidate solution really satisfy the Tracks rules and the intended semantics of the model?"

Keeping these two layers separate is good engineering and good defense material. It shows that the
team does not blindly trust the solver output.

## 2. What the Validator Checks

Main module:

- `tracks_solver/core/validation.py`

Main function:

- `validate_solution(instance, solution)`

The validator checks:

### Terminal rules

- the start is used;
- the end is used;
- each terminal has degree 1.

### Clue rules

- every row uses exactly the required number of cells;
- every column uses exactly the required number of cells.

### Edge-cell consistency

- every selected edge connects two used cells;
- selected edges are known graph edges.

### Degree rules

- each used non-terminal cell has degree 2;
- each unused cell has degree 0.

### Fixed information

- `fixed_used` cells are used;
- `fixed_empty` cells are empty;
- `fixed_edges` are selected;
- `fixed_patterns` match the exact local incident-edge set.

### Connectivity

- all used cells are reachable from the start through selected edges.

### Global size consistency

- `|selected_edges| = |used_cells| - 1`

This is a compact way to reinforce the fact that the selected structure must behave like a single
path rather than a disconnected forest or a graph with extra cycles.

## 3. What Can Go Wrong

The validator and the test suite are designed around realistic failure modes.

### Disconnected components

The solution may satisfy clue counts and local degrees but still contain more than one connected
component.

### Isolated loops

This is a special case of disconnectedness:

- one valid path from `A` to `B`;
- one extra cycle somewhere else.

### Wrong clue counts

A solver or parser bug may produce a structure whose row or column usage does not match the input
clues.

### Branching

A used cell may accidentally have degree 3 or more, which violates the route interpretation.

### Inconsistent fixed hints

The instance may demand impossible combinations, such as:

- a fixed edge touching a cell forced empty;
- a local pattern pointing outside the grid;
- contradictory fixed data on the same cell.

### Visually plausible but invalid solutions

This is exactly why the validator exists. Human inspection is useful, but not sufficient.

## 4. Test Categories in the Project

The test suite mirrors the project structure.

### Parser tests

These verify that:

- valid instances are parsed correctly;
- malformed instances are rejected with explicit errors.

Typical cases:

- missing required fields;
- wrong clue lengths;
- out-of-bounds coordinates;
- invalid fixed hints.

### Graph tests

These verify structural correctness of:

- cell counts;
- edge counts;
- neighbor sets;
- incident-edge sets;
- directed arc counts.

These tests are especially useful because they connect directly to the graph notation from the
report.

### Validation tests

These feed small hand-built solutions to the validator and check that it:

- accepts correct paths;
- rejects disconnected or branched structures;
- rejects clue mismatches;
- rejects fixed-clue violations.

### Solver tests

These check that:

- the MILP solver finds a valid solution on a small solvable instance;
- the MILP solver reports infeasibility on a contradictory instance;
- feasible solver outputs pass the independent validator.

### Generation tests

These verify that:

- generated instances serialize correctly;
- generated instances can be parsed again;
- generated instances are solvable.

### Pygame smoke tests

These confirm that:

- the viewer can render one frame without raising exceptions;
- fixed cells receive the intended background shading.

## 5. Why This Testing Strategy Is Strong

The tests do not only check end-to-end success. They check the boundaries between conceptual
layers:

- parser versus file format;
- graph representation versus report notation;
- solver output versus validator semantics;
- viewer output versus rendering assumptions.

This is a better strategy than relying only on one large end-to-end test, because it localizes
errors more precisely.

## 6. Dataset Results and Experiment Support

Main module:

- `tracks_solver/solver/solve_dataset.py`

This module solves every `.txt` instance in a directory and writes a CSV summary.

The CSV contains fields such as:

- `instance_name`
- `rows`
- `cols`
- `num_cells`
- `num_used_cells`
- `status`
- `is_feasible`
- `solve_time`
- `objective_value`
- `validator_passed`
- `error`

This matters for the report and the defense because it supports:

- runtime comparisons;
- instance-size analysis;
- debugging of difficult maps;
- future experimental tables and plots.

## 7. Why This Matters in the Defense

In an oral defense, saying "the solver works" is weak.

A stronger answer is:

1. the solver encodes the mathematical model;
2. the validator checks the semantics independently;
3. the test suite covers parsing, graph construction, solving, rendering, and generation;
4. dataset runs produce reusable empirical results.

This shows rigor rather than blind optimism.

## Key Takeaways

- The validator is a second line of defense after the MILP solver.
- The test suite is organized by subsystem, not only by end-to-end scenarios.
- Common failure modes are known and explicitly tested.
- Dataset result files turn the project into an experimental platform, not just a one-instance demo.

The last step is to convert all this material into defense-ready explanations.

Next: [Defense Preparation](07_defense_prep.md)
