#!/usr/bin/env python3
"""Rubik's Cube SVG Guide Generator.

Generates complete step-by-step solving guides with cube state visualizations
and algorithms, exported as SVG or HTML documents.

Usage:
  python gen_rubik_guide.py --guide                  # Full guide
  python gen_rubik_guide.py --test                   # Test solved cube
  python gen_rubik_guide.py --state "wwwww..." --moves "R U R'"  # Custom
"""

import argparse
import glob
import math
import os
import subprocess
from typing import List

# Cube faces (positions and stickers)
U, D, F, B, R, L = 0, 1, 2, 3, 4, 5

# Facelet indices: U=0-8, D=9-17, F=18-26, B=27-35, R=36-44, L=45-53
# Grid layout per face:  0 1 2 / 3 4 5 / 6 7 8


def _idx(face: int, pos: int) -> int:
    """Convert face and position to absolute facelet index."""
    return face * 9 + pos


# Face rotation indices for 90° CW and CCW (re-index stickers on rotated face)
CW_FACE = [2, 5, 8, 1, 4, 7, 0, 3, 6]
CCW_FACE = [6, 3, 0, 7, 4, 1, 8, 5, 2]

MOVE_DEFS = {
    # Format: (face_to_rotate, face_positions, cw_index, adjacent_cycles)
    # Cycles rotate 4 stickers: [pos1, pos2, pos3, pos4] → pos1←pos4, pos2←pos1, pos3←pos2, pos4←pos3
    'U': (U, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        [_idx(F, 0), _idx(L, 0), _idx(B, 0), _idx(R, 0)],
        [_idx(F, 1), _idx(L, 1), _idx(B, 1), _idx(R, 1)],
        [_idx(F, 2), _idx(L, 2), _idx(B, 2), _idx(R, 2)],
    ]),
    'D': (D, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        [_idx(F, 6), _idx(R, 6), _idx(B, 6), _idx(L, 6)],
        [_idx(F, 7), _idx(R, 7), _idx(B, 7), _idx(L, 7)],
        [_idx(F, 8), _idx(R, 8), _idx(B, 8), _idx(L, 8)],
    ]),
    'F': (F, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        [_idx(U, 6), _idx(R, 0), _idx(D, 2), _idx(L, 8)],
        [_idx(U, 7), _idx(R, 3), _idx(D, 1), _idx(L, 5)],
        [_idx(U, 8), _idx(R, 6), _idx(D, 0), _idx(L, 2)],
    ]),
    'B': (B, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        [_idx(U, 0), _idx(L, 0), _idx(D, 8), _idx(R, 8)],
        [_idx(U, 1), _idx(L, 3), _idx(D, 7), _idx(R, 5)],
        [_idx(U, 2), _idx(L, 6), _idx(D, 6), _idx(R, 2)],
    ]),
    'R': (R, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        [_idx(F, 2), _idx(U, 2), _idx(B, 6), _idx(D, 2)],
        [_idx(F, 5), _idx(U, 5), _idx(B, 3), _idx(D, 5)],
        [_idx(F, 8), _idx(U, 8), _idx(B, 0), _idx(D, 8)],
    ]),
    'L': (L, [0,1,2,3,4,5,6,7,8], CCW_FACE, [
        [_idx(F, 0), _idx(D, 0), _idx(B, 8), _idx(U, 0)],
        [_idx(F, 3), _idx(D, 3), _idx(B, 5), _idx(U, 3)],
        [_idx(F, 6), _idx(D, 6), _idx(B, 2), _idx(U, 6)],
    ]),
    'M': (U, [], [], [
        [_idx(U, 1), _idx(F, 1), _idx(D, 1), _idx(B, 7)],
        [_idx(U, 4), _idx(F, 4), _idx(D, 4), _idx(B, 4)],
        [_idx(U, 7), _idx(F, 7), _idx(D, 7), _idx(B, 1)],
    ]),
}

# Cube states
SOLVED = list('wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg')

GOAL_STATES = {
    '01_white_cross': list('dwdwwwdwd' + 'ddddydddd' + 'drddrdddd' + 'doddodddd' + 'dbddbdddd' + 'dgddgdddd'),
    '02_white_corners': list('w'*9 + 'ddddydddd' + 'rrrdrdddd' + 'ooododddd' + 'bbbdbdddd' + 'gggdgdddd'),
    '03_middle_layer': list('ddddydddd' + 'w'*9 + 'ddddbbbbb' + 'ddddgdggg' + 'dddrrdrrr' + 'ddddodooo'),
    '04_orient_yellow_cross': list('dydyyydyd' + 'w'*9 + 'dddbbbbbb' + 'dddgggggg' + 'dddrrrrrr' + 'dddoooooo'),
    '05_permute_yellow_edges': list('dydyyydyd' + 'w'*9 + 'dbdbbbbbb' + 'dgdgggggg' + 'drdrrrrrr' + 'dodoooooo'),
    '06_permute_last_layer': list('lydyyydyy' + 'w'*9 + 'dbbbbbbbb' + 'dglgggggg' + 'rrdrrrrrr' + 'lodoooooo'),
    '07_orient_last_layer': list('y'*9 + 'w'*9 + 'b'*9 + 'g'*9 + 'r'*9 + 'o'*9),
}

