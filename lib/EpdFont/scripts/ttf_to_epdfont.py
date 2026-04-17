#!/usr/bin/env python3
"""
Convert TTF/OTF font files directly to .epdfont binary format.

Usage:
    python ttf_to_epdfont.py <font_name> <size> <font_file> [--additional-intervals MIN,MAX] [-o output.epdfont]

Example:
    python ttf_to_epdfont.py hangeuljaemin 14 ./Hangeuljaemin.ttf --additional-intervals 0xAC00,0xD7AF -o hangeuljaemin_14.epdfont
"""

import freetype
import struct
import sys
import math
import argparse
from collections import namedtuple

EPDFONT_MAGIC = 0x46445045  # "EPDF"
EPDFONT_VERSION = 1

GlyphProps = namedtuple("GlyphProps", ["width", "height", "advance_x", "left", "top", "data_length", "data_offset", "code_point"])

def norm_floor(val):
    return int(math.floor(val / (1 << 6)))

def norm_ceil(val):
    return int(math.ceil(val / (1 << 6)))

def norm_round(val):
    """Round a 26.6 fixed-point value to the nearest integer pixel."""
    return int(math.floor(val / (1 << 6) + 0.5))

def load_glyph(font_stack, code_point, load_flags):
    face_index = 0
    while face_index < len(font_stack):
        face = font_stack[face_index]
        glyph_index = face.get_char_index(code_point)
        if glyph_index > 0:
            face.load_glyph(glyph_index, load_flags)
            return face
        face_index += 1
    return None

def quantize_2bit(v):
    """Quantize 8-bit grayscale (0..255) directly to 2-bit (0..3) using evenly
    distributed thresholds (nearest of 0/85/170/255). Avoids the cumulative
    error of the legacy 8 -> 4 -> 2 bit truncation pipeline."""
    if v >= 213:
        return 3
    if v >= 128:
        return 2
    if v >= 43:
        return 1
    return 0

def quantize_1bit(v):
    """Quantize 8-bit grayscale to 1-bit using the standard midpoint."""
    return 1 if v >= 128 else 0

def pack_2bit(bitmap):
    """Pack an 8-bit FreeType grayscale bitmap into 2-bit, MSB first, 4 px/byte.
    Packs across row boundaries to match the renderer's pixelPosition layout."""
    width = bitmap.width
    rows = bitmap.rows
    pitch = bitmap.pitch
    buf = bitmap.buffer
    pixels = []
    px = 0
    total = width * rows
    for y in range(rows):
        row_offset = y * pitch
        for x in range(width):
            v = buf[row_offset + x] if row_offset + x < len(buf) else 0
            px = (px << 2) | quantize_2bit(v)
            if (y * width + x) % 4 == 3:
                pixels.append(px)
                px = 0
    rem = total % 4
    if rem != 0:
        px <<= (4 - rem) * 2
        pixels.append(px)
    return pixels

def pack_1bit(bitmap):
    """Pack an 8-bit FreeType grayscale bitmap into 1-bit, MSB first, 8 px/byte."""
    width = bitmap.width
    rows = bitmap.rows
    pitch = bitmap.pitch
    buf = bitmap.buffer
    pixels = []
    px = 0
    total = width * rows
    for y in range(rows):
        row_offset = y * pitch
        for x in range(width):
            v = buf[row_offset + x] if row_offset + x < len(buf) else 0
            px = (px << 1) | quantize_1bit(v)
            if (y * width + x) % 8 == 7:
                pixels.append(px)
                px = 0
    rem = total % 8
    if rem != 0:
        px <<= (8 - rem)
        pixels.append(px)
    return pixels

