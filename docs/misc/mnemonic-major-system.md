# Mnemonic Major System

The **Mnemonic Major System** helps you to  remember a string of digits (a phone number, a PIN, the first digits of Pi, etc.) by turning numbers into words.
Words are much easier to remember than digits.

The trick: certain consonant letters map to digits 0–9.
Some letters and spaces are completely neutral — they evaluate to nothing,
but they are the glue that lets you build real, meaningful words and sentences around the significant consonants.
Because the mapping is fixed and unambiguous, a word or sentence always translates to exactly the same number.
The mapping is one to many, meaning there's many words translating to the same number.

The goal is to find a word or a sequence of words that:

1. encodes precisely the digits you want to remember, and
2. means something memorable — ideally something you can visualize or that connects to the number itself (eg. connects to a person whose phone number you'd like to remember).

## The mapping
The mapping is a bit different for Polish and English language.
Note that a phonetic pronounciation counts, not the actual letters, particularly in English.

### Polish

| Digit | Sounds | Mnemonic |
|-------|--------|---|
| 0 | `Z` `S` `Ź` `Ś` | "Z" for zero |
| 1 | `T` `D` | "T" has one vertical stroke, like 1 |
| 2 | `N` `Ń` | "N" has 2 vertical strokes |
| 3 | `M` | "M" has 3 vertical strokes |
| 4 | `R` | "czteRy" has R |
| 5 | `L` | "L" - Roman numeral for 50 |
| 6 | `SZ` `CZ` `Ż` `DŻ` `DZ` `DŹ` | "SZeść" and other rustlings |
| 7 | `K` `G` | 7 and K have diagonal stroke |
| 8 | `F` `W` | Fedora logo: f in 8 |
| 9 | `P` `B` | P is flipped 9 |

Note that hard letters and their soft counterparts are always in the same sections.

Neutral (ignored): vowels `A Ą E Ę I O Ó U Y` and `C H CH J Ć Ł`.

### English

| Digit | Sounds |
|-------|--------|
| 0 | S /s/, Z /z/ |
| 1 | T /t/, D /d/ |
| 2 | N /n/ |
| 3 | M /m/ |
| 4 | R /r/ |
| 5 | L /l/ |
| 6 | SH /ʃ/, CH /tʃ/, J /dʒ/ |
| 7 | K /k/, G /g/ |
| 8 | F /f/, V /v/, TH /θ/ |
| 9 | P /p/, B /b/ |

Vowels, W, H, and silent letters are neutral (ignored).

## Examples

Take the phrase **"mój tort ulubiony"** that encodes digits of pi (assosiate with "pie" or round pie chart).
Read only its significant consonants:

```
m ó j   t o r t   u l u b i o n y
3       1   4 1     5   9     2
```

That is **3 141 592** — the first 7 digits of **π**. The letters `ó`, `j`, `o`, `u`, `i`, `o`, `y` and the spaces are all neutral fillers — they contribute nothing to the number, but they turn a bare consonant sequence into a real, vivid phrase that sticks in your memory.

Another one: **"negatywna wada"**:
```
negatywna wada
2 7 1 82  8 1
```
resolves to **2 718 281** - first digits of **e** number.

Short words work great for small numbers:

| Word | Breakdown | Number |
|------|-----------|--------|
| **żaba** | ż=6, b=9 | 69 |
| **muchomor** | m=3, (ch=neutral), m=3, r=4 | 334 |
| **tapir** | t=1, p=9, r=4 | 194 |
| **rain** | r=4, n=2 | 42 |
| **film** | f=8, l=5, m=3 | 853 |

## MemGen — find the word for you

Searching for a matching word by hand can be a tedious process.
**[MemGen](https://igrek51.github.io/memgen/)** is a free browser tool that facilitates it —
type a number, get a list of matching Polish and English words. Choose the ones that resonate with the encoded meaning.

You can add spaces to work on segments separately: `3 141 592` gives results for each chunk independently.

Try it: **<https://igrek51.github.io/memgen/>**  
Source: [github.com/igrek51/memgen](https://github.com/igrek51/memgen)
