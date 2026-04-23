# Tracks Implementation Plan

This guide explains how to implement the mathematical model from the report as Python code.
It is intentionally written step by step. The goal is that a teammate can read this document
and understand exactly what must be built, in which order, and why each part exists.

The project has two main parts:

1. the logic layer, which reads instances, builds the graph, validates solutions, and solves the
   MILP model;
2. the visual layer, which uses Pygame to display the grid, clues, terminals, and final track.

The logic layer must be implemented first. Pygame should only display data that has already been
computed and validated by the core code.

---

## 1. Purpose of This Guide

The report describes Tracks as a graph-based feasibility problem. In the report, the grid becomes
a graph \(G=(V,E)\), where:

- \(V\) is the set of cells;
- \(E\) is the set of possible edges between orthogonally adjacent cells;
- \(y_v\) says whether a cell \(v\) is used by the track;
- \(x_e\) says whether an edge \(e\) is selected as a track connection;
- \(f_{uv}\) is an auxiliary flow variable used to force connectivity.

This guide translates that mathematical description into concrete Python modules.

The basic idea is simple:

1. read a Tracks instance from a file;
2. convert the grid into graph objects;
3. create a MILP model with the same variables and constraints as the report;
4. solve the model;
5. validate the solution independently;
6. display the instance and the solution in text and in Pygame.

The implementation should stay close to the report. This makes the code easier to explain in the
final presentation, because every important line of the solver corresponds to a mathematical rule.

---

## 2. Target Architecture

The repository already has a Python package named `tracks_solver`. We should keep using this
package. Do not create a new `src/` directory unless the whole project is later reorganized.

Recommended structure:

```text
tracks_solver/
  core/
    models.py
    parser.py
    graph.py
    validation.py
    display_ascii.py

  solver/
    __init__.py
    milp.py
    solve_instance.py
    solve_dataset.py

  generation/
    __init__.py
    generate_instance.py
    generate_dataset.py

  ui/
    __init__.py
    pygame_viewer.py

  main.py
```

Recommended data folders:

```text
data/
  tracks/
    manual/
      small_4x4.txt
      small_5x5.txt
    generated/
    datasets/

res/
  tracks/
    solutions/
    datasets/
    screenshots/
```

What each area is for:

- `tracks_solver/core/`: pure puzzle logic, with no solver-specific or Pygame-specific code.
- `tracks_solver/solver/`: MILP model construction and solver calls.
- `tracks_solver/generation/`: random instance generation.
- `tracks_solver/ui/`: Pygame visualization only.
- `tests/`: small tests that prove each part works.

The most important rule is separation of responsibilities. The Pygame interface must not decide
whether a solution is valid. The solver must not know how to draw a track. The parser must not solve
anything. Each module should do one job.

---

## 3. Core Data Model

The data model should be small and explicit. Use normal Python types and dataclasses.

### Basic aliases

Use these conceptual types:

```python
Cell = tuple[int, int]
Edge = tuple[Cell, Cell]
```

A `Cell` is a pair `(row, col)`. Use zero-based indexing in code:

- first row is `0`;
- first column is `0`;
- last row is `rows - 1`;
- last column is `cols - 1`.

This is different from the report, where indices are written mathematically as
\(1,\dots,m\) and \(1,\dots,n\). That is normal: math notation is one-based, Python lists are
zero-based. The parser and display should consistently use zero-based indexing internally.

An `Edge` is a pair of neighboring cells. To avoid duplicates, store every undirected edge in a
canonical order:

```text
((row1, col1), (row2, col2))
```

with the smaller cell first in lexicographic order. This prevents the same edge from appearing once
as `(a, b)` and once as `(b, a)`.

### TracksInstance

`TracksInstance` represents the input puzzle before solving.

Fields:

- `rows: int`
  - number of rows in the grid;
- `cols: int`
  - number of columns in the grid;
- `start: Cell`
  - start terminal, called \(s\) in the report;
- `end: Cell`
  - end terminal, called \(t\) in the report;
- `row_clues: list[int]`
  - row clues \(\rho_i\);
- `col_clues: list[int]`
  - column clues \(\gamma_j\);
- `fixed_used: set[Cell]`
  - cells forced to contain track;
- `fixed_empty: set[Cell]`
  - cells forced to stay empty;
- `fixed_edges: set[Edge]`
  - track connections forced by pre-filled pieces.

Beginner interpretation:

- `row_clues` and `col_clues` say how many cells must be used.
- `fixed_used` and `fixed_empty` say what is already known.
- `fixed_edges` says which neighboring cells must be connected.

