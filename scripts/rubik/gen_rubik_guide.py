#!/usr/bin/env python3
"""
Unified Rubik's Cube SVG Guide Generator

Features:
- Full cube state representation (all 54 stickers, all 6 faces)
- Move simulator (R, L, U, D, F, B and their inverses/doubles)
- Algorithm parser and executor
- SVG renderer with exploded view (main cube + reference faces)
- Generate complete 7-step solving guide or custom test cubes

Usage:
  python gen_rubik_guide.py --guide                  # Full guide (35 SVGs)
  python gen_rubik_guide.py --test                   # Test solved cube
  python gen_rubik_guide.py --state "wwwww..." --moves "R U R'"  # Custom
"""

import os
import argparse
import subprocess
import glob
from typing import List

# ============================================================================
# CUBE STATE & MOVES
# ============================================================================

# Facelet indices: U=0-8, D=9-17, F=18-26, B=27-35, R=36-44, L=45-53
# Each face is laid out as:
#   0 1 2
#   3 4 5
#   6 7 8

def _idx(face: int, pos: int) -> int:
    """Convert face (0-5) and position (0-8) to absolute facelet index."""
    return face * 9 + pos

# Face enumeration
U, D, F, B, R, L = 0, 1, 2, 3, 4, 5

# Move definitions: (face_to_rotate, edge_positions, adjacent_cycles)
# Cycles format: each cycle is a 4-cycle [pos1, pos2, pos3, pos4]
# Meaning: pos2 <- pos1, pos3 <- pos2, pos4 <- pos3, pos1 <- pos4 (standard 4-cycle)

# Face rotation mappings:
#   Grid CW  [6,3,0,7,4,1,8,5,2] gives CCW for cube (face grid "top" points to cube back)
#   Grid CCW [2,5,8,1,4,7,0,3,6] gives CW for cube
#  0 1 2     2 5 8
#  3 4 5  →  1 4 7
#  6 7 8     0 3 6
CW_FACE = [2, 5, 8, 1, 4, 7, 0, 3, 6]
CCW_FACE = [6, 3, 0, 7, 4, 1, 8, 5, 2]

MOVE_DEFS = {
    # Each move: (face_to_rotate, all_positions, cw_idx, [cycles])
    # Cycle rotation: cycle[0] ← cycle[3], cycle[3] ← cycle[2], cycle[2] ← cycle[1], cycle[1] ← old cycle[0]
    # So data flows: old[cycle[0]]→cycle[1]→cycle[2]→cycle[3]→cycle[0]

    'U': (U, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        # U (same as old U'): F→L→B→R→F (front to left, left to back, back to right, right to front)
        [_idx(F, 0), _idx(L, 0), _idx(B, 0), _idx(R, 0)],
        [_idx(F, 1), _idx(L, 1), _idx(B, 1), _idx(R, 1)],
        [_idx(F, 2), _idx(L, 2), _idx(B, 2), _idx(R, 2)],
    ]),
    'D': (D, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        # D CW (from below): F bottom → R bottom → B bottom → L bottom → F
        [_idx(F, 6), _idx(R, 6), _idx(B, 6), _idx(L, 6)],
        [_idx(F, 7), _idx(R, 7), _idx(B, 7), _idx(L, 7)],
        [_idx(F, 8), _idx(R, 8), _idx(B, 8), _idx(L, 8)],
    ]),
    'F': (F, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        # F CW (looking at front): U bottom → R left → D top → L right → U
        [_idx(U, 6), _idx(R, 0), _idx(D, 2), _idx(L, 8)],
        [_idx(U, 7), _idx(R, 3), _idx(D, 1), _idx(L, 5)],
        [_idx(U, 8), _idx(R, 6), _idx(D, 0), _idx(L, 2)],
    ]),
    'B': (B, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        # B CW (looking at back): U top → L left → D bottom → R right → U
        [_idx(U, 0), _idx(L, 0), _idx(D, 8), _idx(R, 8)],
        [_idx(U, 1), _idx(L, 3), _idx(D, 7), _idx(R, 5)],
        [_idx(U, 2), _idx(L, 6), _idx(D, 6), _idx(R, 2)],
    ]),
    'R': (R, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        # R CW (looking at right face): F right → U right → B left → D right → F
        [_idx(F, 2), _idx(U, 2), _idx(B, 6), _idx(D, 2)],
        [_idx(F, 5), _idx(U, 5), _idx(B, 3), _idx(D, 5)],
        [_idx(F, 8), _idx(U, 8), _idx(B, 0), _idx(D, 8)],
    ]),
    'L': (L, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        # L CW (looking at left): F left → D left → B right → U left → F
        [_idx(F, 0), _idx(D, 0), _idx(B, 8), _idx(U, 0)],
        [_idx(F, 3), _idx(D, 3), _idx(B, 5), _idx(U, 3)],
        [_idx(F, 6), _idx(D, 6), _idx(B, 2), _idx(U, 6)],
    ]),
    'M': (U, [], [], [
        # M going down (same as D, looking at right face): U→F→D→B→U
        [_idx(U, 1), _idx(F, 1), _idx(D, 1), _idx(B, 7)],
        [_idx(U, 4), _idx(F, 4), _idx(D, 4), _idx(B, 4)],
        [_idx(U, 7), _idx(F, 7), _idx(D, 7), _idx(B, 1)],
    ]),
}


