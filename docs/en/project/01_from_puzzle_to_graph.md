# From Puzzle to Graph

Why this matters:

Before discussing variables, constraints, or code, the project must explain why Tracks is a graph
problem at all. This is the conceptual bridge between the puzzle as a visual object and the puzzle
as an optimization model.

## 1. The Puzzle in Plain Language

Tracks is played on a rectangular grid. Two special cells act as terminals, traditionally labeled
`A` and `B`. The goal is to build one railway route from `A` to `B`.

The route must satisfy two types of rules at the same time:

1. **local shape rules**
   - a track segment can continue straight or turn by 90 degrees;
   - there are no crossings;
   - the route does not branch;
2. **global counting rules**
   - each row has a clue telling how many cells contain track;
   - each column has a clue telling how many cells contain track.

In some instances, additional information is pre-filled:

- a cell is known to be used;
- a cell is known to be empty;
- a particular connection between two adjacent cells is known;
- or the exact local shape of a track piece is already known.

## 2. The First Modeling Step: Think in Terms of Cells and Adjacency

The puzzle is drawn on a grid, but the route is not defined by coordinates alone. It is defined by
**which cells are used** and **which neighboring cells are connected**.

This is exactly the language of graph theory:

- a **vertex** represents a cell;
- an **edge** represents an orthogonal adjacency between two neighboring cells;
- a **selected subgraph** represents the railway route.

That is why the grid is transformed into a graph <img src="../../imgs/math/graph_g_ve.jpg" alt="G=(V,E)" height="24" />.

## 3. Formal Graph Abstraction

Let the grid have \(m\) rows and \(n\) columns.

- \(R = \{1,\dots,m\}\) is the set of row indices;
- \(C = \{1,\dots,n\}\) is the set of column indices;
- \(V = R \times C\) is the set of grid cells.

Two cells are adjacent if and only if they are orthogonally adjacent in the grid. This gives the
edge set \(E\).

The graph used in the report is therefore the **grid graph**:

```text
G = (V, E)
```

with:

- one vertex per cell;
- one undirected edge between two cells that share a side.

This abstraction matches the course-style graph vocabulary directly. It also explains why the
puzzle is not simply about filling cells: it is about selecting a connected structure in a graph.

## 4. Graph Concepts Used in the Project

The most important graph notions are the following.

### Vertex

A vertex is one cell of the grid.

In code, a cell is stored as:

```python
(row, col)
```

### Edge

An edge links two orthogonally adjacent cells.

If cells `(2, 3)` and `(2, 4)` are neighbors, then the graph contains the corresponding edge.

### Neighbor

The neighbors of a vertex are the vertices that can be reached in one orthogonal step.

For a cell in the middle of the board, there may be up to four neighbors.

### Degree

The degree of a vertex is the number of selected incident edges touching it.

This notion is central for Tracks:

- a used internal track cell must have degree 2;
- each terminal must have degree 1;
- an unused cell must have degree 0.

### Path

A path is a sequence of vertices where consecutive vertices are adjacent.

The railway in Tracks is intended to be a path from the start terminal to the end terminal.

### Simple Path

A simple path does not repeat vertices.

This is the intended solution structure in the project: one simple route from `A` to `B`.

### Cycle

A cycle is a closed path.

Cycles are dangerous here because local degree conditions can allow an isolated loop even when it
does not connect to the terminals.

### Connected Component

A connected component is a maximal set of vertices connected to each other by paths.

In a valid Tracks solution, all used cells must belong to the same connected component.

### Connectedness

Connectedness means there is only one component among the selected cells.

This is not guaranteed by local rules alone. It must be enforced explicitly in the model.

### Cut

A cut separates one subset of vertices from the rest of the graph.

Cuts are important because alternative formulations of connectivity can be expressed by requiring
selected edges to cross appropriate cuts.

## 5. Why the Puzzle Is Not Only Local

At first sight, Tracks seems local because each cell contains only one small piece of track.
This is misleading.

Local rules can enforce:

- whether a cell is used;
- whether two neighboring cells can connect;
- whether a used cell has the right degree.

But local rules alone do **not** guarantee that:

- every used cell is reachable from the start;
- there is exactly one route instead of several components;
- no isolated loop appears somewhere else on the board.

This is the key modeling issue. The puzzle becomes interesting precisely because local geometry and
global connectedness must be satisfied together.

## 6. Common Misunderstanding: “It Looks Fine, So It Must Be Valid”

A frequent mistake is to accept a drawing that looks visually plausible.

For example, suppose:

- the start and end are connected by a valid-looking path;
- every used non-terminal cell has degree 2;
- all row and column clues are satisfied.

This still may be invalid if there is a disconnected cycle elsewhere in the grid.

Graph-theoretically, the selected subgraph would then have at least two connected components:

- one component containing the `A`-to-`B` path;
- one extra cyclic component.

That is why the project uses an explicit connectivity mechanism instead of trusting only degree and
counting constraints.

## 7. Why This Leads Naturally to Mathematical Programming

Once the grid is viewed as a graph, the puzzle can be described using decisions such as:

- is this vertex selected?
- is this edge selected?
- is this vertex connected to the source through selected edges?

These are standard optimization-style questions. They lead naturally to:

- binary variables for used cells;
- binary variables for selected adjacencies;
- auxiliary variables for connectivity.

This is the starting point of the MILP model.

## Key Takeaways

- Tracks is naturally modeled on a grid graph.
- The route is a selected connected subgraph with strict degree conditions.
- Degree, path, cycle, component, and cut are not optional vocabulary here; they are the core of the project.
- The main difficulty is global connectivity, not just local cell drawing.

Now that the puzzle has been turned into a graph problem, the next step is to translate that graph
structure into variables and constraints.

Next: [Mathematical Model](02_mathematical_model.md)
