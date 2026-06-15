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
# SVG RENDERING  –  3-D perspective engine
# ============================================================================
import math as _math

# ── Perspective camera ───────────────────────────────────────────────────────
# Coordinate system: x=right, y=depth (into screen), z=up.
# Camera orbits around the cube centre (0.5, 0.5, 0.5) with:
#   azimuth  = angle in XY plane measured from -y axis (front) toward +x axis (right)
#   elevation = angle above ground plane
# This gives a natural perspective view: F face (y=0) on the left,
# R face (x=1) on the upper-right, U face (z=1) on top.

def _vec_sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _vec_dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def _vec_cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _vec_norm(a):
    m = _math.sqrt(_vec_dot(a, a))
    return (a[0]/m, a[1]/m, a[2]/m)

_CAM_AZ_DEG  = 30.0    # azimuth: 0=front(-y), 90=right(+x)  →  front-right view
_CAM_EL_DEG  = 25.0    # elevation above ground
_CAM_DIST    = 4.0     # distance from cube centre
_CAM_FOV     = 4.0     # focal-length scale (higher = less wide-angle distortion)

_target = (0.5, 0.5, 0.5)
_up_world = (0.0, 0.0, 1.0)

def _build_camera():
    az = _math.radians(_CAM_AZ_DEG)
    el = _math.radians(_CAM_EL_DEG)
    cam = (
        _target[0] + _CAM_DIST * _math.cos(el) * _math.sin(az),
        _target[1] - _CAM_DIST * _math.cos(el) * _math.cos(az),
        _target[2] + _CAM_DIST * _math.sin(el),
    )
    fwd   = _vec_norm(_vec_sub(_target, cam))
    right = _vec_norm(_vec_cross(fwd, _up_world))
    up    = _vec_cross(right, fwd)
    return cam, fwd, right, up

_CAM, _CAM_FWD, _CAM_RIGHT, _CAM_UP = _build_camera()


def _proj(x: float, y: float, z: float):
    """Project a 3-D world point onto the 2-D screen via perspective divide."""
    d  = _vec_sub((x, y, z), _CAM)
    px = _vec_dot(d, _CAM_RIGHT)
    py = _vec_dot(d, _CAM_UP)
    pz = _vec_dot(d, _CAM_FWD)
    if pz < 0.01:
        pz = 0.01
    sx =  px / pz * _CAM_FOV
    sy = -py / pz * _CAM_FOV   # flip y so +z is up on screen
    return (sx, sy)


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

# Minimum gaps (in 3-D cube units) recomputed after perspective projection change.
# Determined by separating-axis theorem: mirror clears all cube faces with 0.05 clearance.
def _compute_mirror_gaps():
    """Find minimum 3-D gap for each mirror so it doesn't overlap the cube in screen space.

    Uses separating-axis theorem along each face's outward screen-space normal.
    Returns (gap_L, gap_D, gap_B).
    """
    def all_cube_pts():
        pts = []
        for face in (_R_FACE, _U_FACE, _F_FACE):
            o, u, v = face
            for row in range(3):
                for col in range(3):
                    pts.extend(_tile_quad(o, u, v, row, col))
        return pts

    def screen_normal_of(dx3, dy3, dz3):
        # Screen displacement of a unit step in the given 3D direction
        p0 = _proj(0.5, 0.5, 0.5)
        p1 = _proj(0.5 + dx3, 0.5 + dy3, 0.5 + dz3)
        sdx, sdy = p1[0]-p0[0], p1[1]-p0[1]
        m = _math.sqrt(sdx*sdx + sdy*sdy)
        return sdx/m, sdy/m

    def dot2(a, b): return a[0]*b[0] + a[1]*b[1]

    def min_gap_for(face_def, outward3d, extra=0.06):
        sn = screen_normal_of(*outward3d)
        step_per_gap = dot2(
            (_proj(0.5+outward3d[0], 0.5+outward3d[1], 0.5+outward3d[2])[0]
             - _proj(0.5, 0.5, 0.5)[0],
             _proj(0.5+outward3d[0], 0.5+outward3d[1], 0.5+outward3d[2])[1]
             - _proj(0.5, 0.5, 0.5)[1]),
            sn
        )
        o, u, v = face_def
        face_pts_g0 = [q for row in range(3) for col in range(3)
                       for q in _tile_quad(o, u, v, row, col)]
        face_min0 = min(dot2(p, sn) for p in face_pts_g0)
        cube_max  = max(dot2(p, sn) for p in all_cube_pts())
        g = (cube_max - face_min0) / step_per_gap + extra
        return max(g, 0.15)

    gap_L = min_gap_for(_L_FACE, (-1,  0,  0))
    gap_D = min_gap_for(_D_FACE, ( 0,  0, -1))
    gap_B = min_gap_for(_B_FACE, ( 0, +1,  0))
    return gap_L, gap_D, gap_B