def apply_move(state: List[str], move: str) -> List[str]:
    """Apply a single move (R, L, U, D, F, B) to cube state. Returns new state."""
    state = list(state)  # Copy
    
    face, edge_positions, cw_idx, cycles = MOVE_DEFS[move]
    
    # Rotate face using per-move cw_idx
    face_stickers = [state[_idx(face, i)] for i in edge_positions]
    for i, pos in enumerate(edge_positions):
        state[_idx(face, pos)] = face_stickers[cw_idx[i]]
    
    # Rotate adjacent edges (4-cycles)
    # Each cycle: [idx0, idx1, idx2, idx3]
    # Rotation: idx0 <- idx3, idx3 <- idx2, idx2 <- idx1, idx1 <- old idx0
    for cycle in cycles:
        saved = state[cycle[3]]
        state[cycle[3]] = state[cycle[2]]
        state[cycle[2]] = state[cycle[1]]
        state[cycle[1]] = state[cycle[0]]
        state[cycle[0]] = saved
    
    return state


def apply_algorithm(state: List[str], algorithm: str) -> List[str]:
    """Parse and apply an algorithm (e.g., 'R U R\' U\'') to cube state."""
    moves = parse_algorithm(algorithm)
    return apply_move_sequence(state, moves)


def parse_algorithm(algorithm: str) -> List[str]:
    """Parse algorithm string into list of moves.

    Supports both space-separated ('R U R\' U\'') and concatenated ('RUR\'U\'', 'LR') formats.
    Returns list like ['R', 'U', 'R\'', 'U\''].
    """
    algorithm = algorithm.strip()
    if not algorithm:
        return []
    # If contains spaces, tokenize by whitespace
    if ' ' in algorithm:
        tokens = algorithm.split()
        moves = []
        for token in tokens:
            if token.endswith("'") or token.endswith("2"):
                moves.append(token)
            else:
                moves.append(token)
        return moves
    # No spaces: parse character by character
    moves = []
    i = 0
    valid_moves = {'R', 'L', 'U', 'D', 'F', 'B', 'M'}
    while i < len(algorithm):
        c = algorithm[i]
        if c in valid_moves:
            if i + 1 < len(algorithm) and algorithm[i + 1] == "'":
                moves.append(c + "'")
                i += 2
            elif i + 1 < len(algorithm) and algorithm[i + 1] == '2':
                moves.append(c + '2')
                i += 2
            else:
                moves.append(c)
                i += 1
        else:
            i += 1  # skip unexpected characters
    return moves


def invert_move(move: str) -> str:
    """Return the inverse of a move (R -> R', R' -> R, R2 -> R2)."""
    if move.endswith("'"):
        return move[:-1]  # R' -> R
    elif move.endswith("2"):
        return move  # R2 -> R2
    else:
        return move + "'"  # R -> R'


def apply_move_sequence(state: List[str], moves: List[str]) -> List[str]:
    """Apply a sequence of moves (handling ', 2 notation)."""
    for move in moves:
        if move.endswith("'"):
            base_move = move[:-1]
            state = apply_move(state, base_move)
            state = apply_move(state, base_move)
            state = apply_move(state, base_move)
        elif move.endswith("2"):
            base_move = move[:-1]
            state = apply_move(state, base_move)
            state = apply_move(state, base_move)
        else:
            state = apply_move(state, move)
    return state


def inverse_algorithm(algorithm: str) -> str:
    """Return the inverse of an algorithm (reversed and each move inverted)."""
    moves = parse_algorithm(algorithm)
    inverted = [invert_move(move) for move in reversed(moves)]
    return ' '.join(inverted)


