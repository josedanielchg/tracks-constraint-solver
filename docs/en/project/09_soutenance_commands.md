# Soutenance Commands

Why this matters:

The oral defense should not depend on remembering Python function names or searching through the
repository. This page gives a direct command sequence that demonstrates the required project
workflow: create an instance, display it, solve it, open the UI, solve several instances, and
format the results as a LaTeX table.

Run all commands from the repository root after installing the dependencies from
`requirements.txt`.

## 1. Create One Instance

Course requirement covered: explain and demonstrate how instances are generated.

```powershell
python -m tracks_solver.course_workflow generate-instance --rows 5 --cols 5 --seed 203 --output data/tracks/generated/soutenance_5x5.txt
```

This command creates one generated `5x5` Tracks instance and saves it in
`data/tracks/generated/soutenance_5x5.txt`. The seed makes the example reproducible: running the
same command again gives the same generated puzzle.

The command is backed by `generate_instance(...)`, which itself uses the project generator. The
generator first creates a valid simple path and then derives the row and column clues from that
path. This is important because it avoids creating impossible boards by accident.

## 2. Display an Unsolved Grid in the Terminal

Course requirement covered: display the game in command-line mode.

```powershell
python -m tracks_solver.course_workflow display-grid data/tracks/generated/soutenance_5x5.txt
```

This prints an ASCII view of the unresolved puzzle. It is intentionally simple: the goal is to
prove that the instance can be read and displayed without using the graphical interface.

This command is backed by `display_grid(...)`, also available through the course-style alias
`displayGrid(...)`.

## 3. Solve One Instance and Display the Solution in the Terminal

Course requirement covered: present the exact resolution program and show its output.

```powershell
python -m tracks_solver.course_workflow solve-instance data/tracks/generated/soutenance_5x5.txt --time-limit 60 --display-solution
```

This command solves the instance with the exact flow-based MILP model. It prints the main result
fields:

- `isOptimal`: whether the solver proved an optimal feasible solution for the constant-objective
  feasibility model;
- `solveTime`: the measured solving time;
- `status`: the solver status used internally by the project;
- `validationPassed`: whether the independent validator accepted the extracted solution.

With `--display-solution`, the solved route is also printed in ASCII. This is the terminal-only
version of the resolution demonstration.

## 4. Open the Solved Instance in the UI

Course requirement covered: display the game in graphical mode.

```powershell
python -m tracks_solver.course_workflow open-ui data/tracks/generated/soutenance_5x5.txt --time-limit 60
```

This command solves the same instance and opens it in the Pygame viewer. The UI is useful during
the defense because it makes the railway path, row clues, column clues, terminals, and fixed hints
easy to inspect visually.

The UI is a visualization layer. The mathematical work is still done by the same exact MILP solver
used in the terminal command.

## 5. Generate Several Instances

Course requirement covered: explain and demonstrate dataset generation.

```powershell
python -m tracks_solver.course_workflow generate-dataset --output-dir data/tracks/generated/soutenance --sizes 5x5,6x6,7x7 --count-per-size 2 --seed 203 --force
```

This creates a small generated dataset:

- `5x5`, `6x6`, and `7x7` boards;
- `2` instances per size;
- deterministic generation from seed `203`;
- files saved under `data/tracks/generated/soutenance`.

The `--force` flag overwrites files with the same names. Remove it if you want to keep already
generated files unchanged.

## 6. Solve Several Instances

Course requirement covered: solve multiple instances and record the results.

```powershell
python -m tracks_solver.course_workflow solve-dataset data/tracks/generated/soutenance --result-dir res/tracks/cbc/soutenance --csv-output res/tracks/cbc/soutenance_summary.csv --time-limit 60 --force
```

This solves every `.txt` instance in `data/tracks/generated/soutenance`. For each instance, it
writes one course-style result file in `res/tracks/cbc/soutenance`. Each result file contains at
least:

- `solveTime = ...`
- `isOptimal = ...`
- `status = ...`
- `validationPassed = ...`

The command also writes a CSV summary to `res/tracks/cbc/soutenance_summary.csv`, which is easier
to inspect or reuse for plots.

## 7. Format Results as a LaTeX Table

Course requirement covered: format computational results as a table.

```powershell
python -m tracks_solver.course_workflow results-table --result-dir res/tracks/cbc/soutenance --output res/tracks/array_soutenance.tex
```

This reads the result files and writes a LaTeX table in `res/tracks/array_soutenance.tex`. The
table is intentionally small and defense-friendly: instance name, board size, solve time, and
optimality status.

## 8. Optional Playable Mode

The playable UI is not required for the course workflow, but it is useful for demonstration and
debugging.

```powershell
python -m tracks_solver.main --play
```

This opens the home screen where a user can generate a new game or load an existing map. It is kept
separate from the course command sequence because the required evaluation concerns generation,
solving, display, and result formatting.

## 9. Relation to the Exact Model

Tracks is solved here with the exact MILP formulation based on cell variables, edge variables, and
flow variables. The flow variables enforce global connectivity, which is the main non-local rule
of the puzzle.

No callback or heuristic solver is implemented for Tracks in this repository. Tracks is treated as
the lower-difficulty game, so the exact flow model is the appropriate scope for this project.

## 10. Function Names Behind the CLI

The CLI keeps the course-style Python aliases available:

- `readInputFile(...)`
- `displayGrid(...)`
- `displaySolution(...)`
- `cplexSolve(...)`
- `generateDataSet(...)`
- `solveDataSet(...)`
- `resultsArray(...)`

Internally, these names call the Python implementation based on PuLP/CBC rather than Julia/CPLEX.
The role is the same: read data, solve exactly, display outputs, and summarize results.

## Key Takeaways

- The `tracks_solver.course_workflow` module is the entry point for defense commands.
- The commands demonstrate the full required workflow without searching through code.
- The UI is useful for communication, but the terminal commands are enough to prove the required
  generation, solving, and result-table pipeline.
- The Tracks solver remains an exact flow-based MILP implementation.

Back to: [Defense Preparation](08_defense_prep.md)