### TracksSolution

`TracksSolution` represents the solver output.

Fields:

- `used_cells: set[Cell]`
  - all cells with \(y_v=1\);
- `selected_edges: set[Edge]`
  - all edges with \(x_e=1\);
- `status: str`
  - solver status, for example `optimal`, `feasible`, `infeasible`, or `timeout`;
- `solve_time: float`
  - total solve time in seconds;
- `objective_value: float | None`
  - normally `0`, because this is a feasibility model;
- `metadata: dict[str, object]`
  - optional solver details.

The solution object should not contain Pygame objects, colors, surfaces, or UI state. It is pure data.

---

## 4. Instance File Format

Use a simple text format that is easy to read manually and easy to parse.

Example:

```text
rows=5
cols=5
start=0,0
end=4,4
row_clues=2,3,2,3,2
col_clues=1,3,3,3,2
fixed_used=0,0;4,4
fixed_empty=2,2
fixed_edges=0,0-0,1;4,3-4,4
```

Meaning:

- `rows=5`: the grid has 5 rows;
- `cols=5`: the grid has 5 columns;
- `start=0,0`: the start terminal is cell `(0, 0)`;
- `end=4,4`: the end terminal is cell `(4, 4)`;
- `row_clues=2,3,2,3,2`: row 0 uses 2 cells, row 1 uses 3 cells, etc.;
- `col_clues=1,3,3,3,2`: column 0 uses 1 cell, column 1 uses 3 cells, etc.;
- `fixed_used=0,0;4,4`: these cells must contain track;
- `fixed_empty=2,2`: this cell must be empty;
- `fixed_edges=0,0-0,1;4,3-4,4`: these connections are pre-filled.

Optional fields:

- `fixed_used`
- `fixed_empty`
- `fixed_edges`

If an optional field is missing, treat it as empty.

Parser validation rules:

1. `rows` and `cols` must be positive.
2. `start` and `end` must be inside the grid.
3. `start != end`.
4. `len(row_clues) == rows`.
5. `len(col_clues) == cols`.
6. `sum(row_clues) == sum(col_clues)`.
7. Every fixed cell must be inside the grid.
8. No cell can be both fixed used and fixed empty.
9. Every fixed edge must connect two orthogonally adjacent cells.
10. Every fixed edge must be inside the grid.
11. Start and end should be automatically added to `fixed_used`.

Do not silently ignore invalid input. If an instance is malformed, raise a clear exception with a
message that tells the user what is wrong.

---

## 5. Graph Construction

The graph module translates the grid into the notation used in the report.

For an instance with `rows = m` and `cols = n`, build:

- `V`: all cells;
- `E_h`: horizontal edges;
- `E_v`: vertical edges;
- `E`: all edges;
- `neighbors[cell]`: cells adjacent to `cell`;
- `incident_edges[cell]`: all edges touching `cell`;
- `A`: directed arcs used for flow variables.

### Cells \(V\)

In code:

```text
V = all (row, col) such that:
    0 <= row < rows
    0 <= col < cols
```

This corresponds to \(V = R \times C\) in the report.

### Horizontal edges \(E^H\)

For each row, connect each cell to the cell immediately on its right:

```text
((row, col), (row, col + 1))
```

for `0 <= col < cols - 1`.

### Vertical edges \(E^V\)

For each column, connect each cell to the cell immediately below it:

```text
((row, col), (row + 1, col))
```

for `0 <= row < rows - 1`.

### Neighbors \(N(v)\)

For a cell `v`, `neighbors[v]` is the set of cells that can be reached in one step:

- up;
- down;
- left;
- right;

only if those cells are inside the grid.

### Incident edges \(\delta(v)\)

For a cell `v`, `incident_edges[v]` is the set of all edges containing `v`.

This is used directly in degree constraints:

```text
sum x[e] for e in incident_edges[v]
```

### Directed arcs \(A\)

For every undirected edge `{u, v}`, create two directed arcs:

```text
(u, v)
(v, u)
```

These arcs are used for the flow variables `f[u, v]`.

Beginner interpretation:

- edges describe track connections;
- arcs describe possible directions for the artificial flow;
- the flow is only a mathematical trick for proving that the selected track is connected.

---

## 6. Validator Before Solver

Build the validator before the MILP solver. This is important because it gives an independent way
to check if a candidate solution is actually valid.

The validator should receive:

- a `TracksInstance`;
- a `TracksSolution`.

It should return either:

- `True` if the solution is valid; or
- a list of errors explaining what failed.

Recommended checks:

### 1. Terminal checks