_MIRROR_GAP_L, _MIRROR_GAP_D, _MIRROR_GAP_B = _compute_mirror_gaps()

# Mirror face definitions: same orientation as the hidden face, shifted outward.
def _shifted(face_def, dx, dy, dz):
    o, u, v = face_def
    return ((o[0]+dx, o[1]+dy, o[2]+dz), u, v)

_L_MIRROR = _shifted(_L_FACE, -_MIRROR_GAP_L, 0,              0)
_D_MIRROR = _shifted(_D_FACE,  0,              0,             -_MIRROR_GAP_D)
_B_MIRROR = _shifted(_B_FACE,  0,             +_MIRROR_GAP_B,  0)


def _build_exploded_polygons() -> List[str]:
    """Build all 57 polygon strings for the exploded cube view via the 3-D engine.

    Index layout:
      0-2   : outlines for R, U, F faces
      3-11  : R face sticker tiles
      12-20 : U face sticker tiles
      21-29 : F face sticker tiles
      30-38 : L mirror tiles
      39-47 : D mirror tiles
      48-56 : B mirror tiles
    """
    polys = []

    # ── 3 face outlines ───────────────────────────────────────────────────────
    for face in (_R_FACE, _U_FACE, _F_FACE):
        o, u, v = face
        corners = [
            _proj(*o),
            _proj(o[0]+u[0], o[1]+u[1], o[2]+u[2]),
            _proj(o[0]+u[0]+v[0], o[1]+u[1]+v[1], o[2]+u[2]+v[2]),
            _proj(o[0]+v[0], o[1]+v[1], o[2]+v[2]),
        ]
        polys.append(_fmt_poly(corners))

    # ── 9 tiles each for R, U, F ─────────────────────────────────────────────
    for face in (_R_FACE, _U_FACE, _F_FACE):
        o, u, v = face
        for row in range(3):
            for col in range(3):
                polys.append(_fmt_poly(_tile_quad(o, u, v, row, col)))

    # ── 9 tiles each for L, D, B mirrors ─────────────────────────────────────
    for face in (_L_MIRROR, _D_MIRROR, _B_MIRROR):
        o, u, v = face
        for row in range(3):
            for col in range(3):
                polys.append(_fmt_poly(_tile_quad(o, u, v, row, col)))

    return polys


# Build at module load.
EXPLODED_POLYGONS = _build_exploded_polygons()

# ViewBox: computed from actual polygon extents plus a small margin.
_VB_MARGIN = 0.10
_all_pts = [
    (float(tok.split(',')[0]), float(tok.split(',')[1]))
    for poly in EXPLODED_POLYGONS
    for tok in poly.split()
]
_VB_X0 = min(p[0] for p in _all_pts) - _VB_MARGIN
_VB_Y0 = min(p[1] for p in _all_pts) - _VB_MARGIN
_VB_W  = max(p[0] for p in _all_pts) - _VB_X0 + _VB_MARGIN
_VB_H  = max(p[1] for p in _all_pts) - _VB_Y0 + _VB_MARGIN


def _cube_edge_lines() -> List[str]:
    """Return SVG <line> strings for the 3 bold visible cube edges.

    The three edges where visible faces meet:
      U-F junction: edge from TFL=(0,0,1) to TFR=(1,0,1)
      U-R junction: edge from TFR=(1,0,1) to TBR=(1,1,1)
      F-R junction: edge from TFR=(1,0,1) to BFR=(1,0,0)
    These are the most visible 'corners' of the cube silhouette.
    """
    edges_3d = [
        ((0,0,1), (1,0,1)),   # U-F top edge
        ((1,0,1), (1,1,1)),   # U-R top edge
        ((1,0,1), (1,0,0)),   # F-R right edge
    ]
    sw = 0.055  # bold stroke width
    lines = []
    for (x0,y0,z0), (x1,y1,z1) in edges_3d:
        p0 = _proj(x0, y0, z0)
        p1 = _proj(x1, y1, z1)
        lines.append(
            f"    <line x1='{p0[0]}' y1='{p0[1]}' x2='{p1[0]}' y2='{p1[1]}' "
            f"stroke='#000000' stroke-width='{sw}' stroke-linecap='round'/>"
        )
    return lines


