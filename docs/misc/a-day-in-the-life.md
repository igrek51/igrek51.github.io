# How to Calculate the Day of the Week

[![](../assets/misc/a-day-in-the-life.png)](../assets/misc/a-day-in-the-life.png)

Given any date, you can determine the day of the week in your head — no calendar needed.
This is a mental arithmetic trick based on **modular arithmetic**.
Sometimes it comes in handy to avoid constantly checking your phone.

## The math behind it
Mathematically, you just need to realize that the set of weekdays forms a **ring of residue classes modulo 7**.
Days of the week repeat in a cycle of 7.
This is exactly what **modulo 7** captures - you only care about the remainder after dividing by 7.
Each day is just a number `0–6`, and arithmetic wraps around.
For simplicity, let's assume the intuitive mapping (In some languages Thursday and Friday are expressed as 4th and 5th day):  
* `1`=Monday,
* `2`=Tuesday,
* `3`=Wednesday,
* `4`=Thursday,
* `5`=Friday,
* `6`=Saturday,
* `0`=Sunday.

Each component of a date — year, century, month, day — contributes an **offset** to the total.
Sum them all up, take the remainder mod 7, and you get the weekday.

## The formula

```
(Y + Y//4 + B + M + D) % 7 = day of the week
```

Where:

- **`Y`** — last 2 digits of the year (e.g. `25` for 2025)
- **`Y//4`** — integer division of Y by 4 (round down), accounts for leap years
- **`B`** — century / base year offset (see table below, 0 for years 2000-2099)
- **`M`** — month code (see table below), including leap day
- **`D`** — day of the month

## Why this works

**Year offset `Y + Y//4`:**
Each year shifts the calendar by 1 day (365 = 52×7 + 1).
Every 4 years there's a leap year adding one extra day, so each year contributes approximately 1.25 days.
`Y//4` accounts for the accumulated leap days up to year `Y`.

**Why we subtract the leap day instead of adding:**
The `Y//4` term assumes every year divisible by 4 is a leap year, so it over-counts by 1
for January and February of an actual leap year (the extra day hasn't occurred yet).
To correct this, the month codes for January and February are pre-decremented by 1 in leap years (6→5, 2→1),
absorbing the over-count for exactly those two months — instead of adjusting all 10 others.

**Century offset `B`:**
The Gregorian calendar has a century correction (century years are leap years only if divisible by 400).
Each century shifts the base by a fixed amount.
Anchoring at year **2000** gives `B=0` — the simplest possible base, so for 21st-century dates you can ignore `B` entirely.

| Century | B |
|---------|---|
| 1900s   | 1 |
| 2000s   | 0 |
| 2100s   | 5 |

Other useful base years with `B=0`: **1944**, **1972**, **2024** — handy if your date is far from 2000.

## Month codes

| Month | Code |
|-------|------|
| Jan   | 6 (5 in leap year) |
| Feb   | 2 (1 in leap year) |
| Mar   | 2 |
| Apr   | 5 |
| May   | 0 |
| Jun   | 3 |
| Jul   | 5 |
| Aug   | 1 |
| Sep   | 4 |
| Oct   | 6 |
| Nov   | 2 |
| Dec   | 4 |

The sequence is: **6 2 2 5 0 3 5 1 4 6 2 4**

### Mnemonic: "genuinely smiled arch-winner"

To memorize this sequence, use the phrase **"genuinely smiled arch-winner"** in the
[Mnemonic Major System](mnemonic-major-system.md):

```
genuinely smiled  arch-winner
6 2 2  5  03 5 1   46    2  4
```

See the [Mnemonic Major System](mnemonic-major-system.md) article for how the encoding works.

## Examples

**2025-12-31:**
```
Y=25, Y//4=6, B=0, M=4 (Dec), D=31
(25 + 6 + 0 + 4 + 31) % 7 = 66 % 7 = 3 → Wednesday
```

**2024-01-06:**
```
Y=24, Y//4=6, B=0, M=5 (Jan in leap year 2024), D=6
(24 + 6 + 0 + 5 + 6) % 7 = 41 % 7 = 6 → Saturday
```

**1993-06-10:**
```
Y=93, Y//4=23, B=1, M=3 (Jun), D=10
(93 + 23 + 1 + 3 + 10) % 7 = 130 % 7 = 4 → Thursday
```

## Tips for mental calculation

**Modulo division**:
Modulo "division" is actually about subtracting.
To find the remainder, keep subtracting multiples of 7 until you get a number from O to 6.

**Reduce early:** apply mod 7 to each term as you go — no need to sum large numbers.
For example, `93 % 7 = 2`, `23 % 7 = 2`, then `(2+2+1+3+3) % 7 = 4`.

**Memorize the current year's offset:** if you know that 2026 contributes `(26 + 6) % 7 = 4`,
then for any date in 2025 you only need:

```
(4 + M + D) % 7
```

with just the month code and day — three numbers instead of five.

Quick lookup for the total year offset:  
* 2025 → 3
* 2026 → 4
* 2027 → 5
* 2028 → 0 (leap year)

**Use a nearby base year** if the date is far from 2000:
pick a known year with `B=0` (e.g. 1972), set `Y = year − base`, and use `B=0`.

Remember that the calendar cycle repeats every 28 years (`lcm(7, 4)`).
