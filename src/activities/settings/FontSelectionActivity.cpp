#include "FontSelectionActivity.h"

#include <GfxRenderer.h>
#include <HalStorage.h>
#include <HardwareSerial.h>
#include <Logging.h>

#include <cstring>

#include "CrossPointSettings.h"
#include "FontManager.h"
#include "MappedInputManager.h"
#include "components/UITheme.h"
#include "fontIds.h"

namespace {
constexpr const char* CACHE_DIR = "/.crosspoint/cache";

// Recursively delete a directory and its contents
void deleteDirectory(const char* path) {
  FsFile dir = Storage.open(path);
  if (!dir || !dir.isDirectory()) {
    if (dir) dir.close();
    return;
  }

  for (auto entry = dir.openNextFile(); entry; entry = dir.openNextFile()) {
    char entryName[64];
    entry.getName(entryName, sizeof(entryName));
    bool isDir = entry.isDirectory();
    entry.close();

    std::string fullPath = std::string(path) + "/" + entryName;
    if (isDir) {
      deleteDirectory(fullPath.c_str());
    } else {
      Storage.remove(fullPath.c_str());
    }
  }
  dir.close();
  Storage.rmdir(path);
}

// Invalidate rendering caches for EPUB reader
// Keeps progress.bin (reading position) but removes layout caches
void invalidateReaderCaches() {
  LOG_DBG("FNT", "Invalidating reader rendering caches...");

  FsFile cacheDir = Storage.open(CACHE_DIR);
  if (!cacheDir || !cacheDir.isDirectory()) {
    if (cacheDir) cacheDir.close();
    LOG_DBG("FNT", "No cache directory found");
    return;
  }

  int deletedCount = 0;
  for (auto bookCache = cacheDir.openNextFile(); bookCache; bookCache = cacheDir.openNextFile()) {
    char bookCacheName[64];
    bookCache.getName(bookCacheName, sizeof(bookCacheName));
    bookCache.close();

    std::string bookCachePath = std::string(CACHE_DIR) + "/" + bookCacheName;

    // For EPUB: delete sections/ folder (keeps progress.bin)
    std::string sectionsPath = bookCachePath + "/sections";
    FsFile sectionsDir = Storage.open(sectionsPath.c_str());
    if (sectionsDir && sectionsDir.isDirectory()) {
      sectionsDir.close();
      deleteDirectory(sectionsPath.c_str());
      LOG_DBG("FNT", "Deleted EPUB sections cache: %s", sectionsPath.c_str());
      deletedCount++;
    } else {
      if (sectionsDir) sectionsDir.close();
    }
  }
  cacheDir.close();

  LOG_DBG("FNT", "Invalidated %d cache entries", deletedCount);
}
}  // namespace

void FontSelectionActivity::taskTrampoline(void* param) {
  auto* self = static_cast<FontSelectionActivity*>(param);
  self->displayTaskLoop();
}

void FontSelectionActivity::scanFontsInDirectory(const char* dirPath) {
  FsFile dir = Storage.open(dirPath);
  if (!dir) {
    LOG_DBG("FNT", "Font folder %s not found", dirPath);
    return;
  }

  if (!dir.isDirectory()) {
    LOG_DBG("FNT", "%s is not a directory", dirPath);
    dir.close();
    return;
  }

  for (auto file = dir.openNextFile(); file; file = dir.openNextFile()) {
    if (!file.isDirectory()) {
      char filename[64];
      file.getName(filename, sizeof(filename));

      const size_t len = strlen(filename);
      if (len > 8 && strcasecmp(filename + len - 8, ".epdfont") == 0 && strncmp(filename, "._", 2) != 0) {
        std::string fullPath = std::string(dirPath) + "/" + filename;
        fontFiles.push_back(fullPath);

        std::string displayName(filename, len - 8);
        fontNames.push_back(displayName);

        LOG_DBG("FNT", "Found font: %s", fullPath.c_str());
      }
    }
    file.close();
  }
  dir.close();
}

void FontSelectionActivity::loadFontList() {
  fontFiles.clear();
  fontNames.clear();

  // Built-in Pretendard sizes
  fontFiles.emplace_back("builtin:12");
  fontNames.emplace_back("Pretendard 12pt (Built-in)");
  fontFiles.emplace_back("builtin:14");
  fontNames.emplace_back("Pretendard 14pt (Built-in)");
  fontFiles.emplace_back("builtin:16");
  fontNames.emplace_back("Pretendard 16pt (Built-in)");

  Storage.mkdir("/.crosspoint");
  Storage.mkdir(FONTS_DIR);

  scanFontsInDirectory(FONTS_DIR);
  scanFontsInDirectory(ROOT_FONTS_DIR);

  LOG_DBG("FNT", "Total fonts found: %zu (including built-in)", fontFiles.size());

  // Find currently selected font index
  selectedIndex = 0;
  if (SETTINGS.customFontPath[0] != '\0') {
    for (size_t i = 1; i < fontFiles.size(); i++) {
      if (fontFiles[i] == SETTINGS.customFontPath) {
        selectedIndex = static_cast<int>(i);
        break;
      }
    }
  }
}

