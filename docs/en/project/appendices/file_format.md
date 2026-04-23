# Appendix: Tracks Instance File Format

This appendix defines the plain-text `.txt` format currently used by the project.

## 1. Required Fields

Every instance must contain:

```text
rows=<integer>
cols=<integer>
start=<row,col>
end=<row,col>
row_clues=<int,int,...>
col_clues=<int,int,...>
```

Example:

```text
rows=4
cols=4
start=0,0
end=3,3
row_clues=4,1,1,1
col_clues=1,1,1,4
```

## 2. Optional Fields

Optional clue fields:

```text
fixed_used=<cell;cell;...>
fixed_empty=<cell;cell;...>
fixed_edges=<edge;edge;...>
fixed_patterns=<pattern;pattern;...>
```

## 3. Primitive Syntax

### Cell

A cell is written as:

```text
row,col
```

Example:

```text
2,3
```

### List separator

Multiple items are separated by semicolons:

```text
fixed_used=1,1;2,3;4,0
```

### Edge

An edge is written as:

```text
row1,col1-row2,col2
```

Example:

```text
fixed_edges=2,0-2,1;0,3-1,3
```

The two cells must be orthogonally adjacent.

### Pattern

A local pattern is written as:

```text
row,col:token
```

Example:

```text
fixed_patterns=0,0:R;2,2:H;4,5:UR
```

## 4. Pattern Tokens

Supported tokens:

- `H`: horizontal piece, equivalent to `L,R`
- `V`: vertical piece, equivalent to `U,D`
- `UR`, `UL`, `DR`, `DL`: corner pieces
- `U`, `D`, `L`, `R`: one-direction patterns, mainly for terminals

Interpretation:

- `U`: up
- `D`: down
- `L`: left
- `R`: right

Non-terminal cells must have exactly two directions.
Terminal cells may have one direction.

## 5. Semantics of Optional Fields

### `fixed_used`

Meaning:

- the cell must belong to the route.

### `fixed_empty`

Meaning:

- the cell must not belong to the route.

### `fixed_edges`

Meaning:

- the listed adjacency must be selected.

### `fixed_patterns`

Meaning:

- the local incident-edge pattern of the cell is fully fixed.

`fixed_patterns` are stronger than `fixed_edges`, because they describe the whole local piece
rather than just one required adjacency.

## 6. Normalization Rules

When an instance is parsed:

- coordinates are normalized as tuples;
- undirected edges are canonicalized;
- the start and end cells are automatically included in `fixed_used`;
- `fixed_patterns` imply corresponding fixed edges internally.

## 7. Common Encoding Mistakes

### Wrong clue length

Invalid:

```text
rows=4
row_clues=1,2,3
```

Reason:

- the number of row clues must equal `rows`.

### Non-adjacent edge

Invalid:

```text
fixed_edges=0,0-2,2
```

Reason:

- fixed edges must connect orthogonally adjacent cells.

### Contradictory fixed cells

Invalid:

```text
fixed_used=1,1
fixed_empty=1,1
```

Reason:

- the same cell cannot be simultaneously forced used and forced empty.

### Pattern pointing outside the grid

Invalid:

```text
rows=4
cols=4
fixed_patterns=0,0:U
```

Reason:

- the pattern would require a connection leaving the board from a non-terminal cell.

## 8. Full Example

```text
rows=5
cols=5
start=4,0
end=0,4
row_clues=3,1,3,1,1
col_clues=3,1,3,1,1
fixed_used=2,1
fixed_empty=4,4
fixed_edges=2,0-2,1;0,3-0,4
fixed_patterns=4,0:U;0,4:L
```

This example contains all currently supported fixed-information fields.
