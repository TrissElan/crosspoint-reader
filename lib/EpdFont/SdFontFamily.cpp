#include "SdFontFamily.h"

#include <HardwareSerial.h>

// ============================================================================
// SdFontFamily Implementation
// ============================================================================

SdFontFamily::~SdFontFamily() {
  if (ownsPointers) {
    delete regular;
    delete bold;
    delete italic;
    delete boldItalic;
  }
}

bool SdFontFamily::load() {
  bool success = true;

  if (regular && !regular->load()) {
    Serial.printf("[%lu] [SdFontFamily] Failed to load regular font\n", millis());
    success = false;
  }
  if (bold && !bold->load()) {
    Serial.printf("[%lu] [SdFontFamily] Failed to load bold font\n", millis());
    // Bold is optional, don't fail completely
  }
  if (italic && !italic->load()) {
    Serial.printf("[%lu] [SdFontFamily] Failed to load italic font\n", millis());
    // Italic is optional
  }
  if (boldItalic && !boldItalic->load()) {
    Serial.printf("[%lu] [SdFontFamily] Failed to load bold-italic font\n", millis());
    // Bold-italic is optional
  }

  return success;
}

bool SdFontFamily::isLoaded() const { return regular && regular->isLoaded(); }

SdFont* SdFontFamily::getFont(EpdFontStyle style) const {
  if (style == BOLD && bold && bold->isLoaded()) {
    return bold;
  }
  if (style == ITALIC && italic && italic->isLoaded()) {
    return italic;
  }
  if (style == BOLD_ITALIC) {
    if (boldItalic && boldItalic->isLoaded()) {
      return boldItalic;
    }
    if (bold && bold->isLoaded()) {
      return bold;
    }
    if (italic && italic->isLoaded()) {
      return italic;
    }
  }

  return regular;
}

void SdFontFamily::getTextDimensions(const char* string, int* w, int* h, EpdFontStyle style) const {
  SdFont* font = getFont(style);
  if (font) {
    font->getTextDimensions(string, w, h);
  } else {
    *w = 0;
    *h = 0;
  }
}

bool SdFontFamily::hasPrintableChars(const char* string, EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->hasPrintableChars(string) : false;
}

const EpdGlyph* SdFontFamily::getGlyph(uint32_t cp, EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->getGlyph(cp) : nullptr;
}

const uint8_t* SdFontFamily::getGlyphBitmap(uint32_t cp, EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->getGlyphBitmap(cp) : nullptr;
}

uint8_t SdFontFamily::getAdvanceY(EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->getAdvanceY() : 0;
}

int8_t SdFontFamily::getAscender(EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->getAscender() : 0;
}

int8_t SdFontFamily::getDescender(EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->getDescender() : 0;
}

bool SdFontFamily::is2Bit(EpdFontStyle style) const {
  SdFont* font = getFont(style);
  return font ? font->is2Bit() : false;
}
