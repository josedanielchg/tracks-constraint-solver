# Tracks Project Documentation

This documentation set explains the Tracks project from first principles to implementation.
It is written as a guided story: the reader starts from the puzzle itself, moves to the graph
abstraction, then to the mixed-integer linear model, then to the Python codebase, and finally to
the material that matters during the oral defense.

This documentation **complements** the formal report. The report remains the authoritative
write-up of the mathematical formulation, while these pages explain the same ideas in a way that
connects directly to the code and to the project narrative.

Why this matters:

- during development, it gives one place where the mathematical ideas and the code are aligned;
- during debugging, it makes clear which rule belongs to which constraint or module;
- during the defense, it gives a coherent explanation path instead of isolated technical details.

## Project in One Paragraph

Tracks is a grid-based logic puzzle in which a single railway route must connect two terminals
while satisfying row and column clues and respecting fixed information. In graph terms, the grid
becomes a graph <img src="../../imgs/math/graph_g_ve.jpg" alt="G=(V,E)" height="24" />, the route becomes a selected connected subgraph with strict degree
conditions, and the puzzle becomes a feasibility problem. The current implementation translates
this idea into Python through a parser, graph helpers, an MILP solver built with PuLP/CBC, an
independent validator, ASCII rendering tools, a Pygame viewer, and dataset-generation utilities.

## Reading Paths

### Quick Defense Path

If the goal is to prepare an oral defense quickly, read in this order:

1. [From Puzzle to Graph](01_from_puzzle_to_graph.md)
2. [Mathematical Model](02_mathematical_model.md)
3. [Benchmark Results](07_benchmark_results.md)
4. [Defense Preparation](08_defense_prep.md)

### Full Technical Path

If the goal is to understand the full system from modeling to code:

1. [From Puzzle to Graph](01_from_puzzle_to_graph.md)
2. [Mathematical Model](02_mathematical_model.md)
3. [Code Architecture](03_code_architecture.md)
4. [Solver Pipeline](04_solver_pipeline.md)
5. [UI, Generation, and Data](05_ui_generation_and_data.md)
6. [Validation and Testing](06_validation_and_testing.md)
7. [Benchmark Results](07_benchmark_results.md)
8. [Defense Preparation](08_defense_prep.md)

### Code-First Path

If the reader already knows the mathematics and wants to navigate the implementation:

1. [Code Architecture](03_code_architecture.md)
2. [Solver Pipeline](04_solver_pipeline.md)
3. [UI, Generation, and Data](05_ui_generation_and_data.md)
4. [Validation and Testing](06_validation_and_testing.md)
5. [Benchmark Results](07_benchmark_results.md)
6. [Model-to-Code Traceability](appendices/model_to_code_traceability.md)

## Documentation Map

- [From Puzzle to Graph](01_from_puzzle_to_graph.md): intuitive and graph-theoretic entry point
- [Mathematical Model](02_mathematical_model.md): the MILP formulation explained in documentation form
- [Code Architecture](03_code_architecture.md): how the repository is organized as a system
- [Solver Pipeline](04_solver_pipeline.md): how one instance goes from text file to validated solution
- [UI, Generation, and Data](05_ui_generation_and_data.md): file format, viewer, generators, and datasets
- [Validation and Testing](06_validation_and_testing.md): why solver output can be trusted
- [Benchmark Results](07_benchmark_results.md): what the generated experiments show in practice
- [Defense Preparation](08_defense_prep.md): likely questions, ready answers, and speaking structure

Appendices:

- [File Format](appendices/file_format.md)
- [Glossary](appendices/glossary.md)
- [Model-to-Code Traceability](appendices/model_to_code_traceability.md)

## Relation to Existing Project Material

- Formal report:
  - [English introduction](../../../report/sections/01_introduction.tex)
  - [English mathematical model](../../../report/sections/02_mathematical_model.tex)
- Implementation guide:
  - [Tracks implementation plan](../../guide/tracks_implementation_plan.md)
- Installation:
  - [Installation guide](../installation.md)

## Storyline of the Project

The core storyline of this project is simple:

1. the puzzle looks local, because it is drawn cell by cell;
2. the real difficulty is global, because the railway must form one valid route;
3. graph theory provides the right language for this jump from local to global;
4. mathematical programming provides the right formalism to express the graph constraints;
5. the codebase mirrors this logic, from parsed instance to graph structures to solver to validator;
6. the defense must show that these pieces are not separate tricks, but one coherent model.

## Key Takeaways

- This documentation set is the explanatory layer of the project.
- The report gives the formal model; these pages explain how the model and the code fit together.
- The recommended reading order is linear, but each page is also usable as a reference.
- The final objective is not only to solve Tracks instances, but to explain the modeling choices clearly.

Next: [From Puzzle to Graph](01_from_puzzle_to_graph.md)
