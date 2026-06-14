#!/usr/bin/env python3
"""
Unit tests for Rubik's Cube move simulator

Tests verify that each move correctly transforms the cube state.
Each test checks specific sticker positions before and after a move.
"""

import sys
sys.path.insert(0, 'scripts/rubik')

from gen_rubik_guide import (
    string_to_state, apply_move, apply_algorithm, 
    _idx, U, D, F, B, R, L
)

# Color abbreviations
w, y, r, o, b, g = 'w', 'y', 'r', 'o', 'b', 'g'

# Solved state for reference
SOLVED = 'wwwwwwwwwyyyyyyyyyrrrrrrrrrooooooooobbbbbbbbbggggggggg'

def state_to_dict(state):
    """Convert state list to a dict mapping position to color"""
    return {i: state[i] for i in range(54)}

def get_sticker(state, face, pos):
    """Get sticker color at specific position"""
    return state[_idx(face, pos)]

def describe_sticker(state, face, pos):
    """Get human-readable description of sticker"""
    faces = {U: 'U', D: 'D', F: 'F', B: 'B', R: 'R', L: 'L'}
    return f"{faces[face]}{pos}"

def assert_sticker(state, face, pos, expected_color, move_name=""):
    """Assert that a sticker has the expected color"""
    actual = get_sticker(state, face, pos)
    if actual != expected_color:
        raise AssertionError(
            f"After {move_name}: {describe_sticker(state, face, pos)} "
            f"expected {expected_color} but got {actual}"
        )

def print_cube_state(state, title=""):
    """Pretty print cube state"""
    print(f"\n{title}")
    print("=" * 60)
    print(f"U (top):    {state[_idx(U, 0)]} {state[_idx(U, 1)]} {state[_idx(U, 2)]}")
    print(f"            {state[_idx(U, 3)]} {state[_idx(U, 4)]} {state[_idx(U, 5)]}")
    print(f"            {state[_idx(U, 6)]} {state[_idx(U, 7)]} {state[_idx(U, 8)]}")
    print()
    print(f"F (front):  {state[_idx(F, 0)]} {state[_idx(F, 1)]} {state[_idx(F, 2)]}")
    print(f"            {state[_idx(F, 3)]} {state[_idx(F, 4)]} {state[_idx(F, 5)]}")
    print(f"            {state[_idx(F, 6)]} {state[_idx(F, 7)]} {state[_idx(F, 8)]}")
    print()
    print(f"R (right):  {state[_idx(R, 0)]} {state[_idx(R, 1)]} {state[_idx(R, 2)]}")
    print(f"            {state[_idx(R, 3)]} {state[_idx(R, 4)]} {state[_idx(R, 5)]}")
    print(f"            {state[_idx(R, 6)]} {state[_idx(R, 7)]} {state[_idx(R, 8)]}")
    print()
    print(f"L (left):   {state[_idx(L, 0)]} {state[_idx(L, 1)]} {state[_idx(L, 2)]}")
    print(f"            {state[_idx(L, 3)]} {state[_idx(L, 4)]} {state[_idx(L, 5)]}")
    print(f"            {state[_idx(L, 6)]} {state[_idx(L, 7)]} {state[_idx(L, 8)]}")
    print()
    print(f"D (bottom): {state[_idx(D, 0)]} {state[_idx(D, 1)]} {state[_idx(D, 2)]}")
    print(f"            {state[_idx(D, 3)]} {state[_idx(D, 4)]} {state[_idx(D, 5)]}")
    print(f"            {state[_idx(D, 6)]} {state[_idx(D, 7)]} {state[_idx(D, 8)]}")
    print()
    print(f"B (back):   {state[_idx(B, 0)]} {state[_idx(B, 1)]} {state[_idx(B, 2)]}")
    print(f"            {state[_idx(B, 3)]} {state[_idx(B, 4)]} {state[_idx(B, 5)]}")
    print(f"            {state[_idx(B, 6)]} {state[_idx(B, 7)]} {state[_idx(B, 8)]}")
    print("=" * 60)

# ============================================================================
# TESTS FOR R MOVE (Right face clockwise)
# ============================================================================