Verify:

- `start` is in `used_cells`;
- `end` is in `used_cells`;
- `start` has exactly one selected incident edge;
- `end` has exactly one selected incident edge.

This matches the report's terminal degree constraints.

### 2. Row and column counts

For each row:

```text
number of used cells in row == row_clues[row]
```

For each column:

```text
number of used cells in column == col_clues[col]
```

This checks the clue constraints.

### 3. Edge-cell consistency

For each selected edge `(u, v)`:

- `u` must be in `used_cells`;
- `v` must be in `used_cells`;
- `u` and `v` must be orthogonally adjacent.

This checks that the solution does not connect empty cells.

### 4. Degree checks

For every used cell:

- if the cell is `start` or `end`, degree must be `1`;
- otherwise, degree must be `2`.

For every unused cell:

- degree must be `0`.

This prevents branches, crossings, and isolated used cells.

### 5. Fixed information checks

Verify:

- every cell in `fixed_used` is used;
- every cell in `fixed_empty` is not used;
- every edge in `fixed_edges` is selected.

### 6. Connectivity check

Run BFS or DFS from `start` using only `selected_edges`.

The visited set must be exactly `used_cells`.

If some used cell is not visited, then the solution contains a disconnected component.

### 7. Extra cycle or extra component check

If all degree checks and connectivity checks pass, then an extra disconnected cycle cannot exist.
Still, the validator should report this explicitly:

- if connectivity fails, say "disconnected component or isolated loop detected";
- if degree fails, say which cell has the wrong degree.

The validator is the best debugging tool for the solver. Whenever the solver returns a solution,
run the validator before displaying it.

---

## 7. MILP Solver Implementation

Use PuLP as the first MILP implementation. It is simple to install and good enough for a first
academic version. Later, the same model can be translated to docplex if CPLEX is required.

The solver should expose one main function:

```text
solve_tracks_instance(instance) -> TracksSolution
```

Internally, it should build the same model as the report.

### 7.1 Create the model

Create a minimization model with objective `0`.

This is a feasibility model. The solver is not trying to find the shortest path or the cheapest
path. It is trying to find any solution satisfying all constraints.

### 7.2 Create cell variables \(y_v\)

For each cell `v` in `V`, create a binary variable:

```text
y[v] in {0, 1}
```

Meaning:

- `y[v] = 1`: cell `v` contains track;
- `y[v] = 0`: cell `v` is empty.

### 7.3 Create edge variables \(x_e\)

For each undirected edge `e` in `E`, create a binary variable:

```text
x[e] in {0, 1}
```

Meaning:

- `x[e] = 1`: the connection is selected;
- `x[e] = 0`: the connection is not selected.

### 7.4 Create flow variables \(f_{uv}\)

For each directed arc `(u, v)` in `A`, create a continuous nonnegative variable:

```text
f[u, v] >= 0
```

Meaning:

- this is artificial flow used to prove connectivity;
- it does not represent a real train.

### 7.5 Add row clue constraints

For each row:

```text
sum y[row, col] over all columns == row_clues[row]
```

This is the code version of:

\[
\sum_{j \in C} y_{(i,j)} = \rho_i.
\]

### 7.6 Add column clue constraints

For each column:

```text
sum y[row, col] over all rows == col_clues[col]
```

This is the code version of:

\[
\sum_{i \in R} y_{(i,j)} = \gamma_j.
\]

### 7.7 Add edge-cell consistency constraints

For each edge `e = (u, v)`:

```text
x[e] <= y[u]
x[e] <= y[v]
```

This prevents selecting an edge connected to an empty cell.

### 7.8 Add terminal constraints

Force the start and end cells to be used:

```text
y[start] == 1
y[end] == 1
```

Force the terminal degrees:

```text
sum x[e] for e incident to start == 1
sum x[e] for e incident to end == 1
```

This makes `start` and `end` the endpoints of the path.

### 7.9 Add internal degree constraints

For every cell that is not a terminal:

```text
sum x[e] for e incident to cell == 2 * y[cell]
```

If the cell is empty, the right side is zero, so no incident edge can be selected.

If the cell is used, the right side is two, so exactly two track connections must touch it.

This is what prevents branches.

### 7.10 Add fixed information constraints

For every cell in `fixed_used`:

```text
y[cell] == 1
```

For every cell in `fixed_empty`:

```text
y[cell] == 0
```

For every edge in `fixed_edges`:

```text
x[edge] == 1
```

If later the instance format supports complete fixed piece patterns, add constraints that force all
non-pattern incident edges to `0`.

