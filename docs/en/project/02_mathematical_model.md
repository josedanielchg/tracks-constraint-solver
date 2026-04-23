# Mathematical Model

Why this matters:

The report gives the formal MILP model. This page explains the same model in documentation form so
that a reader can move from notation to meaning to implementation without treating the equations as
isolated symbols.

For the formal LaTeX version, see:
- [English mathematical model in the report](../../../report/sections/02_mathematical_model.tex)

## 1. Problem Statement

We consider a Tracks instance on an \(m \times n\) grid. Two special cells are prescribed:

- a start terminal \(s\);
- an end terminal \(t\).

The goal is not to minimize a cost. The goal is to decide whether there exists a valid railway
route from \(s\) to \(t\) that satisfies:

- row and column clues;
- local track consistency;
- absence of branching;
- absence of disconnected components or extra loops;
- all fixed information provided in the instance.

This is therefore a **feasibility problem**. In standard MILP form, it is written with the dummy
objective:

```text
min 0
```

The objective is only a technical wrapper. The real content is entirely in the constraints.

## 2. Sets, Indices, and Parameters

The report uses the following notation:

- \(R = \{1,\dots,m\}\): set of row indices
- \(C = \{1,\dots,n\}\): set of column indices
- \(V = R \times C\): set of cells
- \(E = E^H \cup E^V\): set of admissible undirected edges between orthogonally adjacent cells

The horizontal and vertical edge subsets are:

```text
E^H = { {(i,j),(i,j+1)} }
E^V = { {(i,j),(i+1,j)} }
```

For a vertex \(v\):

- \(N(v)\): neighbors of \(v\)
- \(\delta(v)\): edges incident to \(v\)

The terminals are:

- \(s \in V\)
- \(t \in V\)

The clue parameters are:

- \(\rho_i\): row clue for row \(i\)
- \(\gamma_j\): column clue for column \(j\)

Fixed-information sets:

- \(V^+\): cells forced to be used
- \(V^-\): cells forced to be empty
- \(\mathcal{P}\): cells whose local pattern is prescribed
- \(P_v\): prescribed incident edges at \(v \in \mathcal{P}\)

The necessary consistency condition is:

```text
sum_i rho_i = sum_j gamma_j
```

because both sides count the total number of used cells.

## 3. Decision Variables

The model uses three families of variables.

### Cell variables

For each cell \(v \in V\):

```text
y_v = 1 if cell v is used
y_v = 0 otherwise
```

These variables express row and column clues naturally.

### Edge variables

For each admissible undirected edge \(e \in E\):

```text
x_e = 1 if edge e is selected in the railway
x_e = 0 otherwise
```

These variables express the geometry of the route.

### Flow variables

To enforce connectedness, the model uses directed arcs:

```text
A = {(u,v) : {u,v} in E}
```

and for each arc \((u,v)\):

```text
f_uv >= 0
```

This flow does not represent a physical train. It is an auxiliary mathematical device ensuring
that every selected cell can be reached from the source.

## 4. Constraint Families

### 4.1 Row and column count constraints

For every row \(i\):

```text
sum_j y_(i,j) = rho_i
```

For every column \(j\):

```text
sum_i y_(i,j) = gamma_j
```

Plain-English meaning:

- each row must contain exactly the required number of used cells;
- each column must contain exactly the required number of used cells.

These are the direct translations of the puzzle clues.

### 4.2 Edge-cell consistency

For every undirected edge \(\{u,v\} \in E\):

```text
x_{u,v} <= y_u
x_{u,v} <= y_v
```

Plain-English meaning:

- if an edge is selected, both endpoint cells must be used;
- a connection cannot go into an empty cell.

This is a standard compatibility block between node-selection and edge-selection variables.

### 4.3 Terminal constraints

The terminals must be used:

```text
y_s = 1
y_t = 1
```

Their selected degree must be exactly one:

```text
sum_{e in delta(s)} x_e = 1
sum_{e in delta(t)} x_e = 1
```

Plain-English meaning:

- the start and end cells are the two endpoints of the route;
- they have exactly one track connection each.

### 4.4 Internal degree constraints

For every non-terminal cell \(v\):

```text
sum_{e in delta(v)} x_e = 2 y_v
```

Plain-English meaning:

- if the cell is unused, its degree is zero;
- if the cell is used, its degree is exactly two.

This enforces local route continuity and prevents branching.

### 4.5 Fixed information

If a cell is forced to be used:

