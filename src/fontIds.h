// All fonts use the embedded Pretendard JP 12pt (2-bit) epdfont.
// A single font ID is shared across all UI and reader contexts.
#pragma once

// Pretendard JP 12pt – embedded in Flash via .incbin assembly.
// Used for all UI and EPUB reader rendering.
#define PRETENDARD_12_FONT_ID (-800000012)

// Aliases so existing call-sites compile without changes
#define UI_10_FONT_ID  PRETENDARD_12_FONT_ID
#define UI_12_FONT_ID  PRETENDARD_12_FONT_ID
#define SMALL_FONT_ID  PRETENDARD_12_FONT_ID

// Custom reader font loaded from SD card by FontSelectionActivity
#define CUSTOM_FONT_ID (-999999)