def state_to_string(state: List[str]) -> str:
    """Convert state list to 54-char string."""
    return ''.join(state)


def string_to_state(s: str) -> List[str]:
    """Convert 54-char string to state list."""
    if len(s) != 54:
        raise ValueError(f"State string must be 54 chars, got {len(s)}")
    return list(s)


# ============================================================================
# SVG RENDERING  –  3-D engine
# ============================================================================

def _solve_affine(pts3, vals):
    """Solve the 4-variable affine system  [x,y,z,1]·m = val  in least-squares."""
    n = len(pts3)
    ATA = [[0.0]*4 for _ in range(4)]
    ATb = [0.0]*4
    for i in range(n):
        row = list(pts3[i]) + [1.0]
        for j in range(4):
            for k in range(4):
                ATA[j][k] += row[j] * row[k]
            ATb[j] += row[j] * vals[i]
    aug = [ATA[i][:] + [ATb[i]] for i in range(4)]
    for col in range(4):
        best = col
        for row in range(col + 1, 4):
            if abs(aug[row][col]) > abs(aug[best][col]):
                best = row
        aug[col], aug[best] = aug[best], aug[col]
        piv = aug[col][col]
        for row in range(4):
            if row == col:
                continue
            f = aug[row][col] / piv
            for k in range(5):
                aug[row][k] -= f * aug[col][k]
    return [aug[i][4] / aug[i][i] for i in range(4)]


# Affine projection fitted to the 7 visible cube corners that appear in the
# original SVG polygon data.  Coordinate system: x=right, y=depth, z=up.
# Each corner is a vertex shared by three cube faces; the screen positions
# come directly from the outline polygon strings in the original art.
_CORNER_XYZ = [
    (1,0,1), (1,1,1), (1,1,0), (1,0,0),   # R-face corners
    (0,0,1), (0,1,1), (0,0,0),             # L/F/U corners visible in outlines
]
_CORNER_SX = [
     0.20684405736417,  0.65400098857461,  0.59354043975904,  0.18464331255837,
    -0.69915174967186, -0.16103316974267, -0.63049311492991,
]
_CORNER_SY = [
    -0.10342202868208, -0.50223953102503,  0.29677021987952,  0.78141988002483,
    -0.34957587483593, -0.68150055605482,  0.48418667844381,
]
_MX = _solve_affine(_CORNER_XYZ, _CORNER_SX)
_MY = _solve_affine(_CORNER_XYZ, _CORNER_SY)


def _proj(x: float, y: float, z: float):
    """Project a 3-D point to (sx, sy) screen coordinates."""
    return (
        _MX[0]*x + _MX[1]*y + _MX[2]*z + _MX[3],
        _MY[0]*x + _MY[1]*y + _MY[2]*z + _MY[3],
    )


def _tile_quad(o, u, v, row: int, col: int, n: int = 3) -> List[tuple]:
    """Return the 4 projected screen corners of tile (row, col) on a face.

    o  – 3-D origin corner of the face (top-left as seen from outside)
    u  – 3-D column direction vector (one full face width)
    v  – 3-D row    direction vector (one full face height)
    Tile corners wind: top-left, top-right, bottom-right, bottom-left.
    """
    c0, c1 = col / n, (col + 1) / n
    r0, r1 = row / n, (row + 1) / n
    return [
        _proj(o[0]+c0*u[0]+r0*v[0], o[1]+c0*u[1]+r0*v[1], o[2]+c0*u[2]+r0*v[2]),
        _proj(o[0]+c1*u[0]+r0*v[0], o[1]+c1*u[1]+r0*v[1], o[2]+c1*u[2]+r0*v[2]),
        _proj(o[0]+c1*u[0]+r1*v[0], o[1]+c1*u[1]+r1*v[1], o[2]+c1*u[2]+r1*v[2]),
        _proj(o[0]+c0*u[0]+r1*v[0], o[1]+c0*u[1]+r1*v[1], o[2]+c0*u[2]+r1*v[2]),
    ]


def _fmt_poly(pts) -> str:
    return ' '.join(f'{x},{y}' for x, y in pts)


