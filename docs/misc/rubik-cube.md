# Rubik's Cube Cheatsheet
## Move Notation

![](../assets/misc/rubiks-cube-notation.webp)

An apostrophe `'` (pronounced as prime) means to turn the face in the opposite direction (counterclockwise),
e.g. `L'`.

The number `2` means to turn that face twice, e.g. `U2`.

## 3x3x3 Cube Algorithm (Simple)
### 1. White Cross

### 2. White Corners
At first, turn the cube upside-down

### 3. Middle Layer
Move the top layer edge to the right:
```
U R U' R' U' F' U F
```

### 4. Orient Yellow Cross

#### Minus
```
FRU R'U'F
```
(mnemonic: "through roof")

#### L shape
Run "Minus" algo backwards:
```
FUR U'R'F
```
(mnemonic: "furry Urf")

#### Dot
Use both.

### 5. Permute Yellow Edges
R goes alternately. Run until white corner comes back.
```
R U2 R' U' R U' R'
U'
```

### 6. Permute Last Layer
```
L' U R U' L U R' U'
```

### 7. Orient Last Layer
Repeat algo from step "5. Permute Yellow Edges"
with mirrored and regular algorithm:
```
L' U2 L U L' U L
R U2 R' U' R U' R'
```

## 4x4x4 Cube
### Edge Parity
```
# join left bottom with right top, breaks top edge
(dD) R U' R' (dD)'
# interlace left edge with right edge
(dD) R F' U R' F (dD)'
```

### OLL Parity
having bad edge at top, behind:
```
(rR) B2
(rR) U2 (rR) U2
(rR)' U2 (lL) U2
(rR)' U2 (rR) U2
(rR)' U2 (rR)' U2
```

### PLL Parity
Having bad edge top, front:
```
r2 U2 r2 (uU)2 r2 u2
```