STEPS = {
    '01_white_cross': [
        {'variant': 'upside-down', 'label': 'Upside down', 'algorithm': "FF"},
        {'variant': 'elevator', 'label': 'Elevator', 'algorithm': "F' U' R U"},
    ],
    '02_white_corners': [
        {'variant': 'elevator', 'label': 'Elevator on the right', 'algorithm': "F D F'"},
        {'variant': 'elevator-m', 'label': 'Elevator on the left', 'algorithm': "F' D' F", 'mirrored': True},
        {'variant': 'upside-down', 'label': 'Upside-down', 'algorithm': "R' DD R D",
         'goal': list('wwwwwwwwd' + 'ddbdydddd' + 'rrddrdddr' + 'ooododddd' + 'dbbdbdwdd' + 'gggdgdddd'),
         'suffix': '& repeat 2B'},
    ],
    '03_middle_layer': [
        {'variant': 'to-right', 'label': 'Insert right', 'algorithm': "U R U' R' U' F' U F"},
        {'variant': 'to-left', 'label': 'Insert left', 'algorithm': "U' L' U L U F U' F'", 'mirrored': True,
         'goal': list('ddddydddd' + 'w'*9 + 'dddbbdbbb' + 'ddddgdggg' + 'ddddrdrrr' + 'ddddooooo')},
    ],
    '04_orient_yellow_cross': [
        {'variant': 'minus', 'label': 'Minus', 'algorithm': "F R U R' U' F'"},
        {'variant': 'l-shape', 'label': 'L Shape', 'algorithm': "F U R U' R' F'"},
    ],
    '05_permute_yellow_edges': [
        {'variant': 'a', 'label': 'Swap Neighbours', 'algorithm': "R UU R' U' R U' R' U'"},
    ],
    '06_permute_last_layer': [
        {'variant': 'rotate', 'label': 'Rotate 3', 'algorithm': "L' U R U' L U R' U'"},
    ],
    '07_orient_last_layer': [
        {'variant': 'orient', 'label': 'Orient', 'algorithm': "L' UU L U L' U L R UU R' U' R U' R'"},
    ],
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
    valid_moves = {'R', 'L', 'U', 'D', 'F', 'B', 'M'}
    # If contains spaces, tokenize by whitespace
    if ' ' in algorithm:
        tokens = algorithm.split()
        moves = []
        for token in tokens:
            if token.endswith("'") or token.endswith("2"):
                moves.append(token)
            elif len(token) == 2 and token[0] in valid_moves and token[0] == token[1]:
                moves.append(token)
            else:
                moves.append(token)
        return moves
    # No spaces: parse character by character
    moves = []
    i = 0
    while i < len(algorithm):
        c = algorithm[i]
        if c in valid_moves:
            if i + 1 < len(algorithm) and algorithm[i + 1] == "'":
                moves.append(c + "'")
                i += 2
            elif i + 1 < len(algorithm) and algorithm[i + 1] == '2':
                moves.append(c + '2')
                i += 2
            elif i + 1 < len(algorithm) and algorithm[i + 1] == c:
                moves.append(c + c)
                i += 2
            else:
                moves.append(c)
                i += 1
        else:
            i += 1  # skip unexpected characters
    return moves


def invert_move(move: str) -> str:
    """Return the inverse of a move (R -> R', R' -> R, R2 -> R2, RR -> RR)."""
    if move.endswith("'"):
        return move[:-1]  # R' -> R
    elif move.endswith("2"):
        return move  # R2 -> R2
    elif len(move) == 2 and move[0] == move[1]:
        return move  # RR -> RR (self-inverse)
    else:
        return move + "'"  # R -> R'


def apply_move_sequence(state: List[str], moves: List[str]) -> List[str]:
    """Apply a sequence of moves (handling ', 2, and double-letter notation)."""
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
        elif len(move) == 2 and move[0] == move[1]:
            base_move = move[0]
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


# Vector math utilities
def _vec_sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def _vec_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _vec_cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def _vec_norm(a):
    m = math.sqrt(_vec_dot(a, a))
    return (a[0]/m, a[1]/m, a[2]/m)

# Camera configuration (azimuth=30°, elevation=30°)
_CAM_AZ_DEG  = 30.0
_CAM_EL_DEG  = 30.0
_CAM_DIST    = 4.0
_CAM_FOV     = 4.0
_target = (0.5, 0.5, 0.5)
_up_world = (0.0, 0.0, 1.0)

def _build_camera(az_deg):
    az = math.radians(az_deg)
    el = math.radians(_CAM_EL_DEG)
    cam = (
        _target[0] + _CAM_DIST * math.cos(el) * math.sin(az),
        _target[1] - _CAM_DIST * math.cos(el) * math.cos(az),
        _target[2] + _CAM_DIST * math.sin(el),
    )
    fwd   = _vec_norm(_vec_sub(_target, cam))
    right = _vec_norm(_vec_cross(fwd, _up_world))
    up    = _vec_cross(right, fwd)
    return cam, fwd, right, up

_CAM, _CAM_FWD, _CAM_RIGHT, _CAM_UP = _build_camera(_CAM_AZ_DEG)


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


# Face definitions (origin, col-direction, row-direction)
_R_FACE = ((1,1,1), (0,-1,0), (0,0,-1))
_U_FACE = ((0,1,1), (1,0,0),  (0,-1,0))
_F_FACE = ((0,0,1), (1,0,0),  (0,0,-1))
_L_FACE = ((0,0,1), (0,1,0),  (0,0,-1))
_D_FACE = ((0,1,0), (1,0,0),  (0,-1,0))
_B_FACE = ((1,1,1), (-1,0,0), (0,0,-1))

def _compute_mirror_gaps():
    """Compute 3D gaps for mirrors to avoid overlapping cube faces."""
    def all_cube_pts():
        pts = []
        for face in (_R_FACE, _U_FACE, _F_FACE):
            o, u, v = face
            for row in range(3):
                for col in range(3):
                    pts.extend(_tile_quad(o, u, v, row, col))
        return pts

    def screen_normal_of(dx3, dy3, dz3):
        p0 = _proj(0.5, 0.5, 0.5)
        p1 = _proj(0.5 + dx3, 0.5 + dy3, 0.5 + dz3)
        sdx, sdy = p1[0]-p0[0], p1[1]-p0[1]
        m = math.sqrt(sdx*sdx + sdy*sdy)
        return sdx/m, sdy/m

    def dot2(a, b):
        return a[0]*b[0] + a[1]*b[1]

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

def _shifted(face_def, dx, dy, dz):
    """Translate face origin by given offset."""
    o, u, v = face_def
    return ((o[0]+dx, o[1]+dy, o[2]+dz), u, v)

_L_MIRROR = _shifted(_L_FACE, -_MIRROR_GAP_L, 0, 0)
_D_MIRROR = _shifted(_D_FACE, 0, 0, -_MIRROR_GAP_D)
_B_MIRROR = _shifted(_B_FACE, 0, _MIRROR_GAP_B, 0)


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


EXPLODED_POLYGONS = _build_exploded_polygons()

# Compute viewbox from polygon extents
_VB_MARGIN = 0.04
_all_pts = [
    (float(tok.split(',')[0]), float(tok.split(',')[1]))
    for poly in EXPLODED_POLYGONS
    for tok in poly.split()
]
_VB_X0 = min(p[0] for p in _all_pts) - _VB_MARGIN
_VB_Y0 = min(p[1] for p in _all_pts) - _VB_MARGIN
_VB_W  = max(p[0] for p in _all_pts) - _VB_X0 + _VB_MARGIN
_VB_H  = max(p[1] for p in _all_pts) - _VB_Y0 + _VB_MARGIN

# Mirrored camera (az = -30°)
_CAM_M, _CAM_FWD_M, _CAM_RIGHT_M, _CAM_UP_M = _build_camera(-30.0)

def _proj_m(x: float, y: float, z: float):
    d = _vec_sub((x, y, z), _CAM_M)
    px = _vec_dot(d, _CAM_RIGHT_M)
    py = _vec_dot(d, _CAM_UP_M)
    pz = _vec_dot(d, _CAM_FWD_M)
    if pz < 0.01: pz = 0.01
    sx = px / pz * _CAM_FOV
    sy = -py / pz * _CAM_FOV
    return (sx, sy)

# Mirrored view setup (body faces = L, U, F; mirror faces = R, D, B)
_MIRROR_GAP_R_M = _MIRROR_GAP_L
_MIRROR_GAP_D_M = _MIRROR_GAP_D
_MIRROR_GAP_B_M = _MIRROR_GAP_B
_R_MIRROR_M = _shifted(_R_FACE, _MIRROR_GAP_R_M, 0, 0)
_D_MIRROR_M = _shifted(_D_FACE, 0, 0, -_MIRROR_GAP_D_M)
_B_MIRROR_M = _shifted(_B_FACE, 0, _MIRROR_GAP_B_M, 0)

def _tile_quad_proj(o, u, v, row, col, proj_fn, n=3):
    """Project tile quad using a custom projection function."""
    c0, c1 = col / n, (col + 1) / n
    r0, r1 = row / n, (row + 1) / n
    return [
        proj_fn(o[0]+c0*u[0]+r0*v[0], o[1]+c0*u[1]+r0*v[1], o[2]+c0*u[2]+r0*v[2]),
        proj_fn(o[0]+c1*u[0]+r0*v[0], o[1]+c1*u[1]+r0*v[1], o[2]+c1*u[2]+r0*v[2]),
        proj_fn(o[0]+c1*u[0]+r1*v[0], o[1]+c1*u[1]+r1*v[1], o[2]+c1*u[2]+r1*v[2]),
        proj_fn(o[0]+c0*u[0]+r1*v[0], o[1]+c0*u[1]+r1*v[1], o[2]+c0*u[2]+r1*v[2]),
    ]

def _build_mirrored_polygons() -> List[str]:
    """Build polygons for mirrored view using _proj_m."""
    polys = []
    for face in (_L_FACE, _U_FACE, _F_FACE):
        o, u, v = face
        corners = [
            _proj_m(*o),
            _proj_m(o[0]+u[0], o[1]+u[1], o[2]+u[2]),
            _proj_m(o[0]+u[0]+v[0], o[1]+u[1]+v[1], o[2]+u[2]+v[2]),
            _proj_m(o[0]+v[0], o[1]+v[1], o[2]+v[2]),
        ]
        polys.append(_fmt_poly(corners))
    for face in (_L_FACE, _U_FACE, _F_FACE):
        o, u, v = face
        for row in range(3):
            for col in range(3):
                polys.append(_fmt_poly(_tile_quad_proj(o, u, v, row, col, _proj_m)))
    for face in (_R_MIRROR_M, _D_MIRROR_M, _B_MIRROR_M):
        o, u, v = face
        for row in range(3):
            for col in range(3):
                polys.append(_fmt_poly(_tile_quad_proj(o, u, v, row, col, _proj_m)))
    return polys

EXPLODED_POLYGONS_M = _build_mirrored_polygons()

# Compute viewbox for mirrored view
_all_pts_m = [
    (float(tok.split(',')[0]), float(tok.split(',')[1]))
    for poly in EXPLODED_POLYGONS_M
    for tok in poly.split()
]
_VB_X0_M = min(p[0] for p in _all_pts_m) - _VB_MARGIN
_VB_Y0_M = min(p[1] for p in _all_pts_m) - _VB_MARGIN
_VB_W_M  = max(p[0] for p in _all_pts_m) - _VB_X0_M + _VB_MARGIN
_VB_H_M  = max(p[1] for p in _all_pts_m) - _VB_Y0_M + _VB_MARGIN

def _cube_edge_lines_mirrored() -> List[str]:
    """SVG lines for visible cube edges (mirrored view)."""
    edges_3d = [
        ((0,0,1), (0,1,1)),
        ((0,0,1), (1,0,1)),
        ((0,0,1), (0,0,0)),
    ]
    sw = 0.055
    lines = []
    for (x0,y0,z0), (x1,y1,z1) in edges_3d:
        p0 = _proj_m(x0, y0, z0)
        p1 = _proj_m(x1, y1, z1)
        lines.append(
            f"    <line x1='{p0[0]}' y1='{p0[1]}' x2='{p1[0]}' y2='{p1[1]}' "
            f"stroke='#000000' stroke-width='{sw}' stroke-linecap='round'/>"
        )
    return lines

def _connector_lines_mirrored() -> List[str]:
    """SVG dotted lines connecting cube corners to mirror corners (mirrored view)."""
    sw, dash = 0.022, '0.07,0.05'
    connector_pairs = []
    gR = _MIRROR_GAP_R_M
    for xyz in [(1,0,1), (1,1,1), (1,0,0), (1,1,0)]:
        connector_pairs.append((xyz, (xyz[0]+gR, xyz[1], xyz[2])))
    gD = _MIRROR_GAP_D_M
    for xyz in [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]:
        connector_pairs.append((xyz, (xyz[0], xyz[1], xyz[2]-gD)))
    gB = _MIRROR_GAP_B_M
    for xyz in [(0,1,0), (1,1,0), (0,1,1), (1,1,1)]:
        connector_pairs.append((xyz, (xyz[0], xyz[1]+gB, xyz[2])))
    lines = []
    for cube_xyz, mirror_xyz in connector_pairs:
        p0 = _proj_m(*cube_xyz)
        p1 = _proj_m(*mirror_xyz)
        lines.append(
            f"    <line x1='{p0[0]}' y1='{p0[1]}' x2='{p1[0]}' y2='{p1[1]}' "
            f"stroke='#888888' stroke-width='{sw}' stroke-dasharray='{dash}' "
            f"stroke-linecap='round'/>"
        )
    return lines


def _cube_edge_lines() -> List[str]:
    """SVG lines for visible cube edges (main view)."""
    edges_3d = [
        ((0,0,1), (1,0,1)),
        ((1,0,1), (1,1,1)),
        ((1,0,1), (1,0,0)),
    ]
    sw = 0.055
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
    """SVG dotted lines connecting cube corners to mirror corners (main view)."""
    sw = 0.022
    dash = '0.07,0.05'
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
                      scale: float = 1.0, mirrored: bool = False) -> str:
    """Render cube state as SVG group elements at given position and scale."""
    state = list(state)
    color_map = {
        'w': '#FFFFFF', 'y': '#FFD700', 'r': '#FF3333',
        'o': '#FF9500', 'b': '#0066FF', 'g': '#00AA44',
        'l': '#aaaaaa', 'd': '#777777',
    }
    if mirrored:
        return _render_cube_group_mirrored(state, ox, oy, scale, color_map)
    
    transform = f"transform='translate({ox},{oy}) scale({scale})'"
    lines = [f"  <g {transform} style='stroke:#000000;stroke-width:0.028;"
             f"stroke-linejoin:round;stroke-linecap:round'>"]

    lines.extend(_connector_lines())

    # Sticker order: polygon_idx → (face, position)
    # Polygons 0-2: face outlines (R, U, F)
    # Polygons 3-29: face stickers (R, U, F)
    # Polygons 30-56: mirror stickers (L, D, B)
    sticker_order = [
        (0, None), (1, None), (2, None),  # outlines
        # R, U, F faces
        (3, (R, 2)), (4, (R, 1)), (5, (R, 0)),
        (6, (R, 5)), (7, (R, 4)), (8, (R, 3)),
        (9, (R, 8)), (10, (R, 7)), (11, (R, 6)),
        (12, (U, 0)), (13, (U, 1)), (14, (U, 2)),
        (15, (U, 3)), (16, (U, 4)), (17, (U, 5)),
        (18, (U, 6)), (19, (U, 7)), (20, (U, 8)),
        (21, (F, 0)), (22, (F, 1)), (23, (F, 2)),
        (24, (F, 3)), (25, (F, 4)), (26, (F, 5)),
        (27, (F, 6)), (28, (F, 7)), (29, (F, 8)),
        # L, D, B mirrors (columns/rows reversed as needed)
        (30, (L, 2)), (31, (L, 1)), (32, (L, 0)),
        (33, (L, 5)), (34, (L, 4)), (35, (L, 3)),
        (36, (L, 8)), (37, (L, 7)), (38, (L, 6)),
        (39, (D, 6)), (40, (D, 7)), (41, (D, 8)),
        (42, (D, 3)), (43, (D, 4)), (44, (D, 5)),
        (45, (D, 0)), (46, (D, 1)), (47, (D, 2)),
        (48, (B, 0)), (49, (B, 1)), (50, (B, 2)),
        (51, (B, 3)), (52, (B, 4)), (53, (B, 5)),
        (54, (B, 6)), (55, (B, 7)), (56, (B, 8)),
    ]

    # Render mirrors first (behind), then cube faces
    for poly_idx in range(30, 57):
        face_info = sticker_order[poly_idx][1]
        points_str = EXPLODED_POLYGONS[poly_idx]
        face, pos = face_info
        color_char = state[_idx(face, pos)]
        color = color_map.get(color_char, '#CCCCCC')
        lines.append(f"    <polygon fill='{color}' stroke='#000000' "
                     f"points='{points_str}'/>")

    # Render cube faces and outlines
    tile_outline_stroke = 0.03
    for poly_idx in range(3, 30):
        face_info = sticker_order[poly_idx][1]
        points_str = EXPLODED_POLYGONS[poly_idx]
        if face_info is None:
            lines.append(f"    <polygon fill='none' stroke='#000000' "
                         f"stroke-width='{tile_outline_stroke}' points='{points_str}'/>")
        else:
            face, pos = face_info
            color_char = state[_idx(face, pos)]
            color = color_map.get(color_char, '#CCCCCC')
            lines.append(f"    <polygon fill='{color}' stroke='#000000' "
                         f"stroke-width='{tile_outline_stroke}' points='{points_str}'/>")

    lines.append("  </g>")
    return '\n'.join(lines)