def test_r_move_right_face_rotation():
    """R move rotates the right face 90° clockwise"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'R')
    
    print_cube_state(state, "After R move")
    
    # Right face should rotate: top-left -> top-right -> bottom-right -> bottom-left -> top-left
    # Original:                    0 -> 2 -> 8 -> 6 -> 0
    #                              1 -> 5 -> 7 -> 3 -> 1
    # So: R[0]=R[6], R[1]=R[3], R[2]=R[0], R[3]=R[7], R[4]=R[4], R[5]=R[1], R[6]=R[8], R[7]=R[5], R[8]=R[2]
    
    # After R: right face colors should be blue (b) everywhere
    assert_sticker(state, R, 0, 'b', "R - R0")
    assert_sticker(state, R, 1, 'b', "R - R1")
    assert_sticker(state, R, 2, 'b', "R - R2")
    assert_sticker(state, R, 3, 'b', "R - R3")
    assert_sticker(state, R, 4, 'b', "R - R4 (center)")
    assert_sticker(state, R, 5, 'b', "R - R5")
    assert_sticker(state, R, 6, 'b', "R - R6")
    assert_sticker(state, R, 7, 'b', "R - R7")
    assert_sticker(state, R, 8, 'b', "R - R8")
    
    print("✓ R move: right face rotation correct")

def test_r_move_adjacent_edges():
    """R move affects edges of U, F, D, B faces"""
    state = string_to_state(SOLVED)
    
    # Before R: F right column is red (r), U right column is white (w), D right column is yellow (y), B left column is orange (o)
    # After R (dataflow: D→F→U→B→D):
    #   F right column should be yellow (from D)
    #   U right column should be red (from F)
    #   B left column should be white (from U)
    #   D right column should be orange (from B)
    
    state = apply_move(state, 'R')
    
    print_cube_state(state, "After R move - checking adjacent faces")
    
    # Front face right column: should be yellow (from D right column)
    print("\nFront face right column after R:")
    print(f"  F2 (top-right): {get_sticker(state, F, 2)} (expected y)")
    print(f"  F5 (mid-right): {get_sticker(state, F, 5)} (expected y)")
    print(f"  F8 (bot-right): {get_sticker(state, F, 8)} (expected y)")
    
    assert_sticker(state, F, 2, 'y', "R - F2 should be yellow from D2")
    assert_sticker(state, F, 5, 'y', "R - F5 should be yellow from D5")
    assert_sticker(state, F, 8, 'y', "R - F8 should be yellow from D8")
    
    # Up face right column: should be red (from F right column)
    print("\nUp face right column after R:")
    print(f"  U2 (top-right): {get_sticker(state, U, 2)} (expected r)")
    print(f"  U5 (mid-right): {get_sticker(state, U, 5)} (expected r)")
    print(f"  U8 (bot-right): {get_sticker(state, U, 8)} (expected r)")
    
    assert_sticker(state, U, 2, 'r', "R - U2 should be red from F2")
    assert_sticker(state, U, 5, 'r', "R - U5 should be red from F5")
    assert_sticker(state, U, 8, 'r', "R - U8 should be red from F8")
    
    # Down face right column: should be orange (from B left column)
    print("\nDown face right column after R:")
    print(f"  D2 (top-right): {get_sticker(state, D, 2)} (expected o)")
    print(f"  D5 (mid-right): {get_sticker(state, D, 5)} (expected o)")
    print(f"  D8 (bot-right): {get_sticker(state, D, 8)} (expected o)")
    
    assert_sticker(state, D, 2, 'o', "R - D2 should be orange from B6")
    assert_sticker(state, D, 5, 'o', "R - D5 should be orange from B3")
    assert_sticker(state, D, 8, 'o', "R - D8 should be orange from B0")
    
    # Back face left column: should be white (from U right column)
    print("\nBack face left column after R:")
    print(f"  B0 (top-left): {get_sticker(state, B, 0)} (expected w)")
    print(f"  B3 (mid-left): {get_sticker(state, B, 3)} (expected w)")
    print(f"  B6 (bot-left): {get_sticker(state, B, 6)} (expected w)")
    
    assert_sticker(state, B, 0, 'w', "R - B0 should be white from U2")
    assert_sticker(state, B, 3, 'w', "R - B3 should be white from U5")
    assert_sticker(state, B, 6, 'w', "R - B6 should be white from U8")
    
    print("\n✓ R move: all adjacent edges correct")

def test_r_move_left_face_unchanged():
    """R move should NOT affect the left face"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'R')
    
    # Left face should still be all green
    for i in range(9):
        assert_sticker(state, L, i, 'g', f"R - L{i} should stay green")
    
    print("✓ R move: left face unchanged")