# ── Face definitions (origin, col-vec u, row-vec v) ──────────────────────────
# Origin = top-left corner as seen from *outside* the face.
# u = direction that increases the column index (left→right from outside).
# v = direction that increases the row    index (top→bottom from outside).
#
# R face  (x=1, outward +x):  top-left from right = TBR=(1,1,1),  u→-y,  v→-z
_R_FACE = ((1,1,1), (0,-1,0), (0,0,-1))
# U face  (z=1, outward +z):  top-left from above = TBL=(0,1,1),  u→+x,  v→-y
_U_FACE = ((0,1,1), (1,0,0),  (0,-1,0))
# F face  (y=0, outward -y):  top-left from front = TFL=(0,0,1),  u→+x,  v→-z
_F_FACE = ((0,0,1), (1,0,0),  (0,0,-1))
# L face  (x=0, outward -x):  top-left from left  = TFL=(0,0,1),  u→+y,  v→-z
_L_FACE = ((0,0,1), (0,1,0),  (0,0,-1))
# D face  (z=0, outward -z):  top-left from below = BBL=(0,1,0),  u→+x,  v→-y
_D_FACE = ((0,1,0), (1,0,0),  (0,-1,0))
# B face  (y=1, outward +y):  top-left from back  = TBR=(1,1,1),  u→-x,  v→-z
_B_FACE = ((1,1,1), (-1,0,0), (0,0,-1))

# Minimum gaps (in 3-D cube units) so each mirror clears the cube outline.
# Computed by separating-axis theorem along each face's outward screen normal:
#   mirror_min_projection > cube_max_projection  (plus 0.05 visual clearance).
_MIRROR_GAP_L = 0.6737   # L face outward = -x
_MIRROR_GAP_D = 0.8044   # D face outward = -z
_MIRROR_GAP_B = 1.7489   # B face outward = +y

# Mirror face definitions: same orientation as the hidden face, shifted outward.
def _shifted(face_def, dx, dy, dz):
    o, u, v = face_def
    return ((o[0]+dx, o[1]+dy, o[2]+dz), u, v)

_L_MIRROR = _shifted(_L_FACE, -_MIRROR_GAP_L, 0,              0)
_D_MIRROR = _shifted(_D_FACE,  0,              0,             -_MIRROR_GAP_D)
_B_MIRROR = _shifted(_B_FACE,  0,             +_MIRROR_GAP_B,  0)


def _build_exploded_polygons() -> List[str]:
    """Build all 57 polygon strings for the exploded cube view via the 3-D engine.

    Index layout (unchanged from original):
      0-2   : outlines for R, U, F faces
      3-11  : R face sticker tiles
      12-20 : U face sticker tiles
      21-29 : F face sticker tiles
      30-38 : L mirror tiles  (same orientation as L face, shifted outward in -x)
      39-47 : D mirror tiles  (same orientation as D face, shifted outward in -z)
      48-56 : B mirror tiles  (same orientation as B face, shifted outward in +y)

    Sticker-to-polygon mapping in sticker_order is unchanged; the geometry now
    comes entirely from the 3-D projection so all faces are axis-aligned and
    the mirrors are exactly parallel to the corresponding cube faces.
    """
    polys = []

    # ── 3 face outlines (filled with nothing, just strokes) ──────────────────
    for face in (_R_FACE, _U_FACE, _F_FACE):
        o, u, v = face
        corners = [
            _proj(*o),
            _proj(o[0]+u[0], o[1]+u[1], o[2]+u[2]),
            _proj(o[0]+u[0]+v[0], o[1]+u[1]+v[1], o[2]+u[2]+v[2]),
            _proj(o[0]+v[0], o[1]+v[1], o[2]+v[2]),
        ]
        polys.append(_fmt_poly(corners))

    # ── 9 tiles each for R, U, F (main visible faces) ────────────────────────
    for face in (_R_FACE, _U_FACE, _F_FACE):
        o, u, v = face
        for row in range(3):
            for col in range(3):
                polys.append(_fmt_poly(_tile_quad(o, u, v, row, col)))

    # ── 9 tiles each for L, D, B mirrors ────────────────────────────────────
    for face in (_L_MIRROR, _D_MIRROR, _B_MIRROR):
        o, u, v = face
        for row in range(3):
            for col in range(3):
                polys.append(_fmt_poly(_tile_quad(o, u, v, row, col)))

    return polys


# Build at module load.
EXPLODED_POLYGONS = _build_exploded_polygons()

