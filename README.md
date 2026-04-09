# CrossPoint Reader - CJK Fork

A CJK (Korean/Japanese) font support fork of the [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader) firmware for the Xteink X4 e-paper reader.

## Features

- Replaced built-in Bookerly fonts with Pretendard JP 12pt (Flash-embedded, 2-bit antialiased)
- SD card-based custom font loading via `.epdfont` format
- Font selection UI (Settings -> Font)
- Per-font section cache invalidation (djb2 hash-based font ID)
- Flash font zero-copy optimization (~51KB RAM saved)

## Changes from Upstream

- **Font system overhaul**: Removed Bookerly font family (10/12/14/16/18pt x 4 styles), replaced with single Pretendard JP 12pt embedded in Flash
- **SdFont/SdFontFamily**: New on-demand glyph loading system for SD card fonts with LRU bitmap cache
- **FontSelectionActivity**: UI for browsing and selecting `.epdfont` files from SD card
- **Bug fixes**:
  - GlyphBitmapCache collision between built-in and SD fonts (composite cache key)
  - Font setting not persisting across reboots
  - System reboot when selecting SD font (display task lifecycle)
  - Grey pixel remnants from `storeBwBuffer` malloc failure
  - Settings Back button event leak to reader
  - Theme not switching (enum value alignment)
  - SD-to-SD font change not triggering re-indexing

## Limitations

- Only Pretendard JP 12pt is embedded in Flash - other sizes require SD card font files
- SD card fonts consume RAM for interval tables (~51KB per font for full CJK coverage)
- Anti-aliasing may be skipped when RAM is insufficient for BW buffer backup

## How to Build

```bash
# Clone with submodules
git clone --recursive https://github.com/TrissElan/crosspoint-reader.git

# Build
cd crosspoint-reader
pio run

# Flash
pio run --target upload
```

## Generating Custom Fonts

Place `.epdfont` files in `/.crosspoint/fonts/` on the SD card.
Font files can be generated using the included script:

```bash
cd lib/EpdFont/scripts
python generate_pretendard_font.py
```

## Credits

- Original project: [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader)
- Referenced: [crosspoint-reader-ko](https://github.com/crosspoint-reader-ko/crosspoint-reader-ko) - font-path hash-based cache invalidation, SD font architecture patterns
- CJK fork by: TrissElan

## License

This project is licensed under the same license as the original CrossPoint Reader project.
