#!/usr/bin/env python3
"""
Generate 2-bit epdfont files for Flash embedding.

Covers:
  - Basic Latin, Latin-1, Latin Extended-A, Cyrillic, Punctuation, Arrows, Math
  - Hangul Syllables: Adobe KR-0 Supplement 0 (2,780 from kr0_hangul.txt)
  - Hangul Compatibility Jamo (consonants only: ㄱ-ㅎ, ㄲㄸㅃㅆㅉ = 19 chars)
  - CJK Symbols and Punctuation
  - Hiragana + Katakana
  - CJK Unified Ideographs: 한문교육용 기초한자 (~1,800 from edu_hanja_1800.txt)

Usage:
    python generate_cjk_font.py <font_file> [size ...]

    <font_file>  Path to the OTF/TTF source font file.
    [size ...]   Optional list of point sizes to generate (default: 10 12 14).

Output:
    ../builtinFonts/{stem}_{size}.epdfont
    where {stem} is the font filename without extension.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ttf_to_epdfont import convert_ttf_to_epdfont  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILTIN_DIR = os.path.join(SCRIPT_DIR, "..", "builtinFonts")

DEFAULT_SIZES = [10, 12, 14]


def load_codepoints(filename):
    """Load codepoints from a file (one 0xXXXX or U+XXXX per line) and return sorted list."""
    path = os.path.join(SCRIPT_DIR, filename)
    codepoints = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("0x") or line.startswith("0X"):
                codepoints.append(int(line, 16))
            elif line.startswith("U+"):
                codepoints.append(int(line[2:], 16))
    return sorted(codepoints)


def codepoints_to_intervals(codepoints):
    """Convert sorted codepoint list to "0xSTART,0xEND" interval strings."""
    if not codepoints:
        return []
    intervals = []
    start = codepoints[0]
    end = codepoints[0]
    for cp in codepoints[1:]:
        if cp == end + 1:
            end = cp
        else:
            intervals.append(f"0x{start:04X},0x{end:04X}")
            start = cp
            end = cp
    intervals.append(f"0x{start:04X},0x{end:04X}")
    return intervals


# Load codepoint files
KR0_HANGUL = load_codepoints("kr0_hangul.txt")
EDU_HANJA = load_codepoints("edu_hanja_1800.txt")

# Additional Unicode intervals beyond the converter's defaults.
INTERVALS = [
    "0x3000,0x303F",   # CJK Symbols and Punctuation
    "0x3040,0x309F",   # Hiragana
    "0x30A0,0x30FF",   # Katakana
    "0x31F0,0x31FF",   # Katakana Phonetic Extensions
    "0x3131,0x314E",   # Hangul Compatibility Jamo (consonants area)
] + codepoints_to_intervals(KR0_HANGUL) + codepoints_to_intervals(EDU_HANJA)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {os.path.basename(__file__)} <font_file> [size ...]", file=sys.stderr)
        sys.exit(1)

    font_file = sys.argv[1]
    if not os.path.isabs(font_file):
        font_file = os.path.abspath(font_file)

    if not os.path.exists(font_file):
        print(f"ERROR: Font file not found: {font_file}", file=sys.stderr)
        sys.exit(1)

    stem = os.path.splitext(os.path.basename(font_file))[0]

    sizes = DEFAULT_SIZES
    if len(sys.argv) > 2:
        sizes = [int(s) for s in sys.argv[2:]]

    total_bytes = 0
    for size in sizes:
        output = os.path.join(BUILTIN_DIR, f"{stem}_{size}.epdfont")
        print(f"Font   : {os.path.basename(font_file)}")
        print(f"Size   : {size}pt")
        print(f"Mode   : 2-bit greyscale")
        print(f"Output : {output}")
        print()

        t0 = time.time()
        convert_ttf_to_epdfont(
            font_files=[font_file],
            font_name=stem,
            size=size,
            output_path=output,
            additional_intervals=INTERVALS,
            is_2bit=True,
        )
        elapsed = time.time() - t0

        if os.path.exists(output):
            fsize = os.path.getsize(output)
            total_bytes += fsize
            print(f"Done in {elapsed:.1f}s — {fsize:,} bytes ({fsize/1024/1024:.2f} MB)\n")
        else:
            print(f"ERROR: Output file was not created!", file=sys.stderr)
            sys.exit(1)

    if len(sizes) > 1:
        print(f"Total: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