# ViewBox: computed from actual polygon extents plus a small margin.
_VB_MARGIN = 0.08
_all_pts = [
    (float(tok.split(',')[0]), float(tok.split(',')[1]))
    for poly in EXPLODED_POLYGONS
    for tok in poly.split()
]
_VB_X0 = min(p[0] for p in _all_pts) - _VB_MARGIN
_VB_Y0 = min(p[1] for p in _all_pts) - _VB_MARGIN
_VB_W  = max(p[0] for p in _all_pts) - _VB_X0 + _VB_MARGIN
_VB_H  = max(p[1] for p in _all_pts) - _VB_Y0 + _VB_MARGIN


def render_cube_group(state: List[str], ox: float = 0.0, oy: float = 0.0,
                      scale: float = 1.0) -> str:
    """Render cube state as SVG <g> elements at given offset and scale."""
    state = list(state)
    color_map = {
        'w': '#FFFFFF', 'y': '#FFD700', 'r': '#FF3333',
        'o': '#FF9500', 'b': '#0066FF', 'g': '#00AA44',
        'l': '#aaaaaa', 'd': '#777777',
    }
    transform = f"transform='translate({ox},{oy}) scale({scale})'"
    lines = [f"  <g {transform} style='stroke:#000000;stroke-width:0.035;"
             f"stroke-linejoin:round;stroke-linecap:round'>"]

    # Polygon index → (face_enum, sticker_pos) mapping.
    # Mirror faces need sticker re-ordering because of how each face is
    # numbered (from the outside viewer's perspective the column/row direction
    # may differ from the 3-D origin/u/v chosen above).
    #
    # L face: sticker[0]=top-left from left = origin=(0,0,1), col→+y, row→-z
    #   → L[row,col] maps to sticker row*3+col  (standard, no swap needed)
    #   BUT the original sticker_order had columns reversed relative to the
    #   old R-copy approach.  With the proper 3-D face the col direction (+y)
    #   already places sticker 0 at top-left (back of cube) and sticker 2 at
    #   top-right (front of cube), matching the standard L face numbering.
    #
    # D face: sticker[0]=back-left from below = origin=(0,1,0), col→+x, row→-y(front)
    #   → D[row,col] maps to standard sticker row*3+col
    #
    # B face: sticker[0]=top-left from back = origin=(1,1,1), col→-x, row→-z
    #   → B[row,col] maps to standard sticker row*3+col
    sticker_order = [
        # outlines
        (0, None), (1, None), (2, None),
        # R face  – R[row,col] = sticker row*3+col
        (3,  (R, 0)), (4,  (R, 1)), (5,  (R, 2)),
        (6,  (R, 3)), (7,  (R, 4)), (8,  (R, 5)),
        (9,  (R, 6)), (10, (R, 7)), (11, (R, 8)),
        # U face  – U[row,col] = sticker row*3+col
        (12, (U, 0)), (13, (U, 1)), (14, (U, 2)),
        (15, (U, 3)), (16, (U, 4)), (17, (U, 5)),
        (18, (U, 6)), (19, (U, 7)), (20, (U, 8)),
        # F face  – F[row,col] = sticker row*3+col
        (21, (F, 0)), (22, (F, 1)), (23, (F, 2)),
        (24, (F, 3)), (25, (F, 4)), (26, (F, 5)),
        (27, (F, 6)), (28, (F, 7)), (29, (F, 8)),
        # L mirror – origin=(0-gap,0,1), u→+y, v→-z
        #   tile(row,col): col increases toward +y = toward back of cube
        #   L sticker layout (from outside/left): col=0 → front (y=0) = sticker 2,4,8...
        #   Our u=+y means col=0→front? No: u=(0,1,0) so col=0 is y=0 (front), col=2 is y=1 (back).
        #   L sticker 0=top-back, 2=top-front. tile(0,0)=top-front → sticker L[2].
        (30, (L, 2)), (31, (L, 1)), (32, (L, 0)),
        (33, (L, 5)), (34, (L, 4)), (35, (L, 3)),
        (36, (L, 8)), (37, (L, 7)), (38, (L, 6)),
        # D mirror – origin=(0,1,-gap), u→+x, v→-y(front)
        #   tile(row,col): row=0→y=1(back), row=2→y=0(front)
        #   D sticker 0=back-left, 6=front-left. tile(0,0)→back-left→D[0].
        (39, (D, 0)), (40, (D, 1)), (41, (D, 2)),
        (42, (D, 3)), (43, (D, 4)), (44, (D, 5)),
        (45, (D, 6)), (46, (D, 7)), (47, (D, 8)),
        # B mirror – origin=(1,1+gap,1), u→-x, v→-z
        #   tile(row,col): col=0→x=1(right of cube), col=2→x=0(left of cube)
        #   B sticker 0=top-left from back = top-right in cube = x=1. tile(0,0)→B[0].
        (48, (B, 0)), (49, (B, 1)), (50, (B, 2)),
        (51, (B, 3)), (52, (B, 4)), (53, (B, 5)),
        (54, (B, 6)), (55, (B, 7)), (56, (B, 8)),
    ]

    for poly_idx, face_info in sticker_order:
        points_str = EXPLODED_POLYGONS[poly_idx]
        if face_info is None:
            lines.append(f"    <polygon fill='none' stroke='#000000' "
                         f"stroke-width='0.08' points='{points_str}'/>")
        else:
            face, pos = face_info
            color_char = state[_idx(face, pos)]
            color = color_map.get(color_char, '#CCCCCC')
            lines.append(f"    <polygon fill='{color}' stroke='#000000' "
                         f"points='{points_str}'/>")

    lines.append("  </g>")
    return '\n'.join(lines)


