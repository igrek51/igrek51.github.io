# Rubik's Cube Simulator & SVG Generator

## Overview

This project provides a complete Rubik's Cube simulator, SVG renderer, and interactive testing server. It powers the "Rubik's Cube for Dummies" printable guide.

**Key files** (all in `scripts/rubik/`):

| File | Purpose |
|------|---------|
| `gen_rubik_guide.py` | Cube simulator, SVG renderer, guide generator |
| `test_cube_moves.py` | 18 unit tests for all moves and sequences |
| `test_server.py` | HTTP API server for interactive browser testing |
| `test_cube_generator.html` | Web UI for the API |
| `start_server.sh` | Start/restart the API server |

**Output directory**: `docs/rubik-for-dummies/assets/` (generated SVGs)

---

## Quick Start

### 30-Second Setup

```bash
# Terminal 1: Start the server
bash scripts/rubik/start_server.sh

# Open in browser
# http://localhost:8080
```

You'll see a web page with:
- **Input section**: Cube state + moves
- **Output section**: Rendered cube SVG
- **Quick test buttons**: Pre-configured algorithms

### Command Line (No Server Needed)

```bash
# Generate a solved cube
python scripts/rubik/gen_rubik_guide.py --test --output /tmp/solved.svg

# Apply moves to a custom state
python scripts/rubik/gen_rubik_guide.py \
  --state "wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg" \
  --moves "R U R' U'" \
  --output /tmp/result.svg

# Generate the full 7-step guide
python scripts/rubik/gen_rubik_guide.py --guide
```

### Run Unit Tests

```bash
python scripts/rubik/test_cube_moves.py
# 18 tests, all must pass
```

---

## Cube State Format

A **54-character string** representing all 54 stickers:

```
wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg
0-8      9-17      18-26     27-35      36-44     45-53
U face   D face    F face    B face     R face    L face
```

### Face Layout (each face is 3x3):

```
0 1 2    top row
3 4 5    middle row
6 7 8    bottom row
```

### Color Codes

| Char | Color   | Hex     |
|------|---------|---------|
| `w`  | White   | #FFFFFF |
| `y`  | Yellow  | #FFD700 |
| `r`  | Red     | #FF3333 |
| `o`  | Orange  | #FF9500 |
| `b`  | Blue    | #0066FF |
| `g`  | Green   | #00AA44 |
| `l`  | Lt Gray | #aaaaaa |
| `d`  | Dk Gray | #777777 |