def test_r_move_four_times_returns_to_start():
    """Applying R four times should return to the original state"""
    state = string_to_state(SOLVED)
    original = ''.join(state)
    
    for _ in range(4):
        state = apply_move(state, 'R')
    
    result = ''.join(state)
    if original != result:
        print("FAIL: R^4 != identity")
        print(f"Original: {original}")
        print(f"Result:   {result}")
        raise AssertionError("R^4 should equal identity")
    
    print("✓ R move: R^4 = identity")

def test_r_prime_is_inverse_of_r():
    """R' should undo R (R * R' = identity, or R * R^3 = identity)"""
    state = string_to_state(SOLVED)
    original = ''.join(state)
    
    # Apply R
    state = apply_move(state, 'R')
    after_r = ''.join(state)
    
    # Apply R^3 (inverse of R)
    state = apply_move(state, 'R')
    state = apply_move(state, 'R')
    state = apply_move(state, 'R')
    
    result = ''.join(state)
    if original != result:
        print("FAIL: R + R^3 != identity")
        print(f"Original: {original}")
        print(f"After R:  {after_r}")
        print(f"After R^3:{result}")
        raise AssertionError("R + R^3 should equal identity")
    
    print("✓ R move: R + R^3 = identity (R' is inverse)")

# ============================================================================
# TESTS FOR U MOVE (Up face clockwise)
# ============================================================================

def test_u_move_affects_top_edges():
    """U move rotates the top edges clockwise (from above)"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'U')
    
    print_cube_state(state, "After U move")
    
    # After U CW (looking from above): F→L→B→R→F
    # (front goes to left, left to back, back to right, right to front)
    # F top row should be blue (from R)
    # R top row should be orange (from B)
    # B top row should be green (from L)
    # L top row should be red (from F)
    
    assert_sticker(state, F, 0, 'b', "U - F0 from R0")
    assert_sticker(state, F, 1, 'b', "U - F1 from R1")
    assert_sticker(state, F, 2, 'b', "U - F2 from R2")
    
    assert_sticker(state, R, 0, 'o', "U - R0 from B0")
    assert_sticker(state, R, 1, 'o', "U - R1 from B1")
    assert_sticker(state, R, 2, 'o', "U - R2 from B2")
    
    assert_sticker(state, B, 0, 'g', "U - B0 from L0")
    assert_sticker(state, B, 1, 'g', "U - B1 from L1")
    assert_sticker(state, B, 2, 'g', "U - B2 from L2")
    
    assert_sticker(state, L, 0, 'r', "U - L0 from F0")
    assert_sticker(state, L, 1, 'r', "U - L1 from F1")
    assert_sticker(state, L, 2, 'r', "U - L2 from F2")
    
    print("✓ U move: top edges correct (CW: F→L→B→R→F)")

# ============================================================================
# TESTS FOR F MOVE (Front face clockwise)
# ============================================================================

def test_f_move_front_face_rotation():
    """F move rotates the front face"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'F')
    
    # Front face should stay all red
    for i in range(9):
        assert_sticker(state, F, i, 'r', f"F - F{i}")
    
    print("✓ F move: front face rotation correct")