def render_svg_exploded(state: List[str], size: int = 600) -> str:
    """Render cube state as SVG with exploded view (main + reference faces)."""
    vb = f'{_VB_X0:.4f} {_VB_Y0:.4f} {_VB_W:.4f} {_VB_H:.4f}'
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='{vb}'>",
        f"  <rect fill='#FFFFFF' x='{_VB_X0:.4f}' y='{_VB_Y0:.4f}' "
        f"width='{_VB_W:.4f}' height='{_VB_H:.4f}'/>",
        render_cube_group(state),
        "</svg>",
    ]
    return '\n'.join(lines)


def render_svg_sequence(states: List[List[str]], labels: List[str],
                         cell_size: int = 120, arrow_gap: int = 50,
                         label_height: int = 30) -> str:
    """Render multiple cube states in a row with arrows and move labels.
    
    Args:
        states: List of cube states (each is list of 54 strings)
        labels: List of move labels (len = len(states) - 1)
        cell_size: Width/height for each cube cell in px
        arrow_gap: Gap between cubes for arrow in px
        label_height: Extra bottom space for move labels
    """
    n = len(states)
    m = len(labels)
    if m != n - 1:
        raise ValueError(f"Expected {n-1} labels for {n} states, got {m}")
    
    # Layout: each cube in a cell of (cell_size x cell_size), 
    # then arrow_gap, then next cube, etc.
    # viewBox for each cube: width 4.4, height 3.0
    # Scale: cell_size / 4.4
    scale = cell_size / 4.4
    cell_step = cell_size + arrow_gap
    total_width = (n - 1) * cell_step + cell_size
    total_height = cell_size + label_height
    
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{total_width}' height='{total_height}' "
        f"viewBox='0 0 {total_width} {total_height}'>",
        f"  <rect fill='#FFFFFF' x='0' y='0' width='{total_width}' height='{total_height}'/>",
    ]
    
    for i, state in enumerate(states):
        # Cube position: centered in cell
        cx = i * cell_step + cell_size / 2
        cy = cell_size / 2
        # The viewBox center is at x=0.2, y=0.1 (from -2.0 to 2.4, -1.4 to 1.6)
        # So offset to center:
        ox = cx - 0.2 * scale
        oy = cy - 0.1 * scale
        lines.append(render_cube_group(state, ox, oy, scale))
        
        # Arrow to next cube (if not last)
        if i < n - 1:
            label = labels[i]
            arrow_start_x = i * cell_step + cell_size + 5
            arrow_end_x = (i + 1) * cell_step - 5
            arrow_y = cy
            
            # Arrow line
            lines.append(
                f"  <line x1='{arrow_start_x}' y1='{arrow_y}' "
                f"x2='{arrow_end_x}' y2='{arrow_y}' "
                f"stroke='#333333' stroke-width='2' marker-end='url(#arrow)'/>"
            )
            
            # Arrow label below
            lines.append(
                f"  <text x='{(arrow_start_x + arrow_end_x) / 2}' "
                f"y='{cy + label_height / 2 + 4}' "
                f"text-anchor='middle' font-family='monospace' font-size='13' "
                f"fill='#333333'>{label}</text>"
            )
    
    # Arrow marker definition
    lines.insert(3, "  <defs>")
    lines.insert(4, "    <marker id='arrow' viewBox='0 0 10 10' refX='8' refY='5'")
    lines.insert(5, "      markerWidth='6' markerHeight='6' orient='auto-start-reverse'>")
    lines.insert(6, "      <path d='M 0 0 L 10 5 L 0 10 z' fill='#333333'/>")
    lines.insert(7, "    </marker>")
    lines.insert(8, "  </defs>")
    
    lines.append("</svg>")
    return '\n'.join(lines)