Gray tiles (`l`, `d`) mark irrelevant facelets (not part of the current step's focus).

---

## Move Notation

All 6 base moves with standard notation:

- **Basic moves**: `R`, `L`, `U`, `D`, `F`, `B`
- **Inverse (CCW)**: `R'`, `L'`, `U'`, `D'`, `F'`, `B'`
- **Double moves**: `R2`, `L2`, `U2`, `D2`, `F2`, `B2`
- **Sequences**: Space-separated, e.g. `R U R' U'`

### Common Algorithms

- **Sexy Move**: `R U R' U'` (order 6)
- **Sune**: `R U2 R' U' R U' R'` (order 6)
- **A-perm**: `L' U R U' L U R' U'`
- **Yellow Cross (Line)**: `F R U R' U' F'`
- **Yellow Cross (L-shape)**: `F U R U' R' F'`

---

## Move Implementation

### Face Rotation

All moves use `CCW_FACE = [6,3,0,7,4,1,8,5,2]` for face rotation (grid clockwise = cube clockwise for all faces given the isometric view orientation).

### Edge Cycles (4-cycles)

Each move has three 4-cycle tuples connecting adjacent face stickers. A cycle `[a,b,c,d]` applies: `a <- d, d <- c, c <- b, b <- a` (data flows a->b->c->d->a).

| Move | 4-cycles | Data flow |
|------|----------|-----------|
| U | `[F0,L0,B0,R0]`, `[F1,L1,B1,R1]`, `[F2,L2,B2,R2]` | R->F->L->B->R |
| D | `[F6,R6,B6,L6]`, `[F7,R7,B7,L7]`, `[F8,R8,B8,L8]` | L->F->R->B->L |
| R | `[F2,U2,B6,D2]`, `[F5,U5,B3,D5]`, `[F8,U8,B0,D8]` | D->F->U->B->D |
| L | `[F0,D0,B8,U0]`, `[F3,D3,B5,U3]`, `[F6,D6,B2,U6]` | U->F->D->B->U |
| F | `[U6,R0,D2,L8]`, `[U7,R3,D1,L5]`, `[U8,R6,D0,L2]` | L->U->R->D->L |
| B | `[U0,L0,D8,R8]`, `[U1,L3,D7,R5]`, `[U2,L6,D6,R2]` | R->U->L->D->R |

### Validation

Each move passes:
- **M^4 = identity** (4 applications return to start)
- **M + M^3 = identity** (move + 3x same move = inverse)
- **Corner consistency** (8 corners always have 3 distinct colors)

---

## Guide Generation

### Full 7-Step Guide

```bash
# Generate SVGs only
python scripts/rubik/gen_rubik_guide.py --guide --output docs/rubik-for-dummies/assets

# Generate with PNG conversion (requires Inkscape)
python scripts/rubik/gen_rubik_guide.py --guide --png --output docs/rubik-for-dummies/assets
```

### Custom Cube

```bash
python scripts/rubik/gen_rubik_guide.py \
  --state "wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg" \
  --moves "R U R'" \
  --output /tmp/custom.svg
```

### Gray Tiles

```bash
python scripts/rubik/gen_rubik_guide.py \
  --state "lllllllllyyyyyyyyylllllllllyyyyyyyyylllllllllllllllll"
```

### Key Frame Generation

The guide uses the **inverse method**:
1. Start state = `apply_alg(goal_state, inverse_alg(algorithm))`
2. Apply each move sequentially to generate intermediate frames
3. Each frame rendered as individual SVG
4. Combined into sequence SVG with arrow labels between frames

---

## SVG Rendering

### Exploded View

The `render_svg_exploded()` function renders:
- **Main cube** (center): 27 visible stickers from U+F+R perspective
- **L face** (left of main): 9 stickers, columns swapped (L2 on visual left)
- **D face** (below main): 9 stickers, rows inverted (D6 on visual top)

- ViewBox: `-2.0 -1.4 4.4 3.0`
- 48 polygons: 3 outlines + 27 main + 9 L + 9 D
- Fixed geometry from `EXPLODED_POLYGONS`; only colors change

### Sequence Rendering

`render_svg_sequence(states, labels)` generates a horizontal row of cubes with labeled arrows between them. Each cube is connected by an arrow showing the move applied.

---

## Test Server

### Starting the Server

```bash
# Method 1: Using the wrapper script
bash scripts/rubik/start_server.sh

# Method 2: Direct
python scripts/rubik/test_server.py [port] [host]
# Default: port 8080, host localhost
```

### API Endpoint

**POST /api/generate**

```json
{
  "state": "wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg",
  "moves": "R U R' U'"
}
```

Response: `Content-Type: image/svg+xml`

### Web Interface

Open `http://localhost:8080` to use the interactive tester:
- Enter/select cube state
- Apply move sequences
- View rendered SVG in real-time
- Download SVG files

### Quick Test Buttons

Pre-configured in the HTML UI:
- Single moves: R, L, U, D, F, B, R2, R'
- Algorithms: Sexy Move, Sune, Yellow Cross

---

## Troubleshooting

### Server won't start
```bash
# Check Python version (3.6+ required)
python --version

# Check if port is in use
lsof -i :8080

# Check imports
python -c "from scripts.rubik.gen_rubik_guide import *"
```

### SVG not displaying
- Verify file size (~5-10KB): `ls -lh /tmp/test.svg`
- Check SVG syntax: `xmllint /tmp/test.svg`
- Test isolated moves: `python gen_rubik_guide.py --state "SOLVED" --moves "R" --output /tmp/test_R.svg`

### Algorithm verification
- **Inverse test**: `R U R' U'` applied 6x returns to solved
- **Sune test**: `R U R' U R U2 R'` applied 6x returns to solved
- **Corner test**: After any sequence, all 8 corners have 3 distinct colors

## Architecture

### Data Flow

```
User Input (HTML form)
    -> JavaScript fetch to /api/generate
    -> Python server receives JSON
    -> Parse state + moves
    -> Apply moves to cube state
    -> Render SVG from final state
    -> Return SVG to browser
```

### State Processing

```
Input State (54 chars) -> Validate -> Parse -> Apply Moves -> Render -> SVG Output
```

---

## 7 Solving Steps

| Step | Goal | Variants |
|------|------|----------|
| 1: White Cross | White cross on U face | 2 (F, F') |
| 2: White Corners | 4 white corners on U face | 2 |
| 3: Second Layer | 4 edge pieces in middle row | 2 |
| 4: Yellow Cross | Yellow cross on D face | 3 |
| 5: Orient Yellow | Yellow corners oriented | 1 (Sune) |
| 6: Permute Corners | Corners in correct positions | 1 (A-perm) |
| 7: Final Edges | All edges solved | 1 (Antisune + Sune) |
