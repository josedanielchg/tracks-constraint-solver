# Code Architecture

Why this matters:

The mathematical model only becomes useful when the codebase reflects it cleanly. A good defense
does not describe the repository as a pile of files. It explains the repository as a system with
clear responsibilities and a controlled data flow.

## 1. Architecture Principle

The project follows one strong design idea:

```text
parse -> normalize -> model -> solve -> validate -> display
```

Each step has its own module boundary. This matters because:

- the parser should not solve;
- the solver should not draw;
- the UI should not decide validity;
- the validator should not depend on Pygame.

This separation makes the project easier to explain, test, and defend.

## 2. High-Level Repository View

The repository contains several top-level areas:

- `tracks_solver/`: runtime Python package
- `data/`: puzzle instances
- `res/`: generated results
- `tests/`: automated checks
- `report/`: formal project write-up
- `docs/`: explanatory documentation
- `cours/`: course reference material that informs vocabulary and modeling style

The codebase is therefore not just a solver. It is a full project structure containing theory,
implementation, data, and support material for the defense.

## 3. Runtime Package as a System

### `tracks_solver/core/`

Role:

- represent the problem;
- parse instance files;
- build graph structures;
- validate candidate solutions;
- render simple ASCII views.

Inputs:

- raw instance text or instance file paths;
- `TracksInstance` objects;
- `TracksSolution` objects.

Outputs:

- normalized in-memory objects;
- graph helpers;
- validation results;
- ASCII strings.

What it should **not** do:

- create MILP models;
- call the numerical solver;
- open a Pygame window.

This folder is the logical foundation of the whole project.

### `tracks_solver/solver/`

Role:

- build the MILP model;
- call PuLP/CBC;
- solve one instance or a whole dataset.

Inputs:

- `TracksInstance` objects;
- directories of `.txt` instances.

Outputs:

- `TracksSolution` objects;
- CSV result summaries for dataset runs.

What it should **not** do:

- parse raw text directly when reusable parser helpers already exist;
- encode UI behavior;
- replace independent validation.

### `tracks_solver/generation/`

Role:

- generate valid instances from randomly constructed simple paths;
- serialize generated instances to the project file format;
- build datasets automatically.

Inputs:

- grid size;
- optional seed and path-length parameters.

Outputs:

- `TracksInstance` objects;
- `.txt` instance files in dataset folders.

What it should **not** do:

- rely on the Pygame viewer;
- define the optimization model.

### `tracks_solver/ui/`

Role:

- visualize an instance and, optionally, a solution.

Inputs:

- `TracksInstance`
- `TracksSolution` or `None`

Outputs:

- a rendered Pygame surface;
- an interactive window when requested.

What it should **not** do:

- decide whether a solution is valid;
- duplicate parsing logic;
- reimplement graph constraints.

### `tracks_solver/main.py`

Role:

- command-line entrypoint;
- environment check when run without an instance path;
- solve-one-instance workflow when given an instance.

This file is the bridge between the repository and a user running the project from the terminal.

## 4. Support Folders

### `data/`

This folder stores input instances.

Current organization:

- `data/tracks/manual/`: small hand-written instances used for debugging and tests
- `data/tracks/datasets/`: larger or imported instances, including screenshot-based maps
- `data/tracks/generated/`: target location for automatically generated instances

### `res/`

This folder stores outputs rather than inputs.

Current intended organization:

- `res/tracks/solutions/`: saved solutions if needed later
- `res/tracks/datasets/`: CSV summaries from dataset runs
- `res/tracks/screenshots/`: possible visual exports

### `tests/`

This folder is the trust layer of the project.

It checks:

- parsing correctness;
- graph construction;
- validation logic;
- MILP behavior on small instances;
- instance generation;
- Pygame smoke rendering.

### `report/`

This folder contains the formal report in LaTeX:

- an English main report;
- a Spanish companion report with more pedagogical explanations.

### `docs/`

This folder contains developer-facing and defense-facing explanatory documentation, including this
documentation set.

## 5. End-to-End Data Flow

The most important system-level pipeline is:

```text
instance file
  -> parse_tracks_instance(...)
  -> TracksInstance
  -> build_grid_graph(...)
  -> solve_tracks_instance(...)
  -> TracksSolution
  -> validate_solution(...)
  -> ASCII output and/or Pygame rendering
```

This flow matters because every step has one precise job:

1. the parser understands the file format;
2. the graph helper materializes the mathematical objects;
3. the solver creates and solves the MILP;
4. the validator checks the output independently;
5. the display layer only visualizes the result.

## 6. Why the Indexing Difference Matters

The report uses mathematical notation:

- rows indexed from \(1\) to \(m\)
- columns indexed from \(1\) to \(n\)

The Python implementation uses:

- rows indexed from `0` to `rows - 1`
- columns indexed from `0` to `cols - 1`

This is normal, but it must be explained explicitly during the defense because confusion here can
make the code look inconsistent with the model.

The rule is:

- **report notation** is one-based because it is mathematically standard;
- **runtime notation** is zero-based because it is Python standard.

The parser, graph helpers, solver, validator, and viewer all use zero-based coordinates
internally.

## 7. Architecture Strengths

The current structure is strong for a course project because:

- the mathematical model is visible in the runtime package;
- each major concept has a dedicated module;
- tests cover the boundaries between theory and implementation;
- the UI is a thin layer over already validated data.

This is the kind of alignment that makes a project easier to defend: the team can point to a clear
correspondence between theory, software structure, and runtime behavior.

## Key Takeaways

- The repository is organized around a controlled data flow, not around ad hoc scripts.
- `core`, `solver`, `generation`, and `ui` each have a distinct role.
- The validator is intentionally separate from the solver.
- One-based report notation and zero-based Python notation are different on purpose, not by accident.

Now that the structure of the system is clear, the next step is to follow one instance all the way
through the solver pipeline.

Next: [Solver Pipeline](04_solver_pipeline.md)
