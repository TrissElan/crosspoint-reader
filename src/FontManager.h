#pragma once

#include <GfxRenderer.h>

// Load the custom reader font configured in SETTINGS.customFontPath.
// Returns true if the font was loaded successfully.
bool loadCustomReaderFont(GfxRenderer& gfxRenderer);

// Remove the existing custom font (if any) and re-load from SETTINGS.
// Call this after the user picks a new font in FontSelectionActivity.
bool reloadCustomReaderFont();

// Expose the global renderer for modules that need font operations.
GfxRenderer& getGlobalRenderer();
