// Embedded Pretendard JP fonts (2-bit) in Flash via .incbin assembly.
// Zero-copy: intervals read directly from Flash, no RAM allocation.
#pragma once

#define PRETENDARD_12_FONT_ID (-800000012)
#define PRETENDARD_14_FONT_ID (-800000014)
#define PRETENDARD_16_FONT_ID (-800000016)

// Aliases for UI contexts
#define UI_10_FONT_ID  PRETENDARD_12_FONT_ID
#define UI_12_FONT_ID  PRETENDARD_12_FONT_ID
#define SMALL_FONT_ID  PRETENDARD_12_FONT_ID

// Custom reader font loaded from SD card by FontSelectionActivity
#define CUSTOM_FONT_ID (-999999)
