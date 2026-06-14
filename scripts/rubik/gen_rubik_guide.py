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
# SVG RENDERING
# ============================================================================

# Fixed exploded view polygon coordinates (from test_exploded_cube.html)
EXPLODED_POLYGONS = [
    # Outline (3 black polygons) - indices 0-2
    '0.20684405736417,-0.10342202868208 0.65400098857461,-0.50223953102503 0.59354043975904,0.29677021987952 0.18464331255837,0.78141988002483',
    '-0.16103316974267,-0.68150055605482 0.65400098857461,-0.50223953102503 0.20684405736417,-0.10342202868208 -0.69915174967186,-0.34957587483593',
    '-0.69915174967186,-0.34957587483593 0.20684405736417,-0.10342202868208 0.18464331255837,0.78141988002483 -0.63049311492991,0.48418667844381',
    
    # Main cube stickers (27 - visible from U+F+R view) - indices 3-29
    '0.23220459330744,-0.097441401330956 0.38227249092114,-0.23128636700361 0.36999212937981,0.045154977624192 0.22499715953803,0.18982100852027',
    '0.4069817245562,-0.2545381490138 0.54094270983739,-0.37401742313938 0.52467144659853,-0.1077720348288 0.39470136301487,0.021903195614004',
    '0.56310093386749,-0.39487439578917 0.68341608451396,-0.50218300385423 0.66399522435527,-0.24552875671726 0.54682967062863,-0.12862900747859',
    '0.223353818639,0.23784491367276 0.36834878848078,0.093178882776681 0.35693169206116,0.350187397987 0.21668124027086,0.50378990925302',
    '0.3922779720275,0.06821860554084 0.52224805561116,-0.061456624901962 0.50706331929562,0.18701000964104 0.38086087560788,0.32522712075116',
    '0.54378933560067,-0.083930885138136 0.6609548893273,-0.20083063437682 0.6427690222492,0.039502697171029 0.52860459928513,0.16453574940487',
    '0.21515350390181,0.54839286735931 0.35540395569211,0.3947903560933 0.34476218854429,0.63434555238436 0.20895837445964,0.79530846448196',
    '0.37860023265147,0.36841120720791 0.50480267633921,0.23019409609779 0.49059915258614,0.46260522739722 0.36795846550365,0.60796640349897',
    '0.52575903029008,0.20635820880183 0.63992345325415,0.081325156567985 0.6228584076258,0.30684639519048 0.51155550653701,0.43876934010126',
    
    # Top-left area stickers (9) - indices 12-20
    '-0.16308766923626,-0.71207714627716 0.06893319498559,-0.66104579069008 -0.069879916590964,-0.56561143321124 -0.30935815523295,-0.62185393851769',
    '0.11180610591039,-0.65128217351647 0.35708263835866,-0.59733532702698 0.22686512059301,-0.4962248436571 -0.027007005666167,-0.55584781603763',
    '0.40251326858017,-0.58698845898221 0.66221484485652,-0.5298689256595 0.54189969421005,-0.42256031759443 0.27229575081453,-0.48587797561233',
    '-0.33581637736973,-0.60457603181805 -0.096338138727745,-0.54833352651161 -0.24992750361457,-0.44274045834187 -0.49719274936492,-0.5050351446816',
    '-0.052006830500575,-0.53752584778919 0.20186529575861,-0.47790287540865 0.057347059211871,-0.36568825940513 -0.2055961953874,-0.43193277961945',
    '0.24898588289863,-0.46641417348037 0.51858982629416,-0.40309651546248 0.38462884101296,-0.2836172413369 0.10446764635189,-0.35419955747685',
    '-0.52650751013751,-0.48588756542377 -0.27924226438716,-0.42359287908404 -0.45009984781468,-0.30612786796512 -0.70545724037948,-0.3755070017707',
    '-0.23338157689329,-0.41156389934697 0.029561677705984,-0.34531937913265 -0.13174994780725,-0.22006513754759 -0.4042391603208,-0.29409888822805',
    '0.078474752161267,-0.33248841791719 0.35863594682234,-0.26190610177724 0.20856804920864,-0.12806113610458 -0.082836873351964,-0.20723417633213',
    
    # Bottom-left area stickers (9) - indices 21-29
    '-0.72004575804874,-0.34151840727719 -0.46468836548394,-0.27213927347161 -0.45107516882697,0.0026842338018111 -0.69790099484541,-0.072601403908595',
    '-0.41897143950024,-0.25894568756878 -0.14648222698668,-0.18491193688833 -0.14259047425941,0.09602599279775 -0.40535824284327,0.015877819704637',
    '-0.097706202112198,-0.17083564826423 0.19369872044841,-0.091662608036674 0.18649128667899,0.19559980181455 -0.093814449384923,0.11010228142185',
    '-0.69482963515065,-0.026315135872389 -0.44800380913221,0.048970501838018 -0.43533982912821,0.30463120287977 -0.67418372027694,0.22440046260398',
    '-0.40383837771209,0.063133327157647 -0.14107060912822,0.14328150025076 -0.1374586676318,0.40402041077812 -0.39117439770808,0.3187940281994',
    '-0.094059816353234,0.15835665718065 0.18624591971068,0.24385417757335 0.17957334134255,0.5097991731536 -0.090447874856813,0.41909556770801',
    '-0.67131990143287,0.26756077772389 -0.43247601028413,0.34779151799968 -0.42066531159164,0.586226157549 -0.65202564383899,0.50186239958934',
    '-0.38976040593535,0.36276197672144 -0.13604467585907,0.44798835930017 -0.13268341577213,0.69063107484156 -0.37794970724287,0.60119661627076',
    '-0.090675803204967,0.46388861250066 0.17934541299439,0.55459221794625 0.17315028355223,0.8015078150689 -0.087314543118027,0.70653132804205',
    
    # Left face exploded (9 stickers from L, indices 45-53) - indices 30-38
    '-1.26779540669256,-0.347441401330956 -1.11772750907886,-0.48128636700361 -1.13000787062019,-0.20484502237580798 -1.27500284046197,-0.06017899147972999',
    '-1.0930182754438,-0.5045381490138 -0.95905729016261,-0.62401742313938 -0.97532855340147,-0.3577720348288 -1.10529863698513,-0.228096804385996',
    '-0.93689906613251,-0.64487439578917 -0.81658391548604,-0.75218300385423 -0.83600477564473,-0.49552875671726 -0.95317032937137,-0.37862900747858996',
    '-1.276646181361,-0.012155086327239994 -1.13165121151922,-0.15682111722331898 -1.14306830793874,0.100187397987 -1.28331875972914,0.25378990925302003',
    '-1.1077220279725,-0.18178139445916 -0.97775194438884,-0.311456624901962 -0.99293668070438,-0.06298999035896 -1.11913912439212,0.07522712075116',
    '-0.95621066439933,-0.333930885138136 -0.8390451106727,-0.45083063437682 -0.8572309777508,-0.210497302828971 -0.97139540071487,-0.08546425059512999',
    '-1.28484649609819,0.29839286735931003 -1.14459604430789,0.1447903560933 -1.15523781145571,0.38434555238435997 -1.29104162554036,0.54530846448196',
    '-1.12139976734853,0.11841120720790999 -0.99519732366079,-0.019805903902209987 -1.00940084741386,0.21260522739722 -1.13204153449635,0.35796640349897',
    '-0.97424096970992,-0.043641791198169994 -0.86007654674585,-0.168674843432015 -0.8771415923742,0.056846395190480015 -0.98844449346299,0.18876934010126',
    
    # Bottom face exploded (9 stickers from D, indices 9-17) - indices 39-47
    '-0.16308766923626,0.78792285372284 0.06893319498559,0.83895420930992 -0.069879916590964,0.93438856678876 -0.30935815523295,0.87814606148231',
    '0.11180610591039,0.84871782648353 0.35708263835866,0.90266467297302 0.22686512059301,1.0037751563429 -0.027007005666167,0.94415218396237',
    '0.40251326858017,0.91301154101779 0.66221484485652,0.9701310743405 0.54189969421005,1.07743968240557 0.27229575081453,1.01412202438767',
    '-0.33581637736973,0.89542396818195 -0.096338138727745,0.95166647348839 -0.24992750361457,1.05725954165813 -0.49719274936492,0.9949648553184',
    '-0.052006830500575,0.96247415221081 0.20186529575861,1.02209712459135 0.057347059211871,1.13431174059487 -0.2055961953874,1.06806722038055',
    '0.24898588289863,1.03358582651963 0.51858982629416,1.09690348453752 0.38462884101296,1.2163827586631 0.10446764635189,1.14580044252315',
    '-0.52650751013751,1.01411243457623 -0.27924226438716,1.07640712091596 -0.45009984781468,1.19387213203488 -0.70545724037948,1.1244929982293',
    '-0.23338157689329,1.08843610065303 0.029561677705984,1.15468062086735 -0.13174994780725,1.27993486245241 -0.4042391603208,1.20590111177195',
    '0.078474752161267,1.16751158208281 0.35863594682234,1.23809389822276 0.20856804920864,1.37193886389542 -0.082836873351964,1.29276582366787',

    # Back face exploded (9 stickers from B, shifted from F geometry - indices 48-56)
    '0.77995424195126,-1.34151840727719 1.03531163451606,-1.27213927347161 1.04892483117303,-0.9973157661981888 0.80209900515459,-1.072601403908595',
    '1.08102856049976,-1.25894568756878 1.3535177730133199,-1.18491193688833 1.35740952574059,-0.90397400720225 1.09464175715673,-0.984122180295363',
    '1.402293797887802,-1.17083564826423 1.69369872044841,-1.091662608036674 1.68649128667899,-0.80440019818545 1.406185550615077,-0.88989771857815',
    '0.80517036484935,-1.026315135872389 1.05199619086779,-0.951029498161982 1.06466017087179,-0.69536879712023 0.8258162797230599,-0.7755995373960201',
    '1.09616162228791,-0.936866672842353 1.3589293908717799,-0.85671849974924 1.3625413323682,-0.59597958922188 1.10882560229192,-0.6812059718006',
    '1.405940183646766,-0.8416433428193499 1.68624591971068,-0.75614582242665 1.67957334134255,-0.4902008268464 1.409552125143187,-0.5809044322919901',
    '0.8286800985671299,-0.73243922227611 1.06752398971587,-0.65220848200032 1.0793346884083599,-0.413773842451 0.84797435616101,-0.49813760041066',
    '1.11023959406465,-0.6372380232785599 1.36395532414093,-0.55201164069983 1.36731658422787,-0.30936892515843994 1.1220502927571299,-0.39880338372923996',
    '1.409324196795033,-0.53611138749934 1.67934541299439,-0.44540778205375 1.67315028355223,-0.1984921849311 1.4126854568819731,-0.29346867195795',
]


