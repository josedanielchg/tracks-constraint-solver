# Appendix: Glossary

This glossary collects the main graph-theoretic and optimization terms used throughout the project.
The wording is kept consistent with the style of the report and with standard course vocabulary.

## Core graph terms

**Graph**  
A structure <img src="../../../imgs/math/graph_g_ve.jpg" alt="G=(V,E)" height="24" /> with a set of vertices \(V\) and a set of edges \(E\).

**Vertex**  
A node of the graph. In this project, one vertex corresponds to one grid cell.

**Edge**  
A connection between two vertices. In this project, an edge links two orthogonally adjacent cells.

**Adjacency**  
The fact that two vertices are connected by an edge.

**Neighbor**  
A vertex adjacent to a given vertex.

**Incident edge**  
An edge touching a given vertex.

**Degree**  
The number of selected incident edges of a vertex.

**Path**  
A sequence of vertices where consecutive vertices are adjacent.

**Simple path**  
A path that does not repeat vertices.

**Cycle**  
A closed path.

**Connected component**  
A maximal connected subset of vertices.

**Connected graph**  
A graph in which every pair of vertices is connected by a path.

**Cut**  
A set of edges separating one subset of vertices from its complement.

## Tracks-specific graph terms

**Grid graph**  
The graph induced by a rectangular grid, where each cell is a vertex and edges connect orthogonally
adjacent cells.

**Selected subgraph**  
The graph formed by the used cells and selected adjacencies of a candidate Tracks solution.

**Terminal**  
One of the two distinguished endpoints of the railway route, called `A` and `B` in the viewer and
denoted \(s\) and \(t\) in the report.

**Branching**  
A local violation in which a used cell has degree at least 3.

**Disconnected loop**  
An isolated cycle that satisfies local degree rules but does not belong to the main route from the
start to the end.

## Optimization and modeling terms

**Feasibility problem**  
A problem in which the goal is to decide whether there exists a solution satisfying all
constraints, without optimizing a meaningful cost.

**MILP**  
Mixed-integer linear programming. A model using linear constraints, linear objective, and some
variables constrained to be integer or binary.

**Binary variable**  
A variable that can take only values 0 or 1.

**Decision variable**  
A variable whose value is chosen by the solver.

**Constraint**  
A condition that all feasible solutions must satisfy.

**Linear constraint**  
A constraint written as a linear expression in the variables.

**Objective function**  
The quantity minimized or maximized by an optimization model. In this project the objective is the
constant 0.

**Flow formulation**  
A connectivity formulation using auxiliary flow variables to prove reachability.

**Single-commodity flow**  
A flow model using one type of abstract flow sent from one source to the selected vertices.

**Cut formulation**  
A formulation enforcing connectivity through inequalities on selected edges crossing cuts.

**Subtour elimination**  
A family of constraints excluding disconnected cycles or components.

## Code and software terms

**Parser**  
A module that reads a textual instance and converts it into normalized in-memory data.

**Normalization**  
The process of converting multiple equivalent representations into one canonical internal form.

**Canonical edge**  
An undirected edge stored in a deterministic order so it is not duplicated as `(a,b)` and `(b,a)`.

**Validator**  
An independent module that checks whether a candidate solution really satisfies the puzzle rules.

**Traceability**  
The ability to map each mathematical concept to its implementation counterpart in code.