def _render_cube_group_mirrored(state: List[str], ox: float, oy: float,
                                 scale: float, color_map: dict) -> str:
    """Render cube from mirrored perspective (az=-30)."""
    transform = f"transform='translate({ox},{oy}) scale({scale})'"
    lines = [f"  <g {transform} style='stroke:#000000;stroke-width:0.028;"
             f"stroke-linejoin:round;stroke-linecap:round'>"]

    lines.extend(_connector_lines_mirrored())

    sticker_order_m = [
        (0, None), (1, None), (2, None),
        # L, U, F (body)
        (3, (L, 2)), (4, (L, 1)), (5, (L, 0)),
        (6, (L, 5)), (7, (L, 4)), (8, (L, 3)),
        (9, (L, 8)), (10, (L, 7)), (11, (L, 6)),
        (12, (U, 0)), (13, (U, 1)), (14, (U, 2)),
        (15, (U, 3)), (16, (U, 4)), (17, (U, 5)),
        (18, (U, 6)), (19, (U, 7)), (20, (U, 8)),
        (21, (F, 0)), (22, (F, 1)), (23, (F, 2)),
        (24, (F, 3)), (25, (F, 4)), (26, (F, 5)),
        (27, (F, 6)), (28, (F, 7)), (29, (F, 8)),
        # R, D, B (mirrors)
        (30, (R, 2)), (31, (R, 1)), (32, (R, 0)),
        (33, (R, 5)), (34, (R, 4)), (35, (R, 3)),
        (36, (R, 8)), (37, (R, 7)), (38, (R, 6)),
        (39, (D, 6)), (40, (D, 7)), (41, (D, 8)),
        (42, (D, 3)), (43, (D, 4)), (44, (D, 5)),
        (45, (D, 0)), (46, (D, 1)), (47, (D, 2)),
        (48, (B, 0)), (49, (B, 1)), (50, (B, 2)),
        (51, (B, 3)), (52, (B, 4)), (53, (B, 5)),
        (54, (B, 6)), (55, (B, 7)), (56, (B, 8)),
    ]

    # Render mirrors first
    for poly_idx in range(30, 57):
        face_info = sticker_order_m[poly_idx][1]
        points_str = EXPLODED_POLYGONS_M[poly_idx]
        face, pos = face_info
        color_char = state[_idx(face, pos)]
        color = color_map.get(color_char, '#CCCCCC')
        lines.append(f"    <polygon fill='{color}' stroke='#000000' "
                     f"points='{points_str}'/>")

    # Render cube faces and outlines
    tile_outline_stroke = 0.03
    for poly_idx in range(3, 30):
        face_info = sticker_order_m[poly_idx][1]
        points_str = EXPLODED_POLYGONS_M[poly_idx]
        if face_info is None:
            lines.append(f"    <polygon fill='none' stroke='#000000' "
                         f"stroke-width='{tile_outline_stroke}' points='{points_str}'/>")
        else:
            face, pos = face_info
            color_char = state[_idx(face, pos)]
            color = color_map.get(color_char, '#CCCCCC')
            lines.append(f"    <polygon fill='{color}' stroke='#000000' "
                         f"stroke-width='{tile_outline_stroke}' points='{points_str}'/>")

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