def convert_ttf_to_epdfont(font_files, font_name, size, output_path, additional_intervals=None, is_2bit=False, force_autohint=False):
    """Convert TTF font to .epdfont binary format."""

    font_stack = [freetype.Face(f) for f in font_files]

    # Set font size (150 DPI)
    for face in font_stack:
        face.set_char_size(size << 6, size << 6, 150, 150)

    load_flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL
    if force_autohint:
        load_flags |= freetype.FT_LOAD_FORCE_AUTOHINT

    # Default Unicode intervals
    intervals = [
        # Basic Latin
        (0x0000, 0x007F),
        # Latin-1 Supplement
        (0x0080, 0x00FF),
        # Latin Extended-A
        (0x0100, 0x017F),
        # General Punctuation
        (0x2000, 0x206F),
        # Basic Symbols
        (0x2010, 0x203A),
        (0x2040, 0x205F),
        # Currency symbols
        (0x20A0, 0x20CF),
        # Combining Diacritical Marks
        (0x0300, 0x036F),
        # Cyrillic
        (0x0400, 0x04FF),
        # Math Symbols
        (0x2200, 0x22FF),
        # Arrows
        (0x2190, 0x21FF),
    ]

    # Add Korean intervals for Korean fonts
    korean_intervals = [
        # Hangul Syllables (가-힣)
        (0xAC00, 0xD7AF),
        # Hangul Jamo
        (0x1100, 0x11FF),
        # Hangul Compatibility Jamo
        (0x3130, 0x318F),
        # CJK Symbols and Punctuation
        (0x3000, 0x303F),
    ]

    # Add additional intervals if specified
    if additional_intervals:
        for interval in additional_intervals:
            parts = interval.split(',')
            if len(parts) == 2:
                start = int(parts[0], 0)
                end = int(parts[1], 0)
                intervals.append((start, end))

    # Add Korean by default for Korean font names
    if 'hangul' in font_name.lower() or 'korean' in font_name.lower() or 'hangeuljaemin' in font_name.lower():
        intervals.extend(korean_intervals)

    # Sort and merge intervals
    unmerged_intervals = sorted(intervals)
    merged_intervals = []
    for i_start, i_end in unmerged_intervals:
        if merged_intervals and i_start <= merged_intervals[-1][1] + 1:
            merged_intervals[-1] = (merged_intervals[-1][0], max(merged_intervals[-1][1], i_end))
        else:
            merged_intervals.append((i_start, i_end))

    # Validate intervals (remove code points not in font)
    validated_intervals = []
    for i_start, i_end in merged_intervals:
        start = i_start
        for code_point in range(i_start, i_end + 1):
            face = load_glyph(font_stack, code_point, load_flags)
            if face is None:
                if start < code_point:
                    validated_intervals.append((start, code_point - 1))
                start = code_point + 1
        if start <= i_end:
            validated_intervals.append((start, i_end))

    print(f"Processing {len(validated_intervals)} intervals...")

    # Generate glyphs
    total_size = 0
    all_glyphs = []

    for i_start, i_end in validated_intervals:
        for code_point in range(i_start, i_end + 1):
            face = load_glyph(font_stack, code_point, load_flags)
            if face is None:
                continue

            bitmap = face.glyph.bitmap

            if is_2bit:
                pixels = pack_2bit(bitmap)
            else:
                pixels = pack_1bit(bitmap)

            packed = bytes(pixels)
            glyph = GlyphProps(
                width=bitmap.width,
                height=bitmap.rows,
                # Round-to-nearest so sub-pixel advances do not accumulate as
                # systematically tight spacing across a line of text.
                advance_x=norm_round(face.glyph.advance.x),
                left=face.glyph.bitmap_left,
                top=face.glyph.bitmap_top,
                data_length=len(packed),
                data_offset=total_size,
                code_point=code_point,
            )
            total_size += len(packed)
            all_glyphs.append((glyph, packed))

    # Get font metrics from pipe character
    face = load_glyph(font_stack, ord('|'), load_flags)
    if face is None:
        face = font_stack[0]

    advance_y = norm_ceil(face.size.height)
    ascender = norm_ceil(face.size.ascender)
    descender = norm_floor(face.size.descender)

    print(f"Generated {len(all_glyphs)} glyphs")
    print(f"Font metrics: advanceY={advance_y}, ascender={ascender}, descender={descender}")

    # Write .epdfont file
    write_epdfont(output_path, validated_intervals, all_glyphs, advance_y, ascender, descender, is_2bit)

    return True