# ============================================================================
# GUIDE GENERATION
# ============================================================================

# Solved state
SOLVED = list('wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg')

STEPS = {
    '01_white_cross': [
        {'variant': 'red_bottom_1', 'description': 'White-red block at bottom (V1)', 'algorithm': 'F2'},
        {'variant': 'red_bottom_2', 'description': 'White-red at bottom via M (V2)', 'algorithm': "D M D' M'"},
    ],
    # '02_white_corners': [
    #     {'variant': 'rfu', 'description': 'Corner at RFU (white on right)', 'algorithm': 'R U R\''},
    #     {'variant': 'fur', 'description': 'Corner at FUR (white on front)', 'algorithm': 'F U\' F\''},
    # ],
    # '03_second_layer': [
    #     {'variant': 'fr', 'description': 'Edge to FR slot', 'algorithm': 'U R U\' R\' U\' F\' U F'},
    #     {'variant': 'fl', 'description': 'Edge to FL slot', 'algorithm': 'U\' L\' U L U F U\' F\''},
    # ],
    # '04_yellow_cross': [
    #     {'variant': 'line', 'description': 'Line pattern (two opposite edges)', 'algorithm': 'F R U R\' U\' F\''},
    #     {'variant': 'L', 'description': 'L-shape (two adjacent edges)', 'algorithm': 'F U R U\' R\' F\''},
    #     {'variant': 'dot', 'description': 'Dot pattern (no edges)', 'algorithm': 'F R U R\' U\' F\' U2 F U R U\' R\' F\''},
    # ],
    # '05_orient_yellow': [
    #     {'variant': 'sune', 'description': 'Sune (one corner yellow on top)', 'algorithm': 'R U2 R\' U\' R U\' R\''},
    # ],
    # '06_permute_corners': [
    #     {'variant': 'a_perm', 'description': '3-corner cycle', 'algorithm': 'L\' U R U\' L U R\' U\''},
    # ],
    # '07_final_edges': [
    #     {'variant': 'antisune_sune', 'description': 'Antisune then Sune', 'algorithm': 'L\' U2 L U L\' U L R U2 R\' U\' R U\' R\''},
    # ],
}


def generate_test_cube(output_file: str, use_exploded: bool = True):
    """Generate a test cube (solved state)."""
    svg = render_svg_exploded(SOLVED)
    with open(output_file, 'w') as f:
        f.write(svg)
    print(f"Generated: {output_file}")


def generate_custom_cube(state_str: str, moves_str: str, output_file: str, use_exploded: bool = True):
    """Generate a custom cube from state string and optional moves."""
    try:
        state = string_to_state(state_str)
    except ValueError as e:
        print(f"Error parsing state: {e}")
        return
    
    if moves_str:
        try:
            state = apply_algorithm(state, moves_str)
        except Exception as e:
            print(f"Error applying moves: {e}")
            return
    
    svg = render_svg_exploded(state)
    with open(output_file, 'w') as f:
        f.write(svg)
    print(f"Generated: {output_file}")


