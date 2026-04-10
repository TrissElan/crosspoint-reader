# CrossPoint Reader - CJK Fork

A CJK (Korean/Japanese) font support fork of the [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader) firmware for the Xteink X4 e-paper reader.

## Features

- **Pretendard JP 12/14/16pt** embedded in Flash (2-bit antialiased, zero-copy)
- **Reduced character set**: Adobe KR-0 hangul (2,780) + education hanja (1,823) + Hiragana/Katakana + Latin/Cyrillic
- **WiFi file transfer**: built-in hotspot with web-based file browser (upload, delete, rename, move)
- SD card-based custom font loading via `.epdfont` format
- Font selection UI — choose between 3 built-in sizes or SD card fonts
- Per-font section cache invalidation (djb2 hash-based font ID)
- Flash font zero-copy optimization (~51KB RAM saved)

## Changes from Upstream

- **Font system overhaul**: Removed Bookerly font family (10/12/14/16/18pt × 4 styles), replaced with Pretendard JP 12/14/16pt embedded in Flash
- **SdFont/SdFontFamily**: New on-demand glyph loading system for SD card fonts with LRU bitmap cache
- **FontSelectionActivity**: UI for selecting built-in font sizes and browsing `.epdfont` files from SD card
- **WiFi file transfer**: Restored from upstream with simplified hotspot-only mode (no Join Network)
- **Bug fixes**:
  - GlyphBitmapCache collision between built-in and SD fonts (composite cache key)
  - Font setting not persisting across reboots
  - System reboot when selecting SD font (display task lifecycle)
  - Grey pixel remnants from `storeBwBuffer` malloc failure
  - Settings Back button event leak to reader
  - Theme not switching (enum value alignment)
  - SD-to-SD font change not triggering re-indexing
  - Home screen Settings unreachable (menu item count off-by-one)

## Removed from Upstream

This fork is a minimal CJK-focused build. The following upstream features have been removed to reduce firmware size and complexity:

| Category | Removed |
|---|---|
| **Built-in Fonts** | Bookerly (12–18pt), NotoSans (8–18pt), OpenDyslexic (8–14pt), Ubuntu (10–12pt) — all styles (regular/bold/italic/bolditalic). Replaced with Pretendard JP 12/14/16pt |
| **Font System** | FontDecompressor (compressed font loading), FontCacheManager (old cache) |
| **Multi-language** | 20 translation files removed — UI is English only |
| **OTA Update** | Over-the-air firmware update |
| **KOReader Sync** | Reading progress sync with KOReader server |
| **OPDS Catalog** | OPDS book browser and parser |
| **TXT Reader** | Plain text file reading |
| **XTC Reader** | XTC format support |
| **Calibre / WebDAV** | Calibre integration, WebDAV sync |

### What Still Works

- **EPUB reader** — core reading, pagination, chapter navigation, TOC
- **SD card file browser** — browse and open EPUB files
- **SD card custom fonts** — load `.epdfont` files from SD card
- **WiFi file transfer** — hotspot mode, web-based file browser with upload/delete/rename
- **Settings** — font selection (12/14/16pt + SD), theme, sleep timer, orientation
- **Themes** — Lyra, Lyra 3 Covers
- **Sleep / wake** — auto and manual sleep
- **Battery indicator**
- **QR code display** — WiFi connection and URL QR codes

## Limitations

- SD card fonts consume RAM for interval tables (~51KB per font for full CJK coverage)
- Anti-aliasing may be skipped when RAM is insufficient for BW buffer backup

## How to Build

```bash
# Clone with submodules
git clone --recursive https://github.com/TrissElan/crosspoint-reader-cjk-minimized.git

# Build
cd crosspoint-reader-cjk-minimized
pio run

# Flash
pio run --target upload
```

## Generating Custom Fonts

Place `.epdfont` files in `/.crosspoint/fonts/` on the SD card.
Font files can be generated using the included script:

```bash
cd lib/EpdFont/scripts
python generate_pretendard_font.py 12 14 16
```

## Credits

- Original project: [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader)
- Referenced: [crosspoint-reader-ko](https://github.com/crosspoint-reader-ko/crosspoint-reader-ko) - font-path hash-based cache invalidation, SD font architecture patterns
- CJK fork by: TrissElan

## License

This project is licensed under the same license as the original CrossPoint Reader project.