def render_cube_svg(state: List[str], cell_size: int = 120,
                    label_height: int = 0, mirrored: bool = False) -> str:
    """Render a single cube state as a standalone SVG.

    Result is a complete <svg> document sized cell_size x (cell_size + label_height).
    The cube visual sits in the top cell_size portion; label_height adds white space below.
    """
    total_height = cell_size + label_height
    if mirrored:
        vb_w, vb_h = _VB_W_M, _VB_H_M
        vb_x0, vb_y0 = _VB_X0_M, _VB_Y0_M
    else:
        vb_w, vb_h = _VB_W, _VB_H
        vb_x0, vb_y0 = _VB_X0, _VB_Y0
    scale = cell_size / max(vb_w, vb_h)
    cx = cell_size / 2
    cy = cell_size / 2
    vb_cx = vb_x0 + vb_w / 2
    vb_cy = vb_y0 + vb_h / 2
    ox = cx - vb_cx * scale
    oy = cy - vb_cy * scale
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{cell_size}' height='{total_height}' "
        f"viewBox='0 0 {cell_size} {total_height}'>",
        f"  <rect fill='#FFFFFF' width='{cell_size}' height='{total_height}'/>",
        render_cube_group(state, ox, oy, scale, mirrored=mirrored),
        "</svg>",
    ]
    return '\n'.join(lines)


