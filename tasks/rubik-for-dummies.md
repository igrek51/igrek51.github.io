# Task: Rubik's Cube for Dummies

## Goal

Generate a **printable A4 landscape one-pager** showing Rubik's cube solving steps with dense cube-image sequences. Each step displays multiple unsolved variants progressing toward the solved goal state. No external dependencies -- local SVG rendering only.

## Files

- **`scripts/rubik/gen_rubik_guide.py`** -- Cube simulator + SVG renderer + guide generator
  - `render_svg_exploded(colors, size)` -- Exploded view renderer (main cube + reference faces below/left/back)
  - `render_svg_sequence(states, labels, cell_size)` -- Row of cubes with arrow labels between them
  - `apply_move()`, `apply_alg()` -- Move simulator
  - `inverse_alg()` -- Algorithm reversal
  - Key frame generation via inverse method
- **`scripts/rubik/test_cube_moves.py`** -- 18 unit tests for all moves and key sequences
- **`scripts/rubik/test_server.py`** -- HTTP API server for interactive testing
- **`scripts/rubik/test_cube_generator.html`** -- Web UI for the API
- **`scripts/rubik/start_server.sh`** -- Wrapper to start/restart the API server
- **`scripts/rubik/README.md`** -- Consolidated documentation
- **`docs/rubik-for-dummies/rubik_guide.html`** -- HTML guide
- **`docs/rubik-for-dummies/assets/`** -- Generated SVGs

## Step 1: White Cross

- **Goal**: White cross on U face, colored centers + matching edges on side faces, rest gray
- **Variants**:
  1. "Upside down" -- White-red edge at DF, solved by `F2`
  2. "Elevator" -- White-red edge at DB, solved by `D M D' M'`

## Key Implementation Details

### Cube State Representation

