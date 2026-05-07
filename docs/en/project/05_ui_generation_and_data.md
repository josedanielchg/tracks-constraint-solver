# UI, Generation, and Data

Why this matters:

An optimization project is easier to defend when it is grounded in concrete inputs and outputs.
This page explains how instances are represented, how they are generated, how the current viewer
works, and how the project is run from the command line.

## 1. Instance File Format

Tracks instances are stored as plain text `.txt` files.

A minimal example is:

```text
rows=4
cols=4
start=0,0
end=3,3
row_clues=4,1,1,1
col_clues=1,1,1,4
```

Optional fixed-information fields can be added:

```text
fixed_used=2,1
fixed_empty=4,4
fixed_edges=2,0-2,1
fixed_patterns=0,0:R;3,3:U
```

These fields are interpreted as follows:

- `fixed_used`: cells that must belong to the path
- `fixed_empty`: cells that must remain empty
- `fixed_edges`: specific adjacencies that must be selected
- `fixed_patterns`: exact local track patterns at specific cells

For the full syntax, see:
- [File Format Appendix](appendices/file_format.md)

## 2. Manual Maps and Screenshot-Based Maps

The repository currently uses two main kinds of instance files.

### Manual instances

Stored in:

- `data/tracks/manual/`

Examples:

- `small_4x4.txt`
- `small_5x5.txt`
- `unsat_2x2.txt`

Purpose:

- unit tests;
- debugging;
- quick solver checks;
- controlled examples for explanations in the defense.

### Screenshot-based datasets

Stored in:

- `data/tracks/datasets/`

Examples:

- `map_01_8x8_from_screenshot.txt`
- `map_02_15x15_from_screenshot.txt`
- `map_03_10x15_from_screenshot.txt`

These maps were reconstructed from visible puzzle screenshots.
Depending on the screenshot quality, some visible clue pieces are encoded as:

- `fixed_patterns` when the exact geometry is clear;
- `fixed_used` when the cell is clearly part of the route but the exact local orientation is not
  safe to reconstruct from the image alone.

This is a good example of a practical modeling decision: the file format is expressive enough to
encode different levels of certainty.

## 3. Current User-Facing Commands

### Solve one instance in the terminal

```powershell
python -m tracks_solver.main data/tracks/manual/small_4x4.txt
```

What happens:

- the instance is parsed;
- the MILP is solved;
- an ASCII rendering is printed;
- solver status and validation status are printed.

### Solve one instance and open the UI

```powershell
python -m tracks_solver.main data/tracks/datasets/map_01_8x8_from_screenshot.txt --ui --time-limit 60
```

Useful options:

- `--ui`: open the Pygame viewer
- `--time-limit`: pass a time limit to CBC
- `--solver-output`: show the raw MILP solver log

### Solve a dataset from Python

There is currently no dedicated command-line wrapper for dataset solving, but the functionality is
available in code:

```python
from tracks_solver.solver import solve_dataset

rows, output_path = solve_dataset("data/tracks/datasets", time_limit=120)
```

The default CSV output path is:

```text
res/tracks/datasets/<dataset_name>_results.csv
```

## 4. Generation Strategy

Main modules:

- `tracks_solver/generation/generate_instance.py`
- `tracks_solver/generation/generate_dataset.py`

The generation logic follows a sound modeling principle:

1. generate a valid simple path first;
2. compute row clues from that path;
3. compute column clues from that path;
4. optionally expose part of the path as hints;
5. serialize the result.

Why this matters:

- if the process starts from random clues, many generated instances will be infeasible;
- if it starts from a valid path, the generated puzzle is guaranteed to have at least one solution.

This is a standard constructive strategy in puzzle generation.

## 5. How a Generated Instance Is Built

The generator:

- chooses a start and an end cell;
- searches for a simple path using randomized exploration;
- computes row and column clue counts;
- optionally reveals some internal path cells or edges as hints;
- writes the resulting instance in parser-compatible format.

This keeps the data pipeline aligned with the solver pipeline: generated instances are not a
separate format or a special-case workflow.

## 6. The Current Pygame Viewer

Main module:

- `tracks_solver/ui/pygame_viewer.py`

The viewer is intentionally simple at this stage.

It draws:

- the rectangular grid;
- row clues;
- column clues;
- terminal labels `A` and `B`;
- solution tracks, when a `TracksSolution` is provided;
- a darker background for fixed cells.

Track rendering logic:

- each used cell is inspected;
- the selected incident edges determine the directions used by that cell;
- line segments are drawn from the cell center to the relevant borders.

This means the UI is driven by the solved graph structure, not by separate hand-written drawing
logic for each puzzle shape.

## 7. What “Fixed” Means Visually

The current viewer shades fixed cells with a darker gray background.

This includes cells involved in:

- `fixed_used`
- `fixed_empty`
- `fixed_patterns`
- endpoints of `fixed_edges`

The purpose is explanatory rather than aesthetic: it helps the reader or viewer identify which
parts of the instance are given as clues rather than discovered by the solver.

## 8. Current Viewer Controls

Current keyboard behavior in the viewer:

- `Esc`: close the window
- `Space`: toggle solution visibility
- `R`: reset to the base solution state

The `TracksViewer` class also contains a hook for solving during the session if a solve function
is supplied by the caller. In the current command-line workflow, the instance is solved before the
viewer opens, so the displayed route is already known.

## 9. Current Limitations

The present UI is intentionally modest.

Current limitations:

- black-and-white rendering only;
- no advanced piece sprites;
- no click-based game interaction;
- no animation layer;
- dataset solving is available from Python functions, not yet from a dedicated CLI command;
- screenshot-based maps may contain partial reconstructions where `fixed_used` is safer than fully
  prescribed local patterns.

These limitations are acceptable for a first optimization-focused milestone because the project is
still centered on the mathematical model and solver correctness.

## Key Takeaways

- The project uses one text format for manual, generated, and imported instances.
- Generation starts from a valid path, not from random clues.
- The viewer is a presentation layer over validated data.
- The current UI is intentionally simple because the main project value lies in the model and solver.

The next step is to show how the project proves that its outputs are reliable.

Next: [Validation, Testing, and Results](06_validation_testing_and_results.md)
