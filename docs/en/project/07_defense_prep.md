# Defense Preparation

Why this matters:

The project is not complete if the team can solve instances but cannot explain the modeling
choices. This page turns the report and the codebase into defense-ready speaking material.

## 1. Core Oral Strategy

The defense should not start with implementation details. It should start with the problem
structure.

Recommended speaking order:

1. explain the puzzle briefly;
2. explain why the puzzle becomes a graph problem;
3. explain why local rules are not enough;
4. explain the MILP model at a high level;
5. explain how the code mirrors the model;
6. explain how validation and tests make the project trustworthy.

This order keeps the argument coherent and avoids sounding like the code was written before the
model was understood.

## 2. A 2-Minute Pitch

> Tracks is a grid-based logic puzzle where the goal is to connect two terminals by a single
> railway route while respecting row and column clues. We modeled the grid as a graph: cells become
> vertices, adjacencies become edges, and the route becomes a selected connected subgraph.
> The key modeling difficulty is that local degree constraints are not enough, because they allow
> disconnected loops. To avoid that, we built a mixed-integer linear feasibility model with binary
> cell variables, binary edge variables, and auxiliary flow variables that enforce global
> connectivity. Then we implemented this model in Python using PuLP/CBC, added an independent
> validator, and built a simple Pygame viewer to inspect instances and solutions. The result is a
> project where the mathematics, the code structure, and the visual output all align.

## 3. A 5-Minute Explanation

Recommended structure:

### Minute 1: Puzzle and abstraction

- Tracks is about one route on a grid.
- Row and column clues count used cells.
- The natural abstraction is a grid graph.

### Minute 2: Main graph constraints

- Internal used cells must have degree 2.
- Terminals must have degree 1.
- Branches and crossings are forbidden by degree logic.

### Minute 3: Why connectivity matters

- Degree constraints alone allow disconnected cycles.
- This is why we need a global connectivity mechanism.
- We chose a flow formulation because it is rigorous and compact for a first implementation.

### Minute 4: Code architecture

- parser -> graph -> solver -> validator -> UI
- each module mirrors one conceptual step of the model
- the validator is independent from the solver

### Minute 5: Reliability and scope

- tests cover parser, graph, solver, validator, generation, and viewer
- the current UI is simple because the focus is optimization and correctness
- dataset tools prepare the project for experiments and future scaling

## 4. Deep Technical Defense Version

If the jury wants more detail, the team should be able to go one level deeper on each major point.

### Why is Tracks a graph problem?

Because the validity of the railway depends on adjacency, degree, path structure, cycles, and
connected components. Those are graph notions, not merely geometric drawing notions.

### Why is it a feasibility problem and not a cost-minimization problem?

The puzzle does not ask for the shortest or cheapest route. It asks whether a route satisfying all
rules exists. The constant objective `min 0` simply embeds this feasibility viewpoint into MILP
form.

### Why use both cell and edge variables?

Cell variables are natural for row and column counts.
Edge variables are natural for continuity and degree.
Using only one type of variable would make one part of the model much less transparent.

### Why are degree constraints necessary?

Because they encode local shape:

- degree 2 for internal used cells;
- degree 1 for terminals;
- degree 0 for unused cells.

Without them, the solver could select cells that do not form a valid route geometry.

### Why are degree constraints insufficient without connectivity?

Because a disconnected loop also gives degree 2 at each of its used cells.
So degree constraints guarantee local consistency, not global uniqueness of the route.

### Why use a flow formulation?

Because it is a standard and rigorous way to force every selected cell to be reachable from the
source. It is easier to implement as a compact first MILP than a full lazy-cut framework.

### How is the mathematical model reflected in code?

- graph sets and neighborhoods are materialized in `graph.py`
- the MILP variables and constraints are created in `milp.py`
- fixed information is normalized in `models.py` and `parser.py`
- solver output is checked in `validation.py`

### Why is the validator separate from the solver?

Because a solver can satisfy the algebraic model and still expose bugs in extraction, file
interpretation, or fixed-clue handling. The validator is a semantic checkpoint.

### What does the Pygame viewer contribute?

It is not part of the model itself. It contributes:

- visual inspection;
- communication of results;
- easier debugging of puzzle instances and clue placement.

## 5. Likely Jury Questions and Short Answers

### "Why not solve Tracks with pure backtracking?"

You can, and such baselines are useful, but MILP gives a declarative model that is easier to
justify mathematically and compare with standard optimization techniques.

### "Could cut constraints replace the flow formulation?"

Yes. Connectivity can also be enforced with cuts or subtour-style elimination, but that usually
requires dynamic constraint management. Flow is a good compact baseline.

### "Why is the validator still needed if the solver is exact?"

Because correctness is not only about the mathematical backend. It is also about input
interpretation, output extraction, and implementation discipline.

### "What is the most delicate part of the model?"

The global connectivity condition. It is the point where local graph structure and global route
semantics meet.

### "What is the current limitation of the project?"

The current UI is intentionally simple, and the solver is presently based on a first compact MILP
formulation rather than more advanced cut separation or uniqueness-focused generation.

## 6. Defense Checklist for Each Team Member

Each team member should be able to explain clearly:

- what the puzzle asks for;
- why the grid becomes a graph;
- what a degree condition means in this context;
- why a disconnected loop is invalid;
- why a feasibility MILP is appropriate;
- what the roles of <img src="../../imgs/math/variable_triplet_yx_f.jpg" alt="y_v,\ x_e,\ f_{uv}" height="24" /> are;
- why the validator exists;
- what `fixed_used`, `fixed_empty`, `fixed_edges`, and `fixed_patterns` mean;
- how one instance moves from `.txt` file to validated solution;
- what the current UI does and does not do.

## 7. Final Speaking Advice

The strongest version of the defense is not "we implemented a solver."
It is:

- we identified the right graph abstraction;
- we translated it into a rigorous feasibility model;
- we implemented the model faithfully;
- we validated the outputs independently;
- and we can explain every design choice from puzzle semantics to code structure.

## Key Takeaways

- A good defense starts with the problem structure, not with code details.
- The central modeling insight is that local degree rules need a global connectivity companion.
- The codebase is strongest when explained as a faithful implementation of the mathematical model.
- Every team member should be ready to explain both the graph theory and the software architecture.

For quick lookup of terminology and concrete formats, use the appendices:

- [Glossary](appendices/glossary.md)
- [File Format](appendices/file_format.md)
- [Model-to-Code Traceability](appendices/model_to_code_traceability.md)