void FontSelectionActivity::onEnter() {
  Activity::onEnter();

  displayMutex = xSemaphoreCreateMutex();
  loadFontList();
  updateRequired = true;

  xTaskCreate(&FontSelectionActivity::taskTrampoline, "FontSelectionTask",
              4096, this, 1, &displayTaskHandle);
}

void FontSelectionActivity::onExit() {
  xSemaphoreTake(displayMutex, portMAX_DELAY);
  if (displayTaskHandle) {
    vTaskDelete(displayTaskHandle);
    displayTaskHandle = nullptr;
  }
  vSemaphoreDelete(displayMutex);
  displayMutex = nullptr;

  Activity::onExit();
}

void FontSelectionActivity::loop() {
  if (mappedInput.wasPressed(MappedInputManager::Button::Back)) {
    finish();
    return;
  }

  if (mappedInput.wasPressed(MappedInputManager::Button::Confirm)) {
    handleSelection();
    return;
  }

  const int itemCount = static_cast<int>(fontNames.size());
  if (mappedInput.wasPressed(MappedInputManager::Button::Up) ||
      mappedInput.wasPressed(MappedInputManager::Button::Left)) {
    selectedIndex = (selectedIndex + itemCount - 1) % itemCount;
    updateRequired = true;
  } else if (mappedInput.wasPressed(MappedInputManager::Button::Down) ||
             mappedInput.wasPressed(MappedInputManager::Button::Right)) {
    selectedIndex = (selectedIndex + 1) % itemCount;
    updateRequired = true;
  }
}

void FontSelectionActivity::handleSelection() {
  // Stop the display task first to eliminate mutex contention.
  // Heavy SD I/O (font load + cache deletion) under mutex causes watchdog reboot.
  xSemaphoreTake(displayMutex, portMAX_DELAY);
  if (displayTaskHandle) {
    vTaskDelete(displayTaskHandle);
    displayTaskHandle = nullptr;
  }
  xSemaphoreGive(displayMutex);

  // Now safe to use renderer directly ??no competing task
  renderer.clearScreen();
  renderer.drawCenteredText(UI_12_FONT_ID, renderer.getScreenHeight() / 2 - 10, "Applying font...");
  renderer.displayBuffer();

  strncpy(SETTINGS.customFontPath, fontFiles[selectedIndex].c_str(), sizeof(SETTINGS.customFontPath) - 1);
  SETTINGS.customFontPath[sizeof(SETTINGS.customFontPath) - 1] = '\0';

  SETTINGS.saveToFile();
  LOG_DBG("FNT", "Font selected: %s", SETTINGS.customFontPath);

  reloadCustomReaderFont();
  invalidateReaderCaches();

  finish();
}

void FontSelectionActivity::displayTaskLoop() {
  while (true) {
    if (updateRequired) {
      updateRequired = false;
      xSemaphoreTake(displayMutex, portMAX_DELAY);
      doRender();
      xSemaphoreGive(displayMutex);
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void FontSelectionActivity::doRender() {
  const auto pageWidth = renderer.getScreenWidth();
  const auto pageHeight = renderer.getScreenHeight();

  auto drawContent = [&]() {
    renderer.clearScreen();

    renderer.drawCenteredText(UI_12_FONT_ID, 15, "Font Selection", true, EpdFontFamily::BOLD);

    constexpr int lineHeight = 30;
    constexpr int startY = 60;
    const int maxVisibleItems = (pageHeight - startY - 50) / lineHeight;
    const int itemCount = static_cast<int>(fontNames.size());

    int scrollOffset = 0;
    if (itemCount > maxVisibleItems) {
      if (selectedIndex >= maxVisibleItems) {
        scrollOffset = selectedIndex - maxVisibleItems + 1;
      }
    }

    int currentSelectedIndex = 0;
    if (SETTINGS.customFontPath[0] != '\0') {
      for (size_t i = 0; i < fontFiles.size(); i++) {
        if (fontFiles[i] == SETTINGS.customFontPath) {
          currentSelectedIndex = static_cast<int>(i);
          break;
        }
      }
    }

    for (int i = 0; i < maxVisibleItems && (i + scrollOffset) < itemCount; i++) {
      const int itemIndex = i + scrollOffset;
      const int itemY = startY + i * lineHeight;
      const bool isHighlighted = (itemIndex == selectedIndex);
      const bool isCurrentFont = (itemIndex == currentSelectedIndex);

      if (isHighlighted) {
        renderer.fillRect(0, itemY - 2, pageWidth - 1, lineHeight);
      }

      if (isCurrentFont) {
        renderer.drawText(UI_12_FONT_ID, 10, itemY, "*", !isHighlighted);
      }

      renderer.drawText(UI_12_FONT_ID, 35, itemY, fontNames[itemIndex].c_str(), !isHighlighted);
    }

    if (scrollOffset > 0) {
      renderer.drawCenteredText(UI_12_FONT_ID, startY - 15, "...", true);
    }
    if (scrollOffset + maxVisibleItems < itemCount) {
      renderer.drawCenteredText(UI_12_FONT_ID, startY + maxVisibleItems * lineHeight, "...", true);
    }

    const auto labels = mappedInput.mapLabels("Back", "Select", "", "");
    GUI.drawButtonHints(renderer, labels.btn1, labels.btn2, labels.btn3, labels.btn4);
  };
  drawContent();
  renderer.displayBufferWithAA(drawContent);
}