### 7.11 Add flow capacity constraints

Let:

```text
M = rows * cols - 1
```

For every arc `(u, v)`:

```text
0 <= f[u, v] <= M * x[edge(u, v)]
```

This means flow can only pass through selected track edges.

### 7.12 Add source flow constraint

At the start terminal:

```text
outgoing_flow(start) - incoming_flow(start)
    == sum y[v] for every v != start
```

The start sends one unit of flow to every other used cell.

### 7.13 Add flow balance constraints

For every cell `v != start`:

```text
incoming_flow(v) - outgoing_flow(v) == y[v]
```

If `v` is used, it consumes one unit of flow.

If `v` is empty, it consumes zero.

This forces every used cell to be reachable from `start`.

### 7.14 Solve and extract the solution

After solving:

1. read all variables `y[v]`;
2. put every cell with `y[v] = 1` into `used_cells`;
3. read all variables `x[e]`;
4. put every edge with `x[e] = 1` into `selected_edges`;
5. build a `TracksSolution`;
6. run the validator;
7. return the solution and metadata.

If the model is infeasible, return a solution object with empty sets and status `infeasible`.

---

## 8. Console Display

Before using Pygame, create a simple text display. This is faster to debug.

The console display should show:

- the grid;
- row clues;
- column clues;
- start and end terminals;
- optionally the solved track.

Suggested characters:

```text
.  empty cell
A  start terminal
B  end terminal
-  horizontal track
|  vertical track
+  curve or generic track turn
?  unknown track shape
```

How to determine the shape of a used cell:

1. find all selected incident edges of the cell;
2. convert those edges into directions: up, down, left, right;
3. choose the display character:
   - left + right -> `-`;
   - up + down -> `|`;
   - one vertical + one horizontal -> `+`;
   - one edge at a terminal -> `A` or `B`;
   - anything unexpected -> `?`.

This ASCII display should be used in tests and debugging logs.

---

## 9. Pygame Interface

Pygame should be a visual layer over the existing data model. It should not duplicate solver logic.

The Pygame viewer should receive:

- a `TracksInstance`;
- optionally a `TracksSolution`.

Minimum visual features:

1. draw the grid;
2. draw row clues on the right or left of rows;
3. draw column clues above or below columns;
4. draw the start terminal with label `A`;
5. draw the end terminal with label `B`;
6. draw selected track edges from the solution;
7. draw straight pieces and turns clearly.

Recommended layout:

- reserve a margin for row and column clues;
- compute `cell_size` from the window size and grid dimensions;
- draw grid lines first;
- draw clues second;
- draw tracks third;
- draw terminal labels last.

Track drawing rules:

- for each used cell, find its selected incident edges;
- draw a line from the center of the cell to the side of each selected edge;
- this automatically creates straight pieces, turns, and terminal half-pieces.

Basic controls:

- `Esc`: close the window;
- `R`: reload the current instance;
- `S`: solve and display solution, if solver is connected;
- `Space`: toggle between instance-only view and solution view.

Keep the first Pygame version simple. Do not add animations until the static display works.

---

## 10. Instance Generation

Generating valid Tracks instances is easier if we generate a valid path first.

Bad approach:

1. randomly choose row clues and column clues;
2. hope that a solution exists.

This usually creates many impossible instances.

Good approach:

1. choose `rows` and `cols`;
2. choose start and end cells;
3. generate a simple path from start to end;
4. compute row clues from the path;
5. compute column clues from the path;
6. optionally keep a few fixed cells or fixed edges as hints;
7. save the instance.

The generated instance is guaranteed to have at least one solution: the path used to create it.

The instance does not need to have a unique solution unless the course later requires uniqueness.

Simple generation strategy:

- start at `start`;
- repeatedly move to a random unvisited neighbor;
- stop when `end` is reached;
- if stuck, restart;
- reject paths that are too short or too trivial.

Later improvements:

- control path length;
- control number of turns;
- generate larger datasets;
- test uniqueness by solving again with a no-good cut.

---

## 11. Dataset Solving and Results

Dataset solving means running the solver on many instances and saving performance data.

Input:

```text
data/tracks/datasets/<dataset_name>/
```

Output:

```text
res/tracks/datasets/<dataset_name>_results.csv
```

Each result row should contain:

- `instance_name`;
- `rows`;
- `cols`;
- `num_cells`;
- `num_used_cells`;
- `status`;
- `is_feasible`;
- `solve_time`;
- `objective_value`;
- `validator_passed`;
- optional solver metadata.

Recommended workflow:

