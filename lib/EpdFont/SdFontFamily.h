#pragma once

#include "EpdFontFamily.h"
#include "SdFont.h"

/**
 * SD Card font family - similar interface to EpdFontFamily but uses SdFont.
 * Supports regular, bold, italic, and bold-italic variants.
 */
class SdFontFamily {
 private:
  SdFont* regular;
  SdFont* bold;
  SdFont* italic;
  SdFont* boldItalic;
  bool ownsPointers;

  SdFont* getFont(EpdFontStyle style) const;

 public:
  // Constructor with raw pointers (does not take ownership)
  explicit SdFontFamily(SdFont* regular, SdFont* bold = nullptr, SdFont* italic = nullptr, SdFont* boldItalic = nullptr)
      : regular(regular), bold(bold), italic(italic), boldItalic(boldItalic), ownsPointers(false) {}

  ~SdFontFamily();

  // Disable copy
  SdFontFamily(const SdFontFamily&) = delete;
  SdFontFamily& operator=(const SdFontFamily&) = delete;

  // Load all fonts in the family
  bool load();
  bool isLoaded() const;

  // EpdFontFamily-compatible interface
  void getTextDimensions(const char* string, int* w, int* h, EpdFontStyle style = REGULAR) const;
  bool hasPrintableChars(const char* string, EpdFontStyle style = REGULAR) const;

  // Get glyph (metadata only, no bitmap)
  const EpdGlyph* getGlyph(uint32_t cp, EpdFontStyle style = REGULAR) const;

  // Get glyph bitmap data (loaded on demand from SD)
  const uint8_t* getGlyphBitmap(uint32_t cp, EpdFontStyle style = REGULAR) const;

  // Font metadata
  uint8_t getAdvanceY(EpdFontStyle style = REGULAR) const;
  int8_t getAscender(EpdFontStyle style = REGULAR) const;
  int8_t getDescender(EpdFontStyle style = REGULAR) const;
  bool is2Bit(EpdFontStyle style = REGULAR) const;

  // Check if bold variant is available
  bool hasBold() const { return bold != nullptr; }
};