def _connector_lines() -> List[str]:
    """Return SVG dotted <line> elements connecting each cube corner to its mirror corner.

    For each hidden face mirror, the 4 corners of the mirror correspond to the 4 corners
    of the cube face they were 'slid out' from.  We draw dotted lines between them.
    """
    sw   = 0.022   # stroke width
    dash = '0.07,0.05'  # dash pattern

    # Each pair: (cube_corner_3d, mirror_corner_3d)
    # L mirror corners: the L face (x=0) corners slide to x=-gap_L
    # D mirror corners: the D face (z=0) corners slide to z=-gap_D
    # B mirror corners: the B face (y=1) corners slide to y=1+gap_B
    connector_pairs = []

    gL = _MIRROR_GAP_L
    for xyz in [(0,0,1), (0,1,1), (0,0,0), (0,1,0)]:
        connector_pairs.append((xyz, (xyz[0]-gL, xyz[1], xyz[2])))

    gD = _MIRROR_GAP_D
    for xyz in [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]:
        connector_pairs.append((xyz, (xyz[0], xyz[1], xyz[2]-gD)))

    gB = _MIRROR_GAP_B
    for xyz in [(0,1,0), (1,1,0), (0,1,1), (1,1,1)]:
        connector_pairs.append((xyz, (xyz[0], xyz[1]+gB, xyz[2])))

    lines = []
    for cube_xyz, mirror_xyz in connector_pairs:
        p0 = _proj(*cube_xyz)
        p1 = _proj(*mirror_xyz)
        lines.append(
            f"    <line x1='{p0[0]}' y1='{p0[1]}' x2='{p1[0]}' y2='{p1[1]}' "
            f"stroke='#888888' stroke-width='{sw}' stroke-dasharray='{dash}' "
            f"stroke-linecap='round'/>"
        )
    return lines


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
    lines = [f"  <g {transform} style='stroke:#000000;stroke-width:0.028;"
             f"stroke-linejoin:round;stroke-linecap:round'>"]

    # ── Dotted connector lines (drawn first, behind everything) ──────────────
    lines.extend(_connector_lines())

    # ── Sticker polygons ─────────────────────────────────────────────────────
    # Polygon index → (face_enum, sticker_pos) mapping.
    #
    # Face tile origins and col/row directions (from _build_exploded_polygons):
    #
    # R face: origin=TBR=(1,1,1), u→-y (toward front), v→-z (toward bottom)
    #   tile(0,0)=TBR area=R[0], tile(0,2)=TFR area=R[2], tile(2,0)=BBR=R[6], tile(2,2)=BFR=R[8]
    #   → standard mapping: tile(r,c)→R[r*3+c]
    #
    # U face: origin=TBL=(0,1,1), u→+x, v→-y (toward front)
    #   tile(0,0)=TBL=U[0], tile(0,2)=TBR=U[2], tile(2,0)=TFL=U[6], tile(2,2)=TFR=U[8]
    #   → standard mapping: tile(r,c)→U[r*3+c]
    #
    # F face: origin=TFL=(0,0,1), u→+x, v→-z
    #   tile(0,0)=TFL=F[0], tile(0,2)=TFR=F[2], tile(2,0)=BFL=F[6], tile(2,2)=BFR=F[8]
    #   → standard mapping: tile(r,c)→F[r*3+c]
    #
    # L mirror: origin=(0-gap,0,1), u→+y, v→-z
    #   tile(0,0)=(−gap,0,1)=front-top, tile(0,2)=(−gap,1,1)=back-top
    #   L sticker viewed from outside (-x): left=back(y=1), right=front(y=0)
    #   L[0]=top-back=tile(0,2), L[2]=top-front=tile(0,0)
    #   → tile(r,c) → L[r*3 + (2-c)]  (column reversed)
    #
    # D mirror: origin=(0,1,−gap), u→+x, v→-y (toward front, decreasing y)
    #   tile(0,0)=(0,1,−gap)=back-left, tile(2,0)=(0,0,−gap)=front-left
    #   D sticker viewed from outside (-z, looking up): top=back, left=x=0
    #   D[0]=back-left=tile(0,0), D[6]=front-left=tile(2,0) ← but viewer sees it from above!
    #   From above (+z looking down): front (y=0) is NEAREST and should appear
    #   at the top of the mirror (closest to cube). In screen: tile(0) has smaller sy
    #   (higher), so tile(0,0) is the upper-back part. The NEAR part (front, y=0)
    #   is tile(row=2). For a natural "mirror" view: D[6..8] (front row, nearest F face)
    #   should appear at the TOP of the D mirror → tile(row=0).
    #   → tile(r,c) → D[(2-r)*3 + c]  (row reversed)
    #
    # B mirror: origin=(1,1+gap,1), u→-x, v→-z
    #   tile(0,0)=(1,1+gap,1)=right-top, tile(0,2)=(0,1+gap,1)=left-top
    #   B sticker viewed from outside (+y, looking toward -y):
    #   left=x=1(right of cube from front), right=x=0, so columns are reversed relative to front.
    #   B[0]=top-left from back=top of x=1=tile(0,0), B[2]=top of x=0=tile(0,2)
    #   → standard mapping: tile(r,c)→B[r*3+c]
    sticker_order = [
        # outlines (thick border drawn separately, these just serve as face background)
        (0, None), (1, None), (2, None),
        # R face
        (3,  (R, 0)), (4,  (R, 1)), (5,  (R, 2)),
        (6,  (R, 3)), (7,  (R, 4)), (8,  (R, 5)),
        (9,  (R, 6)), (10, (R, 7)), (11, (R, 8)),
        # U face
        (12, (U, 0)), (13, (U, 1)), (14, (U, 2)),
        (15, (U, 3)), (16, (U, 4)), (17, (U, 5)),
        (18, (U, 6)), (19, (U, 7)), (20, (U, 8)),
        # F face
        (21, (F, 0)), (22, (F, 1)), (23, (F, 2)),
        (24, (F, 3)), (25, (F, 4)), (26, (F, 5)),
        (27, (F, 6)), (28, (F, 7)), (29, (F, 8)),
        # L mirror – columns reversed: tile(r,c) → L[r*3+(2-c)]
        (30, (L, 2)), (31, (L, 1)), (32, (L, 0)),
        (33, (L, 5)), (34, (L, 4)), (35, (L, 3)),
        (36, (L, 8)), (37, (L, 7)), (38, (L, 6)),
        # D mirror – rows reversed: tile(r,c) → D[(2-r)*3+c]
        (39, (D, 6)), (40, (D, 7)), (41, (D, 8)),
        (42, (D, 3)), (43, (D, 4)), (44, (D, 5)),
        (45, (D, 0)), (46, (D, 1)), (47, (D, 2)),
        # B mirror – standard: tile(r,c) → B[r*3+c]
        (48, (B, 0)), (49, (B, 1)), (50, (B, 2)),
        (51, (B, 3)), (52, (B, 4)), (53, (B, 5)),
        (54, (B, 6)), (55, (B, 7)), (56, (B, 8)),
    ]

    for poly_idx, face_info in sticker_order:
        points_str = EXPLODED_POLYGONS[poly_idx]
        if face_info is None:
            lines.append(f"    <polygon fill='none' stroke='#000000' "
                         f"stroke-width='0.06' points='{points_str}'/>")
        else:
            face, pos = face_info
            color_char = state[_idx(face, pos)]
            color = color_map.get(color_char, '#CCCCCC')
            lines.append(f"    <polygon fill='{color}' stroke='#000000' "
                         f"points='{points_str}'/>")

    # ── Bold cube edges on top ────────────────────────────────────────────────
    lines.extend(_cube_edge_lines())

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
    # Scale so the full viewBox fits inside cell_size in the larger dimension.
    scale = cell_size / max(_VB_W, _VB_H)
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
        # Cube position: centered in cell.
        # The viewBox centre in 3D-engine coords is (_VB_X0 + _VB_W/2, _VB_Y0 + _VB_H/2).
        cx = i * cell_step + cell_size / 2
        cy = cell_size / 2
        vb_cx = _VB_X0 + _VB_W / 2
        vb_cy = _VB_Y0 + _VB_H / 2
        ox = cx - vb_cx * scale
        oy = cy - vb_cy * scale
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