def write_epdfont(output_path, intervals, all_glyphs, advance_y, ascender, descender, is_2bit):
    """Write font data to .epdfont binary file."""

    # Calculate offsets
    header_size = 32
    intervals_size = len(intervals) * 12
    glyphs_size = len(all_glyphs) * 16

    intervals_offset = header_size
    glyphs_offset = intervals_offset + intervals_size
    bitmap_offset = glyphs_offset + glyphs_size

    # Collect bitmap data
    bitmap_data = b''.join([packed for _, packed in all_glyphs])

    with open(output_path, 'wb') as f:
        # Write header (32 bytes)
        header = struct.pack(
            '<IHBBBBBB5I',
            EPDFONT_MAGIC,           # uint32 magic
            EPDFONT_VERSION,         # uint16 version
            1 if is_2bit else 0,     # uint8 is2Bit
            0,                       # uint8 reserved1
            advance_y & 0xFF,        # uint8 advanceY
            ascender & 0xFF,         # int8 ascender
            descender & 0xFF,        # int8 descender (signed)
            0,                       # uint8 reserved2
            len(intervals),          # uint32 intervalCount
            len(all_glyphs),         # uint32 glyphCount
            intervals_offset,        # uint32 intervalsOffset
            glyphs_offset,           # uint32 glyphsOffset
            bitmap_offset,           # uint32 bitmapOffset
        )
        f.write(header)

        # Write intervals
        offset = 0
        for i_start, i_end in intervals:
            f.write(struct.pack('<3I', i_start, i_end, offset))
            offset += i_end - i_start + 1

        # Write glyphs
        for glyph, _ in all_glyphs:
            f.write(struct.pack(
                '<4B2h2I',
                glyph.width,
                glyph.height,
                glyph.advance_x,
                0,  # reserved
                glyph.left,
                glyph.top,
                glyph.data_length,
                glyph.data_offset,
            ))

        # Write bitmap data
        f.write(bitmap_data)

    total_size = bitmap_offset + len(bitmap_data)
    print(f"\nCreated: {output_path}")
    print(f"  Intervals: {len(intervals)}")
    print(f"  Glyphs: {len(all_glyphs)}")
    print(f"  Bitmap size: {len(bitmap_data)} bytes")
    print(f"  Total file size: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")

def main():
    parser = argparse.ArgumentParser(description='Convert TTF/OTF font to .epdfont binary format')
    parser.add_argument('name', help='Font name (used for identification)')
    parser.add_argument('size', type=int, help='Font size in points')
    parser.add_argument('fontfiles', nargs='+', help='TTF/OTF font file(s), in priority order')
    parser.add_argument('--2bit', dest='is_2bit', action='store_true', help='Generate 2-bit greyscale instead of 1-bit')
    parser.add_argument('--force-autohint', dest='force_autohint', action='store_true',
                        help='Force the FreeType auto-hinter. Recommended for CFF-based CJK fonts at small pixel sizes where native hints are weak.')
    parser.add_argument('--additional-intervals', dest='additional_intervals', action='append',
                        help='Additional Unicode intervals as MIN,MAX (hex or decimal). Can be repeated.')
    parser.add_argument('-o', '--output', dest='output', help='Output .epdfont file path')
    args = parser.parse_args()

    output_path = args.output if args.output else f"{args.name}_{args.size}.epdfont"

    print(f"Converting {args.fontfiles[0]} to {output_path}")
    print(f"Font: {args.name}, Size: {args.size}pt, Mode: {'2-bit' if args.is_2bit else '1-bit'}, Autohint: {args.force_autohint}")
    print("")

    success = convert_ttf_to_epdfont(
        args.fontfiles,
        args.name,
        args.size,
        output_path,
        args.additional_intervals,
        args.is_2bit,
        args.force_autohint,
    )

    if success:
        print("\nConversion complete!")
    else:
        print("\nConversion failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