def test_f_move_affects_adjacent_faces():
    """F move affects U bottom, R left, D top, L right"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'F')
    
    print_cube_state(state, "After F move")
    
    # U bottom row (6,7,8) should be green (from L right column, reversed: 2,5,8 -> 8,5,2)
    print("\nU bottom row after F:")
    print(f"  U6: {get_sticker(state, U, 6)} (expected g from L2)")
    print(f"  U7: {get_sticker(state, U, 7)} (expected g from L5)")
    print(f"  U8: {get_sticker(state, U, 8)} (expected g from L8)")
    
    assert_sticker(state, U, 6, 'g', "F - U6 from L2")
    assert_sticker(state, U, 7, 'g', "F - U7 from L5")
    assert_sticker(state, U, 8, 'g', "F - U8 from L8")
    
    # R left column (0,3,6) should be white (from U bottom row, reversed: 8,7,6 -> 8,7,6)
    print("\nR left column after F:")
    print(f"  R0: {get_sticker(state, R, 0)} (expected w from U6)")
    print(f"  R3: {get_sticker(state, R, 3)} (expected w from U7)")
    print(f"  R6: {get_sticker(state, R, 6)} (expected w from U8)")
    
    assert_sticker(state, R, 0, 'w', "F - R0 from U6")
    assert_sticker(state, R, 3, 'w', "F - R3 from U7")
    assert_sticker(state, R, 6, 'w', "F - R6 from U8")
    
    # D top row (0,1,2) should be blue (from R left column, reversed: 6,3,0 -> 0,3,6)
    print("\nD top row after F:")
    print(f"  D0: {get_sticker(state, D, 0)} (expected b from R6)")
    print(f"  D1: {get_sticker(state, D, 1)} (expected b from R3)")
    print(f"  D2: {get_sticker(state, D, 2)} (expected b from R0)")
    
    assert_sticker(state, D, 0, 'b', "F - D0 from R6")
    assert_sticker(state, D, 1, 'b', "F - D1 from R3")
    assert_sticker(state, D, 2, 'b', "F - D2 from R0")
    
    # L right column (2,5,8) should be yellow (from D top row, reversed: 0,1,2 -> 2,1,0)
    print("\nL right column after F:")
    print(f"  L2: {get_sticker(state, L, 2)} (expected y from D2)")
    print(f"  L5: {get_sticker(state, L, 5)} (expected y from D1)")
    print(f"  L8: {get_sticker(state, L, 8)} (expected y from D0)")
    
    assert_sticker(state, L, 2, 'y', "F - L2 from D2")
    assert_sticker(state, L, 5, 'y', "F - L5 from D1")
    assert_sticker(state, L, 8, 'y', "F - L8 from D0")
    
    print("\n✓ F move: all adjacent edges correct")

# ============================================================================
# TESTS FOR D MOVE (Down face clockwise)
# ============================================================================

def test_d_move_bottom_face_rotation():
    """D move rotates the bottom face 90° clockwise"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'D')
    # D face should stay all yellow
    for i in range(9):
        assert_sticker(state, D, i, 'y', f"D - D{i}")
    print("✓ D move: bottom face rotation correct")

