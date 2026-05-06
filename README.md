# 🚂 Tracks Constraint Solver

A graph-based and optimization-oriented solver for the **Tracks** logic puzzle, implemented in
**Python** with a simple **Pygame** viewer.

This repository is built around one clear idea: the puzzle is easier to understand, solve, and
defend when it is treated as a **graph feasibility problem** rather than as a purely visual grid
game.

## 🖼️ From Puzzle to Solution

<p align="center">
  <img src="data/tracks/datasets/map_03_10x15_from_screenshot_unsolved.jpg" alt="Tracks puzzle unsolved" width="340" />
  <img src="docs/imgs/Screenshot.jpg" alt="Tracks puzzle solved" width="340" />
</p>
<p align="center">
  <em>Unsolved instance</em>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <em>Current solved view</em>
</p>

## ✨ What This Project Contains

- a formal **MILP model** of Tracks based on the project report
- a Python implementation with:
  - instance parsing
  - graph construction helpers
  - MILP solving with **PuLP/CBC**
  - independent solution validation
  - ASCII rendering
  - a lightweight **Pygame** viewer
- dataset and instance-generation utilities
- a full English documentation set for:
  - the puzzle abstraction
  - the mathematical model
  - the code architecture
  - defense preparation

## 🧠 Project in One Paragraph

Tracks is a grid-based logic puzzle in which a single railway route must connect two terminals
while satisfying row and column clues and respecting fixed information. In graph terms, the grid
becomes a graph <img src="docs/imgs/math/graph_g_ve.jpg" alt="G=(V,E)" height="24" />, the route becomes a selected connected subgraph with strict degree
conditions, and the puzzle becomes a feasibility problem. This repository translates that model
into Python through a parser, graph helpers, a solver, an independent validator, rendering tools,
and a simple visual interface.

## 📚 Documentation First

The repository now has a full project handbook in:

- [docs/en/project/index.md](docs/en/project/index.md)

That documentation is the best starting point if you want to understand the project as a coherent
story rather than as isolated files.

### Suggested reading paths

**Quick defense path**

1. [From Puzzle to Graph](docs/en/project/01_from_puzzle_to_graph.md)
2. [Mathematical Model](docs/en/project/02_mathematical_model.md)
3. [Defense Preparation](docs/en/project/07_defense_prep.md)

**Full technical path**

1. [Project documentation index](docs/en/project/index.md)
2. [From Puzzle to Graph](docs/en/project/01_from_puzzle_to_graph.md)
3. [Mathematical Model](docs/en/project/02_mathematical_model.md)
4. [Code Architecture](docs/en/project/03_code_architecture.md)
5. [Solver Pipeline](docs/en/project/04_solver_pipeline.md)
6. [UI, Generation, and Data](docs/en/project/05_ui_generation_and_data.md)
7. [Validation, Testing, and Results](docs/en/project/06_validation_testing_and_results.md)
8. [Defense Preparation](docs/en/project/07_defense_prep.md)

### Related project material

- Formal report:
  - [English introduction](report/sections/01_introduction.tex)
  - [English mathematical model](report/sections/02_mathematical_model.tex)
- Installation:
  - [Installation guide](docs/en/installation.md)
- Implementation planning:
  - [Tracks implementation plan](docs/guide/tracks_implementation_plan.md)

## 🏗️ Repository Overview

```text
tracks_solver/
  core/        # models, parser, graph helpers, validator, ASCII display
  solver/      # MILP model and solving helpers
  generation/  # random instance and dataset generation
  ui/          # Pygame viewer

data/          # manual, dataset, and imported instances
res/           # generated outputs and result files
tests/         # parser, graph, solver, UI, and validation tests
report/        # LaTeX report
docs/          # project documentation and guides
```

## ⚙️ Quick Start

Use Python **3.11**, **3.12**, or **3.13** so `pygame` installs cleanly.

### 1. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For the full setup workflow:

- [docs/en/installation.md](docs/en/installation.md)

### 2. Run the environment check

```powershell
python -m tracks_solver.main
```

### 3. Solve one instance

```powershell
python -m tracks_solver.main data/tracks/manual/small_4x4.txt
```

### 4. Open the UI

```powershell
python -m tracks_solver.main data/tracks/datasets/map_01_8x8_from_screenshot.txt --ui --time-limit 60
```

## 🔍 Why the Modeling Matters

The central modeling point of the project is that **local constraints are not enough**.

Even if:

- every used internal cell has degree 2,
- the terminals have degree 1,
- and the row and column clues are satisfied,

the board may still contain a disconnected loop.

That is why the project uses:

- binary variables for used cells,
- binary variables for selected adjacencies,
- and a **flow-based connectivity formulation** to force one valid route.

This is the main mathematical idea of the project, and it is reflected directly in the code.

## 🧪 Current Capabilities

- parse `.txt` puzzle instances
- support `fixed_used`, `fixed_empty`, `fixed_edges`, and `fixed_patterns`
- solve small and medium instances with MILP
- validate solver output independently
- render solutions in ASCII and Pygame
- generate solvable random instances
- solve datasets and export CSV summaries

## ✅ Quality Checks

Run the test suite with:

```powershell
python -m pytest
```

The tests cover:

- parsing
- graph construction
- validation
- solver behavior
- generation
- Pygame smoke rendering

## 🎯 What This Repository Is For

This project is not only about producing a solution grid.
It is also about being able to explain:

- why Tracks is a graph problem,
- why it is modeled as a feasibility MILP,
- how the mathematical model becomes code,
- and why the implementation can be trusted.

If you want the shortest path into that story, start here:

- [docs/en/project/index.md](docs/en/project/index.md)