def _bare_move(move_label: str) -> str:
    """Extract the bare face letter from a move label (e.g. F' -> F, FF -> F)."""
    s = move_label.replace("'", "").replace("2", "")
    if len(s) == 2 and s[0] == s[1]:
        s = s[0]
    return s


def render_transition_svg(move_label: str, arrow_gap: int = 100) -> str:
    """Render a transition visualization as a 3x3 grid with a move arrow.

    For layer moves (U/D/R/L) a straight arrow spans the three affected tiles.
    For face moves (F) a rounded/spiral arrow sits across all nine tiles.
    A progress arrow below the grid points right toward the next state.
    The move label is drawn below the progress arrow.
    """
    C = 15
    GW = GH = C * 3
    SVG_W = GW + 2 * 5 + 1  # grid + margins + marker overhang
    GX = 5
    GY = 2
    CX = GX + GW / 2
    CY = GY + GH / 2
    AR = C * 0.6  # arc radius for F move
    ARROW_Y = GY + GH + 24
    LY = GY + GH + 17
    SVG_H = ARROW_Y + 6

    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{SVG_W}' height='{SVG_H}' "
        f"viewBox='0 0 {SVG_W} {SVG_H}'>",
        "  <defs>",
        "    <marker id='arr' viewBox='0 0 10 10' refX='8' refY='5'",
        "      markerWidth='4' markerHeight='4' orient='auto'>",
        "      <path d='M 0 0 L 10 5 L 0 10 z' fill='#333333'/>",
        "    </marker>",
                "    <marker id='arr-flip' viewBox='0 0 10 10' refX='10' refY='5'",
        "      markerWidth='4' markerHeight='4' orient='auto'>",
        "      <path d='M 10 0 L 0 5 L 10 10 z' fill='#333333'/>",
        "    </marker>",
        "    <marker id='arr-progress' viewBox='0 0 10 10' refX='8' refY='5'",
        "      markerWidth='4' markerHeight='4' orient='auto'>",
        "      <path d='M 0 0 L 10 5 L 0 10 z' fill='#cccccc'/>",
        "    </marker>",


        "  </defs>",
        f"  <rect x='{GX}' y='{GY}' width='{GW}' height='{GH}' "
        f"fill='#f0f0f0' stroke='#888' stroke-width='1'/>",
        f"  <line x1='{GX + C}' y1='{GY}' x2='{GX + C}' y2='{GY + GH}' stroke='#aaa' stroke-width='0.5'/>",
        f"  <line x1='{GX + 2*C}' y1='{GY}' x2='{GX + 2*C}' y2='{GY + GH}' stroke='#aaa' stroke-width='0.5'/>",
        f"  <line x1='{GX}' y1='{GY + C}' x2='{GX + GW}' y2='{GY + C}' stroke='#aaa' stroke-width='0.5'/>",
        f"  <line x1='{GX}' y1='{GY + 2*C}' x2='{GX + GW}' y2='{GY + 2*C}' stroke='#aaa' stroke-width='0.5'/>",
    ]

    bare = _bare_move(move_label)

    if bare == 'F':
        if "'" in move_label.replace("2", ""):
            lines.append(
                f"  <path d='M {CX:.1f},{CY - AR:.1f} A {AR:.1f},{AR:.1f} 0 1,0 {CX + AR:.1f},{CY:.1f}' "
                "fill='none' stroke='#333' stroke-width='2.5' marker-end='url(#arr-flip)'/>")
        else:
            lines.append(
                f"  <path d='M {CX:.1f},{CY - AR:.1f} A {AR:.1f},{AR:.1f} 0 1,1 {CX - AR:.1f},{CY:.1f}' "
                "fill='none' stroke='#333' stroke-width='2.5' marker-end='url(#arr-flip)'/>")
    elif bare == 'U':
        my = GY + C // 2
        if "'" in move_label:
            lines.append(
                f"  <line x1='{GX + 3}' y1='{my}' x2='{GX + GW - 3}' y2='{my}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
        else:
            lines.append(
                f"  <line x1='{GX + GW - 3}' y1='{my}' x2='{GX + 3}' y2='{my}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
    elif bare == 'D':
        my = GY + 2 * C + C // 2
        if "'" in move_label:
            lines.append(
                f"  <line x1='{GX + GW - 3}' y1='{my}' x2='{GX + 3}' y2='{my}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
        else:
            lines.append(
                f"  <line x1='{GX + 3}' y1='{my}' x2='{GX + GW - 3}' y2='{my}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
    elif bare == 'R':
        mx = GX + 2 * C + C // 2
        if "'" in move_label:
            lines.append(
                f"  <line x1='{mx}' y1='{GY + 3}' x2='{mx}' y2='{GY + GH - 3}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
        else:
            lines.append(
                f"  <line x1='{mx}' y1='{GY + GH - 3}' x2='{mx}' y2='{GY + 3}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
    elif bare == 'L':
        mx = GX + C // 2
        if "'" in move_label:
            lines.append(
                f"  <line x1='{mx}' y1='{GY + GH - 3}' x2='{mx}' y2='{GY + 3}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")
        else:
            lines.append(
                f"  <line x1='{mx}' y1='{GY + 3}' x2='{mx}' y2='{GY + GH - 3}' "
                f"stroke='#333' stroke-width='2.5' marker-end='url(#arr)'/>")

    lines.append(
        f"  <text x='{SVG_W / 2}' y='{LY}' "
        f"text-anchor='middle' font-family='Consolas, monospace' font-size='14' "
        f"fill='#333333'>{move_label}</text>")
    lines.append(
        f"  <line x1='{GX + 3}' y1='{ARROW_Y}' x2='{GX + GW - 3}' y2='{ARROW_Y}' "
        f"stroke='#ccc' stroke-width='1.5' marker-end='url(#arr-progress)'/>")
    lines.append("</svg>")
    return '\n'.join(lines)


def render_svg_notation() -> str:
    """Generate SVG documenting cube move notation with visual examples."""
    W, H = 1040, 760
    SCALE = 82.0
    PCX, PCY = 280.0, 385.0
    vb_cx = _VB_X0 + _VB_W / 2
    vb_cy = _VB_Y0 + _VB_H / 2
    ox = PCX - vb_cx * SCALE
    oy = PCY - vb_cy * SCALE

    def p2p(x, y, z):
        """Project 3D point to screen with scale and offset."""
        sx, sy = _proj(x, y, z)
        return (ox + sx * SCALE, oy + sy * SCALE)

    # Face properties for notation diagram
    centers = {
        'R': (1.0, 0.5, 0.5), 'U': (0.5, 0.5, 1.0), 'F': (0.5, 0.0, 0.5),
        'L': (-_MIRROR_GAP_L, 0.5, 0.5), 'D': (0.5, 0.5, -_MIRROR_GAP_D),
        'B': (0.5, 1.0 + _MIRROR_GAP_B, 0.5),
    }
    axes = {
        'R': ((0, -1, 0), (0, 0, -1)), 'U': ((1, 0, 0), (0, -1, 0)),
        'F': ((1, 0, 0), (0, 0, -1)), 'L': ((0, 1, 0), (0, 0, -1)),
        'D': ((1, 0, 0), (0, -1, 0)), 'B': ((-1, 0, 0), (0, 0, -1)),
    }
    normals = {
        'R': (1, 0, 0), 'U': (0, 0, 1), 'F': (0, -1, 0),
        'L': (-1, 0, 0), 'D': (0, 0, -1), 'B': (0, 1, 0),
    }
    arrow_colors = {
        'R': '#FF3333', 'U': '#FFFFFF', 'F': '#0066FF',
        'L': '#FF9500', 'D': '#FFD700', 'B': '#00AA44',
    }
    RAD, SWEEP_DEG, AHS = 0.38, 160, 15
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' "
        f"viewBox='0 0 {W} {H}'>",
        f"  <rect fill='#F5F5F5' x='0' y='0' width='{W}' height='{H}'/>",
    ]
    lines.append(
        "  <text x='40' y='50' font-family='Arial,sans-serif' "
        "font-size='28' font-weight='bold' fill='#222'>"
        "Rubik's Cube Notation</text>"
    )
    lines.append(
        "  <text x='40' y='78' font-family='Arial,sans-serif' "
        "font-size='14' fill='#666'>"
        "Each letter means turning that face 90\u00b0 clockwise "
        "(as seen from outside)</text>"
    )
    lines.append(render_cube_group(SOLVED, ox, oy, SCALE))
    for name in ['R', 'U', 'F', 'L', 'D']:
        cx, cy, cz = centers[name]
        ax1, ax2 = axes[name]
        col = arrow_colors[name]
        fc = _proj(cx, cy, cz)
        nx, ny, nz = normals[name]
        fn = _proj(cx + nx * 0.01, cy + ny * 0.01, cz + nz * 0.01)
        sdx = fn[0] - fc[0]
        sdy = fn[1] - fc[1]
        sdm = math.hypot(sdx, sdy)
        if sdm > 1e-10:
            sdx /= sdm
            sdy /= sdm
        # Find best arc start position (most aligned with screen normal)
        best_t, best_dot = 0.0, -1e10
        for i in range(720):
            t = 2 * math.pi * i / 720
            px = cx + RAD * (math.cos(t) * ax1[0] + math.sin(t) * ax2[0])
            py = cy + RAD * (math.cos(t) * ax1[1] + math.sin(t) * ax2[1])
            pz = cz + RAD * (math.cos(t) * ax1[2] + math.sin(t) * ax2[2])
            ps = _proj(px, py, pz)
            dot = (ps[0] - fc[0]) * sdx + (ps[1] - fc[1]) * sdy
            if dot > best_dot:
                best_dot = dot
                best_t = t
        
        # Sweep from start to end
        t0 = best_t + math.radians(SWEEP_DEG)
        t1 = best_t
        if name in ('U', 'F'):
            t0 = best_t - math.radians(SWEEP_DEG)
            t1 = best_t
        
        # Sample arc
        n_seg = 32
        arc_pts = []
        for i in range(n_seg + 1):
            t = t0 + (t1 - t0) * i / n_seg
            px = cx + RAD * (math.cos(t) * ax1[0] + math.sin(t) * ax2[0])
            py = cy + RAD * (math.cos(t) * ax1[1] + math.sin(t) * ax2[1])
            pz = cz + RAD * (math.cos(t) * ax1[2] + math.sin(t) * ax2[2])
            arc_pts.append(p2p(px, py, pz))
        path_d = f"M {arc_pts[0][0]:.2f} {arc_pts[0][1]:.2f}"
        for pt in arc_pts[1:]:
            path_d += f" L {pt[0]:.2f} {pt[1]:.2f}"
        lines.append(
            f"  <path d='{path_d}' fill='none' stroke='#000' "
            f"stroke-width='5.5' stroke-linecap='round'/>"
        )
        lines.append(
            f"  <path d='{path_d}' fill='none' stroke='{col}' "
            f"stroke-width='4' stroke-linecap='round'/>"
        )
        tip_t = t1
        tx = cx + RAD * (math.cos(tip_t) * ax1[0] + math.sin(tip_t) * ax2[0])
        ty = cy + RAD * (math.cos(tip_t) * ax1[1] + math.sin(tip_t) * ax2[1])
        tz = cz + RAD * (math.cos(tip_t) * ax1[2] + math.sin(tip_t) * ax2[2])
        tip_p = p2p(tx, ty, tz)
        adx = sdx
        ady = sdy
        arr_angle = math.atan2(ady, adx)
        perp = arr_angle + math.pi / 2
        back = 0.55
        bx = tip_p[0] + AHS * back * adx
        by = tip_p[1] + AHS * back * ady
        hs = AHS * 0.6
        p1 = (bx + hs * math.cos(perp), by + hs * math.sin(perp))
        p2 = (bx - hs * math.cos(perp), by - hs * math.sin(perp))
        lines.append(
            f"  <polygon points='{tip_p[0]:.2f},{tip_p[1]:.2f} "
            f"{p1[0]:.2f},{p1[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}' "
            f"fill='{col}' stroke='#000' stroke-width='1.5' stroke-linejoin='round'/>"
        )
        badge_dist = 38
        badge_x = tip_p[0] + badge_dist * adx
        badge_y = tip_p[1] + badge_dist * ady
        lines.append(
            f"  <circle cx='{badge_x:.1f}' cy='{badge_y:.1f}' "
            f"r='14' fill='{col}' stroke='#FFF' stroke-width='2.5'/>"
        )
        lines.append(
            f"  <text x='{badge_x:.1f}' y='{badge_y + 5.5:.1f}' "
            f"text-anchor='middle' font-family='Arial,sans-serif' "
            f"font-size='16' font-weight='bold' fill='#FFF'>"
            f"{name}</text>"
        )
    legend_x = 580
    legend_y = 150
    lines.append(
        f"  <rect x='{legend_x - 20}' y='{legend_y - 30}' "
        f"width='420' height='420' rx='12' fill='#FFF' "
        f"stroke='#DDD' stroke-width='1.5'/>"
    )
    lines.append(
        f"  <text x='{legend_x}' y='{legend_y + 10}' "
        f"font-family='Arial,sans-serif' font-size='20' font-weight='bold' "
        f"fill='#333'>Face Moves</text>"
    )
    face_names = {
        'R': 'Right face', 'U': 'Upper face', 'F': 'Front face',
        'L': 'Left face', 'D': 'Down face', 'B': 'Back face',
    }
    ly = legend_y + 55
    for name in ['R', 'U', 'F', 'L', 'D']:
        lines.append(
            f"  <circle cx='{legend_x + 12}' cy='{ly}' r='9' "
            f"fill='{arrow_colors[name]}'/>"
        )
        lines.append(
            f"  <text x='{legend_x + 12}' y='{ly + 4}' text-anchor='middle' "
            f"font-family='Arial,sans-serif' font-size='11' font-weight='bold' "
            f"fill='#FFF'>{name}</text>"
        )
        lines.append(
            f"  <text x='{legend_x + 35}' y='{ly + 5}' "
            f"font-family='Arial,sans-serif' font-size='15' "
            f"fill='#444'>{face_names[name]}</text>"
        )
        ly += 35
    ly += 15
    lines.append(
        f"  <text x='{legend_x}' y='{ly}' "
        f"font-family='Arial,sans-serif' font-size='18' font-weight='bold' "
        f"fill='#333'>Suffix Rules</text>"
    )
    ly += 35
    for label, desc in [
        ('R', 'Clockwise (no suffix)'),
        ("R'", 'Counter-clockwise (apostrophe)'),
        ('RR', 'Half turn (180\u00b0)'),
    ]:
        lines.append(
            f"  <text x='{legend_x}' y='{ly}' "
            f"font-family='monospace' font-size='16' font-weight='bold' "
            f"fill='#333'>{label}</text>"
        )
        lines.append(
            f"  <text x='{legend_x + 55}' y='{ly}' "
            f"font-family='Arial,sans-serif' font-size='15' "
            f"fill='#666'>\u2014  {desc}</text>"
        )
        ly += 30
    ly += 10
    lines.append(
        f"  <text x='{legend_x}' y='{ly}' "
        f"font-family='Arial,sans-serif' font-size='16' font-weight='bold' "
        f"fill='#333'>Special Moves</text>"
    )
    ly += 30
    lines.append(
        f"  <text x='{legend_x}' y='{ly}' "
        f"font-family='monospace' font-size='15' font-weight='bold' "
        f"fill='#333'>M</text>"
    )
    lines.append(
        f"  <text x='{legend_x + 55}' y='{ly}' "
        f"font-family='Arial,sans-serif' font-size='15' fill='#666'>"
        f"\u2014  Middle slice (like D, between R and L)</text>"
    )
    lines.append("</svg>")
    return '\n'.join(lines)


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


def step_title(step_name: str) -> str:
    """Convert '01_white_cross' to '1. White Cross' with optional emoji."""
    parts = step_name.split('_', 1)
    num = parts[0].lstrip('0')
    name = parts[1].replace('_', ' ').title() if len(parts) > 1 else ''
    emoji = {'03_middle_layer': '\U0001F503 '}.get(step_name, '')
    return f'{emoji}{num}. {name}'


_STEP_LETTER = 'ABCDEFGH'


def variant_label(step_name: str, step_idx: int, label: str, alg: str) -> str:
    """Build variant label like '1A. Upside down: <span class="alg">FF</span>'."""
    step_num = step_name.split('_', 1)[0].lstrip('0')
    letter = _STEP_LETTER[step_idx]
    return f'{step_num}{letter}. {label}: <span class="alg">{alg}</span>'


def generate_guide(output_dir: str = 'docs/rubik-for-dummies/assets', short: bool = False):
    """Generate all steps: per-move cube SVGs, shared transition SVGs, and rubik_guide.html.
    
    When short=True, each variant shows only the first state, all transitions, and the last state.
    """
    os.makedirs(output_dir, exist_ok=True)
    parent_dir = os.path.dirname(output_dir.rstrip('/'))
    assets_prefix = os.path.basename(output_dir.rstrip('/')) + '/'

    total = 0

    # First pass: collect all unique move labels across every variant
    all_unique_moves = set()
    for _step_name, variants in STEPS.items():
        for variant in variants:
            all_unique_moves.update(parse_algorithm(variant['algorithm']))

    # Generate one shared transition SVG per unique move label
    def _transition_filename(label: str) -> str:
        return f'transition-{label.replace("'", "-prime")}.svg'

    transition_cache = {}
    for move_label in sorted(all_unique_moves):
        svg = render_transition_svg(move_label, arrow_gap=50)
        name = _transition_filename(move_label)
        path = os.path.join(output_dir, name)
        with open(path, 'w') as f:
            f.write(svg)
        transition_cache[move_label] = name
        total += 1

    # Second pass: generate cube SVGs and collect variant data
    variant_data = []  # list of (step_name, step_idx, label, alg, state_files, arrow_files, suffix)

    for step_name, variants in STEPS.items():
        for idx, variant in enumerate(variants):
            alg = variant['algorithm']
            var_id = variant['variant']
            mirrored = variant.get('mirrored', False)
            suffix = variant.get('suffix', '')
            goal_state: list[str] = variant.get('goal', GOAL_STATES[step_name])
            moves = parse_algorithm(alg)

            # Compute start state (apply inverse to solved)
            inv_alg = inverse_algorithm(alg)
            start_state = apply_algorithm(goal_state, inv_alg)

            # Generate per-move sequence of states
            states = [start_state]
            current = list(start_state)
            for move in moves:
                current = apply_move_sequence(current, [move])
                states.append(list(current))

            prefix = f'{step_name}_{var_id}'

            # Write individual cube state SVGs
            state_files = []
            for i, s in enumerate(states):
                svg = render_cube_svg(s, cell_size=240, mirrored=mirrored)
                name = f'{prefix}_s{i}.svg'
                path = os.path.join(output_dir, name)
                with open(path, 'w') as f:
                    f.write(svg)
                state_files.append(name)
                total += 1

            # Reference shared transition SVGs
            arrow_files = [transition_cache[m] for m in moves]

            label = variant.get('label', var_id)
            variant_data.append((step_name, idx, label, alg, state_files, arrow_files, suffix))

            print(f"  {step_name}/{var_id}: {len(state_files)} states + "
                  f"{len(arrow_files)} arrows")

    # Build HTML body
    body = []
    body.append('<p class="title">Rubik\'s Cube for Dummies</p>')
    body.append('')

    body.append('<h2>Moves Notation</h2>')
    body.append('')
    body.append('<div class="notation">')
    body.append(f'  <img class="notation-img" src="{assets_prefix}notation-alt.svg" alt="Move Notation">')
    body.append(f'  <img class="notation-img" src="{assets_prefix}notation-prime-alt.svg" alt="Move Notation Prime">')
    body.append('</div>')
    body.append('')

    current_step = None
    for step_name, idx, label, alg, state_files, arrow_files, suffix in variant_data:
        if step_name != current_step:
            body.append(f'<h2>{step_title(step_name)}</h2>')
            body.append('')
            current_step = step_name

        label_html = variant_label(step_name, idx, label, alg)
        body.append('<div class="variant">')
        body.append(f'  <div class="label">{label_html}</div>')
        body.append('  <div class="seq-row">')
        if short:
            body.append(f'    <img class="cube" src="{assets_prefix}{state_files[0]}">')
            for a in arrow_files:
                body.append(f'    <img class="transition" src="{assets_prefix}{a}">')
            body.append(f'    <img class="cube" src="{assets_prefix}{state_files[-1]}">')
        else:
            for i in range(len(state_files)):
                body.append(f'    <img class="cube" src="{assets_prefix}{state_files[i]}">')
                if i < len(arrow_files):
                    body.append(f'    <img class="transition" src="{assets_prefix}{arrow_files[i]}">')
        body.append('  </div>')
        if suffix:
            body.append(f'  {suffix}')
        body.append('</div>')
        body.append('')

    css_file = 'guide-short.css' if short else 'guide.css'
    title = 'Rubik\'s Cube for Dummies (short)' if short else 'Rubik\'s Cube for Dummies'
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=297mm">
<title>{title}</title>
<link rel="stylesheet" href="assets/{css_file}">
</head>
<body>

{chr(10).join(body)}

</body>
</html>
"""

    html_name = 'guide-short.html' if short else 'rubik_guide.html'
    html_path = os.path.join(parent_dir, html_name)
    with open(html_path, 'w') as f:
        f.write(html)
    print(f"  root HTML = {html_path}")
    total += 1

    print(f"\nDone! Generated {total} files")


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
    parser.add_argument('--guide-short', action='store_true',
                        help='Generate short guide (first cube, transitions, last cube)')
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
    
    if args.guide or args.guide_short:
        out_dir = args.output or 'docs/rubik-for-dummies/assets'
        generate_guide(out_dir, short=args.guide_short)
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
