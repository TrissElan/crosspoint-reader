#!/usr/bin/env python3
"""
Generate Pretendard JP 12pt 2-bit epdfont for Flash embedding.

Covers:
  - Basic Latin, Latin-1, Latin Extended-A, Cyrillic, Punctuation, Arrows, Math
  - Hangul Syllables (full 11,172)
  - Hangul Compatibility Jamo (consonants only: ㄱ-ㅎ, ㄲㄸㅃㅆㅉ = 19 chars)
  - CJK Symbols and Punctuation
  - Hiragana + Katakana
  - Halfwidth and Fullwidth Forms
  - CJK Unified Ideographs (whatever the font contains — KS+JIS subset ~7,138)

Usage:
    python generate_pretendard_font.py

Output:
    ../builtinFonts/pretendard_12.epdfont
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ttf_to_epdfont import convert_ttf_to_epdfont  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(
    SCRIPT_DIR, "..", "builtinFonts", "source", "PretendardJP-Regular.otf"
)
OUTPUT_FILE = os.path.join(
    SCRIPT_DIR, "..", "builtinFonts", "pretendard_12.epdfont"
)

SIZE = 12

# Additional Unicode intervals beyond the converter's defaults.
# The converter already includes Basic Latin / Latin-1 / Latin Extended-A /
# Cyrillic / Punctuation / Arrows / Math / Currency by default.
INTERVALS = [
    "0x3000,0x303F",   # CJK Symbols and Punctuation
    "0x3040,0x309F",   # Hiragana
    "0x30A0,0x30FF",   # Katakana
    "0x31F0,0x31FF",   # Katakana Phonetic Extensions
    "0xFF00,0xFFEF",   # Halfwidth and Fullwidth Forms
    "0xAC00,0xD7A3",   # Hangul Syllables (full 11,172)
    # Hangul consonants only (ㄱ-ㅎ basic 14 + ㄲㄸㅃㅆㅉ double 5 = 19)
    # ㄱ=0x3131 ㄲ=0x3132 ㄴ=0x3134 ㄷ=0x3137 ㄸ=0x3138 ㄹ=0x3139
    # ㅁ=0x3141 ㅂ=0x3142 ㅃ=0x3143 ㅅ=0x3145 ㅆ=0x3146 ㅇ=0x3147
    # ㅈ=0x3148 ㅉ=0x3149 ㅊ=0x314A ㅋ=0x314B ㅌ=0x314C ㅍ=0x314D ㅎ=0x314E
    # Range 0x3131-0x314E covers all 19 consonants + some vowels mixed in,
    # but the tool auto-skips missing glyphs, so we include the whole block.
    # Actually, the font has all 53 jamo — specify consonants range only.
    "0x3131,0x314E",   # Hangul Compatibility Jamo (consonants area, 30 codepoints)
    "0x4E00,0x9FFF",   # CJK Unified Ideographs (font has ~7,138)
]


def main():
    if not os.path.exists(FONT_FILE):
        print(f"ERROR: Font file not found: {FONT_FILE}", file=sys.stderr)
        sys.exit(1)

    print(f"Font   : {os.path.basename(FONT_FILE)}")
    print(f"Size   : {SIZE}pt")
    print(f"Mode   : 2-bit greyscale")
    print(f"Output : {OUTPUT_FILE}")
    print()

    t0 = time.time()
    convert_ttf_to_epdfont(
        font_files=[FONT_FILE],
        font_name="Pretendard",
        size=SIZE,
        output_path=OUTPUT_FILE,
        additional_intervals=INTERVALS,
        is_2bit=True,
    )
    elapsed = time.time() - t0

    if os.path.exists(OUTPUT_FILE):
        fsize = os.path.getsize(OUTPUT_FILE)
        print(f"\nDone in {elapsed:.1f}s — {fsize:,} bytes ({fsize/1024/1024:.2f} MB)")
    else:
        print("\nERROR: Output file was not created!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