```text
y_v = 1
```

If a cell is forced to be empty:

```text
y_v = 0
```

If a local pattern is prescribed, then:

```text
x_e = 1 for edges that belong to the pattern
x_e = 0 for incident edges that do not belong to the pattern
```

Plain-English meaning:

- fixed clues are encoded as hard constraints, not as preferences;
- a fully known clue cell behaves like a small local certificate of geometry.

### 4.6 Flow-based connectivity

Let \(M = |V| - 1\). For each arc \((u,v)\):

```text
0 <= f_uv <= M x_{u,v}
```

This means flow can use an arc only if the underlying undirected edge is selected.

At the source:

```text
outgoing(s) - incoming(s) = sum_{v != s} y_v
```

At every other vertex \(v \neq s\):

```text
incoming(v) - outgoing(v) = y_v
```

Plain-English meaning:

- the source sends one unit of flow to each other used cell;
- every used cell must absorb one unit;
- therefore every used cell must be reachable from the source through selected edges.

## 5. Why Degree Constraints Alone Are Not Enough

This is one of the most important ideas of the whole project.

Suppose the model contains:

- row and column clue constraints;
- edge-cell consistency;
- degree constraints.

Then an invalid configuration can still appear:

- one valid path from \(s\) to \(t\);
- one extra disconnected cycle somewhere else.

Why does this happen?

Because every cell in that disconnected cycle still has degree 2, so the local constraints are all
satisfied. The failure is global, not local.

That is why the model needs a connectivity formulation in addition to degree constraints.

## 6. Why the Flow Formulation Removes Disconnected Loops

The flow formulation works by contradiction.

Suppose a disconnected component exists and does not contain the source \(s\).
Then:

- no flow can enter that component, because flow is limited to selected edges;
- but each used cell in that component requires one unit of net inflow.

These two facts are incompatible.

Therefore, every used cell must lie in the same connected component as the source.
Combined with the degree conditions, this excludes:

- disconnected paths;
- isolated loops;
- detached fragments;
- branches.

## 7. Alternative Connectivity Formulations

The project uses a single-commodity flow formulation because it is explicit, rigorous, and easy to
map into code. However, it is not the only valid option.

### Cut constraints

One can require that every selected subset not containing the source is connected to the rest of
the graph by at least one selected edge.

This leads to connectivity cuts of the form:

```text
sum_{e in delta(S)} x_e >= 1
```

for appropriate selected subsets \(S\).

Advantage:

- closer to pure graph connectivity language.

Disadvantage:

- exponentially many potential cuts;
- often implemented with lazy constraints or separation procedures.

### Subtour-style elimination

Because Tracks resembles a path-selection problem on a graph, one can also think in the style of
subtour elimination from TSP-like models.

Advantage:

- conceptually familiar in combinatorial optimization.

Disadvantage:

- again, it usually requires dynamic cut management instead of a compact first model.

For a first implementation, the flow approach is the most direct baseline.

## 8. Compact Mapping from Model to Code

| Mathematical object | Meaning | Where it appears in code |
| --- | --- | --- |
| \(V\) | set of cells | `tracks_solver/core/graph.py` via `build_grid_graph(...).cells` |
| \(E\) | admissible undirected edges | `build_grid_graph(...).edges` |
| \(N(v)\) | neighbors of one cell | `build_grid_graph(...).neighbors` |
| \(\delta(v)\) | incident edges of one cell | `build_grid_graph(...).incident_edges` |
| \(y_v\) | used-cell variable | `tracks_solver/solver/milp.py` as `y[cell]` |
| \(x_e\) | selected-edge variable | `tracks_solver/solver/milp.py` as `x[edge]` |
| \(f_{uv}\) | connectivity-flow variable | `tracks_solver/solver/milp.py` as `f[arc]` |
| \(V^+, V^-, \mathcal{P}\) | fixed clues | parsed into `TracksInstance` in `tracks_solver/core/models.py` and `parser.py` |

The full mapping table is available in:
- [Model-to-Code Traceability](appendices/model_to_code_traceability.md)

## Key Takeaways

- The Tracks model is a feasibility MILP, not a cost-minimization problem.
- Cell variables express clue counts naturally; edge variables express geometry naturally.
- Degree constraints enforce local path structure, but not global validity.
- Flow constraints provide the global connectivity guarantee that removes isolated loops.

The next step is to understand how the repository mirrors this model at the architecture level.

Next: [Code Architecture](03_code_architecture.md)