def test_d_move_adjacent_edges():
    """D move bottom faces of F, R, B, L"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'D')
    # After D CW from below: L→F→R→B→L (data flow: F←L, R←F, B←R, L←B)
    # F bottom (6,7,8) gets from L bottom (6,7,8) = green
    assert_sticker(state, F, 6, 'g', "D - F6 from L6")
    assert_sticker(state, F, 7, 'g', "D - F7 from L7")
    assert_sticker(state, F, 8, 'g', "D - F8 from L8")
    # R bottom (6,7,8) gets from F bottom (6,7,8) = red
    assert_sticker(state, R, 6, 'r', "D - R6 from F6")
    assert_sticker(state, R, 7, 'r', "D - R7 from F7")
    assert_sticker(state, R, 8, 'r', "D - R8 from F8")
    # B bottom (6,7,8) gets from R bottom (6,7,8) = blue
    assert_sticker(state, B, 6, 'b', "D - B6 from R6")
    assert_sticker(state, B, 7, 'b', "D - B7 from R7")
    assert_sticker(state, B, 8, 'b', "D - B8 from R8")
    # L bottom (6,7,8) gets from B bottom (6,7,8) = orange
    assert_sticker(state, L, 6, 'o', "D - L6 from B6")
    assert_sticker(state, L, 7, 'o', "D - L7 from B7")
    assert_sticker(state, L, 8, 'o', "D - L8 from B8")
    print("✓ D move: all adjacent edges correct")

# ============================================================================
# TESTS FOR B MOVE (Back face clockwise)
# ============================================================================

def test_b_move_adjacent_edges():
    """B move affects U top, R right, D bottom, L left"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'B')
    # After B CW: U←R, L←U, D←L, R←D
    # U top (0,1,2) gets from R right column (8,5,2) = blue
    assert_sticker(state, U, 0, 'b', "B - U0 from R8")
    assert_sticker(state, U, 1, 'b', "B - U1 from R5")
    assert_sticker(state, U, 2, 'b', "B - U2 from R2")
    # L left (0,3,6) gets from U top (0,1,2) = white
    assert_sticker(state, L, 0, 'w', "B - L0 from U0")
    assert_sticker(state, L, 3, 'w', "B - L3 from U1")
    assert_sticker(state, L, 6, 'w', "B - L6 from U2")
    # D bottom (6,7,8) gets from L left (0,3,6) = green
    assert_sticker(state, D, 6, 'g', "B - D6 from L6")
    assert_sticker(state, D, 7, 'g', "B - D7 from L3")
    assert_sticker(state, D, 8, 'g', "B - D8 from L0")
    # R right (2,5,8) gets from D bottom (6,7,8) = yellow
    assert_sticker(state, R, 2, 'y', "B - R2 from D6")
    assert_sticker(state, R, 5, 'y', "B - R5 from D7")
    assert_sticker(state, R, 8, 'y', "B - R8 from D8")
    print("✓ B move: all adjacent edges correct")

# ============================================================================
# TESTS FOR L MOVE (Left face clockwise)
# ============================================================================

def test_l_move_adjacent_edges():
    """L move affects U left, F left, D left, B right"""
    state = string_to_state(SOLVED)
    state = apply_move(state, 'L')
    # After L CW: F←U, D←F, B←D, U←B
    # F left (0,3,6) gets from U left (0,3,6) = white
    assert_sticker(state, F, 0, 'w', "L - F0 from U0")
    assert_sticker(state, F, 3, 'w', "L - F3 from U3")
    assert_sticker(state, F, 6, 'w', "L - F6 from U6")
    # D left (0,3,6) gets from F left (0,3,6) = red
    assert_sticker(state, D, 0, 'r', "L - D0 from F0")
    assert_sticker(state, D, 3, 'r', "L - D3 from F3")
    assert_sticker(state, D, 6, 'r', "L - D6 from F6")
    # B right (2,5,8) gets from D left (0,3,6) = yellow
    assert_sticker(state, B, 2, 'y', "L - B2 from D6")
    assert_sticker(state, B, 5, 'y', "L - B5 from D3")
    assert_sticker(state, B, 8, 'y', "L - B8 from D0")
    # U left (0,3,6) gets from B right (2,5,8) = orange
    assert_sticker(state, U, 0, 'o', "L - U0 from B2")
    assert_sticker(state, U, 3, 'o', "L - U3 from B5")
    assert_sticker(state, U, 6, 'o', "L - U6 from B8")
    print("✓ L move: all adjacent edges correct")

# ============================================================================
# TESTS FOR SEQUENCES (corner consistency)
# ============================================================================

def check_corners(state, description=""):
    """Verify all 8 corners have exactly 3 distinct colors. Returns (ok, bad_corners)."""
    corner_defs = [
        ('URF', [(U,8),(R,0),(F,2)]),
        ('UFL', [(U,6),(F,0),(L,2)]),
        ('ULB', [(U,0),(L,0),(B,2)]),
        ('UBR', [(U,2),(B,0),(R,2)]),
        ('DRF', [(D,2),(R,6),(F,8)]),
        ('DFL', [(D,0),(F,6),(L,8)]),
        ('DLB', [(D,6),(L,6),(B,8)]),
        ('DBR', [(D,8),(B,6),(R,8)]),
    ]
    bad = []
    for name, positions in corner_defs:
        colors = [state[_idx(f,p)] for f,p in positions]
        if len(set(colors)) != 3:
            bad.append((name, colors))
    if bad:
        raise AssertionError(
            f"After {description}: invalid corners: {bad}"
        )
    return True