- **54-character string** (one char per facelet, faces in order U, D, F, B, R, L)
- **Facelet indices**: U=0-8, D=9-17, F=18-26, B=27-35, R=36-44, L=45-53
- **Color codes**: `w`=white, `y`=yellow, `r`=red, `o`=orange, `b`=blue, `g`=green, `l`=light gray (#aaaaaa), `d`=dark gray (#777777)
- **Solved state**: `wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg`
- **White Cross goal**: `dwdwwwdwd` + `d`*9 + `drddrdddd` + `doddodddd` + `dbddbdddd` + `dgddgdddd`

### Move Definitions

- **Face rotation**: All 6 moves use `CCW_FACE = [6,3,0,7,4,1,8,5,2]` (grid clockwise = cube clockwise for all faces in the isometric view)
- **4-cycles**: `[a,b,c,d]` applies `a <- d, d <- c, c <- b, b <- a` (data flow a->b->c->d->a)

| Move | 4-cycles | Data flow |
|------|----------|-----------|
| U | `[F0,L0,B0,R0]`, `[F1,L1,B1,R1]`, `[F2,L2,B2,R2]` | R->F->L->B->R |
| D | `[F6,R6,B6,L6]`, `[F7,R7,B7,L7]`, `[F8,R8,B8,L8]` | L->F->R->B->L |
| R | `[F2,U2,B6,D2]`, `[F5,U5,B3,D5]`, `[F8,U8,B0,D8]` | D->F->U->B->D |
| L | `[F0,D0,B8,U0]`, `[F3,D3,B5,U3]`, `[F6,D6,B2,U6]` | U->F->D->B->U |
| F | `[U6,R0,D2,L8]`, `[U7,R3,D1,L5]`, `[U8,R6,D0,L2]` | L->U->R->D->L |
| B | `[U0,L0,D8,R8]`, `[U1,L3,D7,R5]`, `[U2,L6,D6,R2]` | R->U->L->D->R |

### Key Frame Generation

- **Inverse method**: Start state = `apply_alg(goal, inverse_alg(algorithm))`
  - Final state = `apply_alg(start, algorithm)`
  - Each intermediate frame rendered as individual SVG + combined into sequence SVG with arrows

### Exploded View

- Main cube in center (27 visible stickers from U+F+R view)
- Reference faces:
  - **Below**: 9 D face stickers (rows inverted: D6->visual top, D0->visual bottom)
  - **Left**: 9 L face stickers (columns swapped: L2->visual left, L0->visual right)
  - **Upper-right (back)**: 9 B face stickers (columns swapped: B2->visual left, B0->visual right), shifted from F geometry
- Single SVG per cube state
- ViewBox: `-2.0 -1.4 4.4 3.0` with 57-polygon geometry (48 original + 9 B face)
- Polygon indices: 0-2 outlines, 3-11 R, 12-20 U, 21-29 F, 30-38 L (exploded), 39-47 D (exploded), 48-56 B (exploded)

### Mirror Offsets

- **L face** (left): shifted from R geometry by `dx=-1.5, dy=-0.25` (dy adjusted up by 1 tile height)
- **D face** (below): shifted from U geometry by `dx=0, dy=+1.5`
- **B face** (upper-right): shifted from F geometry by `dx=+1.5, dy=-1.0` (dx adjusted right by 1 tile width)

### SVG Sticker Order Rules

- **Main view (R, U, F)**: direct view, no mirror -- map position 0 to polygon (R,0) etc.
- **L exploded** (shifted left, mirror effect): columns swapped -- polygon 30 shows (L,2), polygon 38 shows (L,6)
- **D exploded** (shifted down, mirror effect): rows inverted -- polygon 39 shows (D,6), polygon 47 shows (D,2)
- **B exploded** (shifted upper-right, mirror effect): columns swapped -- polygon 48 shows (B,2), polygon 56 shows (B,6)

### Per-Move Sequence Rendering

- `render_svg_sequence()` generates a row of cubes connected by arrows labeled with each move
- SVG width = `(n-1)*(cell_size+arrow_gap) + cell_size`, height = `cell_size + label_height`
- Arrow marker defined in `<defs>` with CSS-compatible rendering

### PNG Conversion

- Inkscape used for SVG->PNG via `--export-type=png` flag
- Resolution: cube images 600x600, sequence images proportional (e.g., 630x150 for 4 cubes)

### Test Server API

- Python http.server-based HTTP server on `0.0.0.0:8080`
- Endpoint: `POST /api/generate` -- accepts state string and returns SVG
- Web UI at `/` for interactive testing
- Start/restart via `bash scripts/rubik/start_server.sh`

### Color Map

| Char | Color     | Hex     |
|------|-----------|---------|
| w    | white     | #FFFFFF |
| y    | yellow    | #FFD700 |
| r    | red       | #FF3333 |
| o    | orange    | #FF9500 |
| b    | blue      | #0066FF |
| g    | green     | #00AA44 |
| l    | light gray| #aaaaaa |
| d    | dark gray | #777777 |

## Commands

### Generate Guide
```bash
python scripts/rubik/gen_rubik_guide.py --guide --output docs/rubik-for-dummies/assets
```

### Generate Guide with PNG
```bash
python scripts/rubik/gen_rubik_guide.py --guide --png --output docs/rubik-for-dummies/assets
```

### Generate Single Test Cube
```bash
python scripts/rubik/gen_rubik_guide.py --test --output /tmp/test.svg
```

### Generate Custom Cube State
```bash
python scripts/rubik/gen_rubik_guide.py --state "..." --moves "R U R'" --output custom.svg
```

### Run Unit Tests
```bash
python scripts/rubik/test_cube_moves.py
# 18 tests, all must pass
```

### Start Test Server
```bash
bash scripts/rubik/start_server.sh
# http://localhost:8080
```

### Render Cube with Gray Tiles
```bash
python scripts/rubik/gen_rubik_guide.py --state "lllllllllyyyyyyyyylllllllllyyyyyyyyylllllllllllllllll"
```

## Verification Checklist

- [x] Cube simulator logic verified (move definitions, inverse algorithms, 18 tests pass)
- [x] SVG rendering with exploded view correct (L column-swapped, D row-swapped, B column-swapped mirror rules)
- [x] All 6 moves + M move use CCW_FACE (face rotation consistent)
- [x] M move verified: M^4 = identity, M + M^3 = identity; M cycles [U1,F1,D1,B7], [U4,F4,D4,B4], [U7,F7,D7,B1]
- [x] Step 1 White Cross variants: "Upside down" (F2) and "Elevator" (D M D' M')
- [x] Step 1 goal state: white cross + colored centers + matching edges, rest gray
- [x] Sequence SVG rendering with arrow labels and move labels
- [x] `--png` flag converts SVGs via Inkscape
- [x] Test server API, restartable via start_server.sh
- [x] Gray tile support (`l` = #aaaaaa, `d` = #777777)
- [x] B face mirror added to exploded view (polygons 48-56, shifted from F geometry)
- [x] L mirror shifted up 0.25 (one tile height)
- [x] B mirror shifted right 0.3 (one tile width)
- [x] Variant labels renamed: "Upside down" (F2) and "Elevator" (D M D' M')
- [ ] Print layout verified on actual A4 paper or print preview
- [ ] HTML guide renders correctly at 2x scale

## Future Enhancements

1. **More variants for Step 1**: Additional white cross edge positions (not just bottom)
2. **Steps 2-7**: Complete with all variants and algorithms
3. **Unfolded net view**: Show all 6 faces unfolded flat
4. **Interactive mode**: Click to animate algorithm step-by-step
5. **Multiple languages**: Translate algorithm text and step descriptions