def generate_guide(output_dir: str = 'docs/rubik-for-dummies/assets'):
    """Generate all 7 steps with per-move image sequences."""
    os.makedirs(output_dir, exist_ok=True)
    
    step_labels = {
        '01_white_cross': 'Step 1: White Cross',
        '02_white_corners': 'Step 2: White Corners',
        '03_second_layer': 'Step 3: Second Layer',
        '04_yellow_cross': 'Step 4: Yellow Cross',
        '05_orient_yellow': 'Step 5: Orient Yellow',
        '06_permute_corners': 'Step 6: Permute Corners',
        '07_final_edges': 'Step 7: Final Edges',
    }
    
    total = 0
    for step_name, variants in STEPS.items():
        solved_svg = render_svg_exploded(SOLVED)
        
        if step_name == '01_white_cross':
            # Goal: White Cross on U face, colored centers and matching edges on sides
            # U: white cross (white center U4, edges U1,U3,U5,U7), corners gray
            # F: red center F4, red edge F1, rest gray
            # R: blue center R4, blue edge R1, rest gray
            # B: orange center B4, orange edge B1, rest gray
            # L: green center L4, green edge L1, rest gray
            # D: all gray
            goal_state = list('dwdwwwdwd' + 'd'*9 + 'drddrdddd' + 'doddodddd' + 'dbddbdddd' + 'dgddgdddd')
            solved_svg = render_svg_exploded(goal_state)
            
            # Now generate variants for Step 1
            for variant in variants:
                alg = variant['algorithm']
                var_id = variant['variant']
                moves = parse_algorithm(alg)
                
                # Start state (inverse of alg applied to goal state)
                inv_alg = inverse_algorithm(alg)
                start_state = apply_algorithm(goal_state, inv_alg)
                
                # Generate sequence
                states = [start_state]
                current = list(start_state)
                move_labels = []
                for move in moves:
                    current = apply_move_sequence(current, [move])
                    states.append(list(current))
                    move_labels.append(move)
                
                seq_svg = render_svg_sequence(states, move_labels, cell_size=240)
                seq_file = os.path.join(output_dir, f'{step_name}_{var_id}_seq.svg')
                with open(seq_file, 'w') as f:
                    f.write(seq_svg)
                print(f"  {step_name}/{var_id}: sequence = {seq_file}")
                total += 1
            continue
        
        for variant in variants:
            alg = variant['algorithm']
            var_id = variant['variant']
            desc = variant['description']
            moves = parse_algorithm(alg)
            
            # Compute start state (apply inverse to solved)
            inv_alg = inverse_algorithm(alg)
            start_state = apply_algorithm(SOLVED.copy(), inv_alg)
            
            # Generate per-move sequence of states
            states = [start_state]
            current = list(start_state)
            move_labels = []
            for move in moves:
                current = apply_move_sequence(current, [move])
                states.append(list(current))
                move_labels.append(move)
            
            # Generate sequence SVG with arrows
            seq_svg = render_svg_sequence(states, move_labels, cell_size=240)
            seq_file = os.path.join(output_dir, f'{step_name}_{var_id}_seq.svg')
            with open(seq_file, 'w') as f:
                f.write(seq_svg)
            print(f"  {step_name}/{var_id}: sequence = {seq_file}")
            total += 1
            
            # Generate individual start/goal SVGs
            start_svg = render_svg_exploded(start_state)
            start_file = os.path.join(output_dir, f'{step_name}_{var_id}_start.svg')
            with open(start_file, 'w') as f:
                f.write(start_svg)
            
            goal_state = apply_algorithm(start_state.copy(), alg)
            goal_svg = render_svg_exploded(goal_state)
            goal_file = os.path.join(output_dir, f'{step_name}_{var_id}_goal.svg')
            with open(goal_file, 'w') as f:
                f.write(goal_svg)
            total += 2
            
            # Per-move individual frames
            for i, s in enumerate(states):
                frame_svg = render_svg_exploded(s)
                frame_file = os.path.join(output_dir, f'{step_name}_{var_id}_f{i}.svg')
                with open(frame_file, 'w') as f:
                    f.write(frame_svg)
                total += 1
    
    print(f"\nDone! Generated {total} SVGs in {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Rubik\'s Cube SVG Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gen_rubik_guide.py --guide                    # Full guide
  python gen_rubik_guide.py --test                     # Test cube (solved)
  python gen_rubik_guide.py --state "www..." --moves "R U R'"  # Custom
        """
    )
    
    parser.add_argument('--guide', action='store_true',
                        help='Generate full 7-step guide')
    parser.add_argument('--test', action='store_true',
                        help='Generate test cube (solved state)')
    parser.add_argument('--state', type=str, default=None,
                        help='54-char state string (U, D, F, B, R, L faces)')
    parser.add_argument('--moves', type=str, default=None,
                        help='Move sequence (e.g., "R U R\' U\'" or "R2 D L")')
    parser.add_argument('--png', action='store_true',
                        help='Convert SVGs to PNG using inkscape')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file or directory')
    
    args = parser.parse_args()
    
    if args.guide:
        out_dir = args.output or 'docs/rubik-for-dummies/assets'
        generate_guide(out_dir)
        if args.png:
            files = glob.glob(os.path.join(out_dir, '*.svg'))
            for f in files:
                png = f[:-3] + 'png'
                subprocess.run(['inkscape', f, '--export-type=png',
                                f'--export-filename={png}',
                                '--export-background=white'],
                               capture_output=True)
                print(f'  PNG: {png}')
    
    elif args.test or args.state:
        out_file = args.output or '/tmp/test.svg'
        if args.state:
            generate_custom_cube(args.state, args.moves or '', out_file)
        else:
            generate_test_cube(out_file)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