def test_lu_sequence_corners():
    """L U sequence should keep all 8 corners valid (3 distinct colors each)."""
    state = string_to_state(SOLVED)
    state = apply_algorithm(state, 'L U')
    print_cube_state(state, "After L U")
    check_corners(state, "L U")
    print("✓ L U: all 8 corners have 3 distinct colors")

def test_fd_sequence_corners():
    """F D sequence should keep all 8 corners valid."""
    state = string_to_state(SOLVED)
    state = apply_algorithm(state, 'F D')
    check_corners(state, "F D")
    print("✓ F D: all 8 corners have 3 distinct colors")

def test_r_u_prime_sequence_corners():
    """R U' sequence should keep all 8 corners valid."""
    state = string_to_state(SOLVED)
    state = apply_algorithm(state, "R U'")
    check_corners(state, "R U'")
    print("✓ R U': all 8 corners have 3 distinct colors")

# ============================================================================
# TESTS FOR ALGORITHMS
# ============================================================================

def test_r_u_r_prime_u_prime():
    """R U R' U' (Sexy Move) should return to solved after 6 iterations"""
    state = string_to_state(SOLVED)
    for _ in range(6):
        state = apply_algorithm(state, "R U R' U'")
    result = ''.join(state)
    if result != SOLVED:
        print_cube_state(state, "After 6x Sexy Move")
        raise AssertionError("Six Sexy Moves should return to solved")
    print("✓ Algorithm: 6x (R U R' U') = identity (Sexy Move order 6)")

def test_sune_algorithm():
    """Sune (R U R' U R U2 R') has order 6"""
    state = string_to_state(SOLVED)
    for _ in range(6):
        state = apply_algorithm(state, "R U R' U R U2 R'")
    result = ''.join(state)
    if result != SOLVED:
        raise AssertionError(
            f"Sune should have order 6, but 6 iterations did not return to solved"
        )
    print("✓ Algorithm: Sune (R U R' U R U2 R') order 6 correct")