1. list all instance files in a dataset folder;
2. parse each instance;
3. solve it;
4. validate the solution if feasible;
5. save one row of results;
6. continue even if one instance fails, but record the error.

The final report can use this data to create tables and plots.

---

## 12. Testing Strategy

Tests should be added gradually. Do not wait until the whole solver is finished.

### Parser tests

Test that:

- a valid small instance is parsed correctly;
- missing required fields are rejected;
- wrong row clue length is rejected;
- wrong column clue length is rejected;
- start outside the grid is rejected;
- fixed edge between non-neighbor cells is rejected.

### Graph construction tests

For a `2x2` grid:

- there should be 4 cells;
- there should be 4 undirected edges;
- each corner should have 2 neighbors.

For a `3x3` grid:

- the center cell should have 4 neighbors;
- corner cells should have 2 neighbors;
- side non-corner cells should have 3 neighbors.

### Validator tests

Test:

- a valid tiny path;
- a disconnected solution;
- a solution with a branch;
- a solution with wrong row clues;
- a solution with wrong column clues;
- a solution that violates fixed cells.

### Solver tests

Test:

- one small solvable instance;
- one small infeasible instance;
- solver output passes the validator;
- status is correctly reported.

### Generation tests

Test:

- generated instances parse successfully;
- generated clues match the generated path;
- generated instance has at least one feasible solution.

### Pygame smoke test

The Pygame test should not require manual interaction.

Possible approach:

- initialize Pygame with a dummy video driver;
- create the viewer;
- draw one frame;
- assert that no exception is raised;
- close Pygame.

This proves that the UI can start in automated test environments.

---

## 13. Suggested Development Order

### Sprint 1: Core data and parsing

Goal: read a Tracks instance and represent it in memory.

Tasks:

1. create `tracks_solver/core/models.py`;
2. define `Cell`, `Edge`, `TracksInstance`, and `TracksSolution`;
3. create `tracks_solver/core/parser.py`;
4. implement parsing for the text format;
5. add parser validation;
6. create one manual instance in `data/tracks/manual/`;
7. add parser tests.

Definition of done:

- the manual instance can be parsed;
- invalid files fail with clear errors;
- parser tests pass.

### Sprint 2: Graph helpers and validator

Goal: build the grid graph and validate candidate solutions.

Tasks:

1. create `tracks_solver/core/graph.py`;
2. implement cells, edges, neighbors, incident edges, and arcs;
3. create `tracks_solver/core/validation.py`;
4. implement terminal checks;
5. implement row and column count checks;
6. implement degree checks;
7. implement BFS/DFS connectivity check;
8. add graph and validator tests.

Definition of done:

- graph helpers match expected counts on small grids;
- validator accepts a correct tiny solution;
- validator rejects disconnected or branched solutions.

### Sprint 3: MILP solver

Goal: implement the mathematical model from the report.

Tasks:

1. add PuLP to `requirements.txt`;
2. create `tracks_solver/solver/milp.py`;
3. build variables `y`, `x`, and `f`;
4. add row and column constraints;
5. add edge-cell consistency constraints;
6. add terminal and degree constraints;
7. add fixed information constraints;
8. add flow connectivity constraints;
9. solve a small manual instance;
10. validate solver output.

Definition of done:

- solver finds a valid solution on a small instance;
- solver reports infeasible on a contradictory instance;
- every feasible solver output passes the independent validator.

### Sprint 4: Display and Pygame

Goal: make solutions visible.

Tasks:

1. implement ASCII display;
2. implement Pygame grid drawing;
3. draw row and column clues;
4. draw start and end terminals;
5. draw selected track edges;
6. add basic keyboard controls;
7. add a Pygame smoke test.

Definition of done:

- a solved instance can be displayed in the terminal;
- the same instance can be displayed in a Pygame window;
- the Pygame viewer does not contain solver logic.

### Sprint 5: Generation, datasets, and experiments

Goal: prepare final project results.

Tasks:

1. implement path-based random generation;
2. save generated instances;
3. solve folders of instances;
4. save CSV or JSON results;
5. collect solve times;
6. create tables or plots for the final report.

Definition of done:

- a dataset can be generated automatically;
- the solver can run on the dataset;
- results are saved in a reusable format;
- the final report can use the collected data.

---

## Final Implementation Rule

Always keep the report, the code, and the tests aligned.

If the code adds a constraint, the report should be able to explain it.
If the report states a rule, the validator should check it.
If the solver returns a solution, the validator should confirm it before the UI displays it.

This avoids the most common project failure: having a solver that produces something that looks
correct visually but does not actually satisfy the mathematical model.