def render_cube_group(state: List[str], ox: float = 0.0, oy: float = 0.0, 
                       scale: float = 1.0) -> str:
    """Render cube state as SVG <g> elements at given offset and scale.
    
    The viewBox is -2.0 to 2.4 in X, -1.4 to 1.6 in Y (size 4.4 x 3.0).
    Returns the string of <polygon> elements inside a <g> tag.
    """
    state = list(state)
    color_map = {
        'w': '#FFFFFF', 'y': '#FFD700', 'r': '#FF3333',
        'o': '#FF9500', 'b': '#0066FF', 'g': '#00AA44',
        'l': '#aaaaaa', 'd': '#777777',
    }
    transform = f"transform='translate({ox},{oy}) scale({scale})'"
    lines = [f"  <g {transform} style='stroke:#000000;stroke-width:0.035;stroke-linejoin:round;stroke-linecap:round'>"]
    
    sticker_order = [
        (0, None), (1, None), (2, None),
        (3, (R, 0)), (4, (R, 1)), (5, (R, 2)), 
        (6, (R, 3)), (7, (R, 4)), (8, (R, 5)), 
        (9, (R, 6)), (10, (R, 7)), (11, (R, 8)),
        (12, (U, 0)), (13, (U, 1)), (14, (U, 2)), 
        (15, (U, 3)), (16, (U, 4)), (17, (U, 5)), 
        (18, (U, 6)), (19, (U, 7)), (20, (U, 8)),
        (21, (F, 0)), (22, (F, 1)), (23, (F, 2)), 
        (24, (F, 3)), (25, (F, 4)), (26, (F, 5)), 
        (27, (F, 6)), (28, (F, 7)), (29, (F, 8)),
        # L face exploded (shifted from R geometry - columns mirrored)
        (30, (L, 2)), (31, (L, 1)), (32, (L, 0)), 
        (33, (L, 5)), (34, (L, 4)), (35, (L, 3)), 
        (36, (L, 8)), (37, (L, 7)), (38, (L, 6)),
        # D face rows swapped (shifted from U geometry - rows inverted)
        (39, (D, 6)), (40, (D, 7)), (41, (D, 8)), 
        (42, (D, 3)), (43, (D, 4)), (44, (D, 5)), 
        (45, (D, 0)), (46, (D, 1)), (47, (D, 2)),
        # B face exploded (shifted from F geometry - columns mirrored)
        (48, (B, 2)), (49, (B, 1)), (50, (B, 0)),
        (51, (B, 5)), (52, (B, 4)), (53, (B, 3)),
        (54, (B, 8)), (55, (B, 7)), (56, (B, 6)),
    ]
    
    for poly_idx, face_info in sticker_order:
        points_str = EXPLODED_POLYGONS[poly_idx]
        if face_info is None:
            lines.append(f"    <polygon fill='none' stroke='#000000' stroke-width='0.08' points='{points_str}'/>")
        else:
            face, pos = face_info
            color_char = state[_idx(face, pos)]
            color = color_map.get(color_char, '#CCCCCC')
            lines.append(f"    <polygon fill='{color}' stroke='#000000' points='{points_str}'/>")
    
    lines.append("  </g>")
    return '\n'.join(lines)


def render_svg_exploded(state: List[str], size: int = 600) -> str:
    """Render cube state as SVG with exploded view (main + reference faces)."""
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='-2.0 -1.4 4.4 3.0'>",
        f"  <rect fill='#FFFFFF' x='-2.0' y='-1.4' width='4.4' height='3.0'/>",
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