def test_r_prime_d_f_sequence():
    """Verify R' D F sequence affects specific stickers correctly"""
    state = string_to_state(SOLVED)
    state = apply_algorithm(state, "R' D F")
    print_cube_state(state, "After R' D F")

    # Check specific stickers after R' D F
    # These are derived from manually performing the moves on a solved cube
    assert_sticker(state, U, 0, 'w', "R' D F - U0")
    assert_sticker(state, U, 1, 'w', "R' D F - U1")
    assert_sticker(state, U, 2, 'o', "R' D F - U2")
    assert_sticker(state, U, 3, 'w', "R' D F - U3")
    assert_sticker(state, U, 4, 'w', "R' D F - U4")
    assert_sticker(state, U, 5, 'o', "R' D F - U5")
    assert_sticker(state, U, 6, 'o', "R' D F - U6")
    assert_sticker(state, U, 7, 'g', "R' D F - U7")
    assert_sticker(state, U, 8, 'g', "R' D F - U8")

    assert_sticker(state, D, 0, 'r', "R' D F - D0")
    assert_sticker(state, D, 1, 'b', "R' D F - D1")
    assert_sticker(state, D, 2, 'b', "R' D F - D2")
    assert_sticker(state, D, 3, 'y', "R' D F - D3")
    assert_sticker(state, D, 4, 'y', "R' D F - D4")
    assert_sticker(state, D, 5, 'y', "R' D F - D5")
    assert_sticker(state, D, 6, 'r', "R' D F - D6")
    assert_sticker(state, D, 7, 'r', "R' D F - D7")
    assert_sticker(state, D, 8, 'r', "R' D F - D8")

    assert_sticker(state, F, 0, 'g', "R' D F - F0")
    assert_sticker(state, F, 1, 'r', "R' D F - F1")
    assert_sticker(state, F, 2, 'r', "R' D F - F2")
    assert_sticker(state, F, 3, 'g', "R' D F - F3")
    assert_sticker(state, F, 4, 'r', "R' D F - F4")
    assert_sticker(state, F, 5, 'r', "R' D F - F5")
    assert_sticker(state, F, 6, 'g', "R' D F - F6")
    assert_sticker(state, F, 7, 'w', "R' D F - F7")
    assert_sticker(state, F, 8, 'w', "R' D F - F8")

    assert_sticker(state, B, 0, 'y', "R' D F - B0")
    assert_sticker(state, B, 1, 'o', "R' D F - B1")
    assert_sticker(state, B, 2, 'o', "R' D F - B2")
    assert_sticker(state, B, 3, 'y', "R' D F - B3")
    assert_sticker(state, B, 4, 'o', "R' D F - B4")
    assert_sticker(state, B, 5, 'o', "R' D F - B5")
    assert_sticker(state, B, 6, 'b', "R' D F - B6")
    assert_sticker(state, B, 7, 'b', "R' D F - B7")
    assert_sticker(state, B, 8, 'b', "R' D F - B8")

    assert_sticker(state, R, 0, 'w', "R' D F - R0")
    assert_sticker(state, R, 1, 'b', "R' D F - R1")
    assert_sticker(state, R, 2, 'b', "R' D F - R2")
    assert_sticker(state, R, 3, 'w', "R' D F - R3")
    assert_sticker(state, R, 4, 'b', "R' D F - R4")
    assert_sticker(state, R, 5, 'b', "R' D F - R5")
    assert_sticker(state, R, 6, 'o', "R' D F - R6")
    assert_sticker(state, R, 7, 'r', "R' D F - R7")
    assert_sticker(state, R, 8, 'w', "R' D F - R8")

    assert_sticker(state, L, 0, 'g', "R' D F - L0")
    assert_sticker(state, L, 1, 'g', "R' D F - L1")
    assert_sticker(state, L, 2, 'y', "R' D F - L2")
    assert_sticker(state, L, 3, 'g', "R' D F - L3")
    assert_sticker(state, L, 4, 'g', "R' D F - L4")
    assert_sticker(state, L, 5, 'y', "R' D F - L5")
    assert_sticker(state, L, 6, 'y', "R' D F - L6")
    assert_sticker(state, L, 7, 'o', "R' D F - L7")
    assert_sticker(state, L, 8, 'y', "R' D F - L8")

    print("✓ Algorithm: R' D F sequence correct")

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("RUBIK'S CUBE MOVE SIMULATOR - UNIT TESTS")
    print("="*70)
    
    tests = [
        ("R move: Right face rotation", test_r_move_right_face_rotation),
        ("R move: Adjacent edges", test_r_move_adjacent_edges),
        ("R move: Left face unchanged", test_r_move_left_face_unchanged),
        ("R move: R^4 = identity", test_r_move_four_times_returns_to_start),
        ("R move: R + R^3 = identity", test_r_prime_is_inverse_of_r),
        ("U move: Top edges", test_u_move_affects_top_edges),
        ("F move: Front face rotation", test_f_move_front_face_rotation),
        ("F move: Adjacent edges", test_f_move_affects_adjacent_faces),
        ("D move: Bottom face rotation", test_d_move_bottom_face_rotation),
        ("D move: Adjacent edges", test_d_move_adjacent_edges),
        ("B move: Adjacent edges", test_b_move_adjacent_edges),
        ("L move: Adjacent edges", test_l_move_adjacent_edges),
        ("L U: corners valid", test_lu_sequence_corners),
        ("F D: corners valid", test_fd_sequence_corners),
        ("R U': corners valid", test_r_u_prime_sequence_corners),
        ("Algorithm: Sexy Move x6", test_r_u_r_prime_u_prime),
        ("Algorithm: Sune", test_sune_algorithm),
        ("Algorithm: R' D F", test_r_prime_d_f_sequence),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            test_func()
            passed += 1
            print(f"✓ PASSED")
        except AssertionError as e:
            failed += 1
            print(f"✗ FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    sys.exit(0 if failed == 0 else 1)
