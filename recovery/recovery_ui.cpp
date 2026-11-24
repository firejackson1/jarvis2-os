// SPDX-License-Identifier: Apache-2.0
#include <recovery_ui/device.h>
#include <recovery_ui/screen_ui.h>
#include "button_mapping.h"
#include "lcars_menu.h"

// Public minui API, verified against the pinned minui/include/minui/minui.h.
void gr_color(unsigned char r, unsigned char g, unsigned char b, unsigned char a);

class Jarvis2RecoveryUI final : public ScreenRecoveryUI {
 public:
  KeyAction CheckKey(int key, bool held) override {
    if (key == KEY_OK || key == KEY_SELECT || key == KEY_KPENTER) {
      EnqueueKey(KEY_ENTER);
      return IGNORE;
    }
    switch (jarvis2::BoxButton(key, held, IsTextVisible())) {
      case jarvis2::BoxAction::Delegate:
        return ScreenRecoveryUI::CheckKey(key, held);
      case jarvis2::BoxAction::Reveal:
        ShowText(true);
        return IGNORE;
      case jarvis2::BoxAction::Next:
        EnqueueKey(KEY_TAB);
        return IGNORE;
      case jarvis2::BoxAction::Select:
        EnqueueKey(KEY_ENTER);
        return IGNORE;
    }
    return IGNORE;
  }

  bool SetMenuDirection(jarvis2::Direction direction) {
    std::lock_guard<std::mutex> lock(updateMutex);
    if (!lcars_active_ || !menu_) return false;
    static_cast<jarvis2::LcarsMenu*>(menu_.get())->SetDirection(direction);
    return true;
  }
 protected:
  std::unique_ptr<Menu> CreateMenu(const std::vector<std::string>& headers,
      const std::vector<std::string>& items, size_t selected) const override {
    auto display_headers = headers;
    display_headers.insert(display_headers.begin(), "DEVELOPMENT UI - NOT BOOT TESTED");
    auto menu = std::make_unique<jarvis2::LcarsMenu>(display_headers, items, selected, *this, ScreenWidth(), ScreenHeight(), headers.empty());
    lcars_active_ = menu->CanRender();
    if (!lcars_active_) return ScreenRecoveryUI::CreateMenu(headers, items, selected);
    return menu;
  }
  std::unique_ptr<Menu> CreateMenu(const GRSurface*, const std::vector<const GRSurface*>&,
      const std::vector<std::string>& headers, const std::vector<std::string>& items,
      size_t selected) const override {
    return CreateMenu(headers, items, selected);
  }
  void SetColor(UIElement element) const override {
    switch (element) {
      case UIElement::HEADER: gr_color(246,174,98,255); break;
      case UIElement::MENU_BG: gr_color(21,27,37,255); break;
      case UIElement::MENU_SEL_BG: gr_color(182,160,218,255); break;
      case UIElement::MENU_SEL_BG_ACTIVE: gr_color(246,174,98,255); break;
      case UIElement::MENU_SEL_FG: gr_color(11,14,20,255); break;
      case UIElement::TEXT_FILL: gr_color(11,14,20,255); break;
      case UIElement::INFO: gr_color(174,184,202,255); break;
      default: gr_color(237,241,248,255); break;
    }
  }
  void draw_menu_and_text_buffer_locked(const std::vector<std::string>& help) override {
    if (!menu_ || !lcars_active_) {
      ScreenRecoveryUI::draw_menu_and_text_buffer_locked(help);
      return;
    }
    SetColor(UIElement::TEXT_FILL);
    DrawFill(0, 0, ScreenWidth(), ScreenHeight());
    menu_start_y_ = menu_->DrawHeader(0, 0);
    menu_->SetMenuHeight(ScreenHeight());
    menu_->DrawItems(0, 0, ScreenWidth(), IsLongPress());
  }
  int SelectMenu(const Point& point) override {
    if (!lcars_active_) return ScreenRecoveryUI::SelectMenu(point);
    std::lock_guard<std::mutex> lock(updateMutex);
    if (!menu_) return -1;
    auto* lcars = static_cast<jarvis2::LcarsMenu*>(menu_.get());
    auto geometry = lcars->Geometry();
    for (const auto& tile : geometry.tiles) {
      if (point.x() >= tile.x && point.x() < tile.x+tile.w && point.y() >= tile.y && point.y() < tile.y+tile.h) {
        menu_->Select(lcars->LogicalIndex(tile.index));
        update_screen_locked();
        break;
      }
    }
    return menu_->selection();
  }
 private:
  mutable bool lcars_active_ = false;
};

class Jarvis2RecoveryDevice final : public Device {
 public:
  Jarvis2RecoveryDevice() : Device(new Jarvis2RecoveryUI) {
    // Keep the first bring-up menu diagnostic-only. This is not confinement:
    // an independently authorized root shell can still write block devices.
    for (auto action : {WIPE_DATA, WIPE_CACHE, WIPE_SYSTEM, MENU_WIPE,
                        APPLY_UPDATE, APPLY_ADB_SIDELOAD}) {
      RemoveMenuItemForAction(action);
    }
  }

  int HandleMenuKey(int key, bool visible) override {
    if (visible && key == KEY_TAB) return kHighlightDown; // one-button linear traversal, including Back
    if (visible && (key == KEY_UP || key == KEY_DOWN || key == KEY_LEFT || key == KEY_RIGHT)) {
      auto direction = key == KEY_UP ? jarvis2::Direction::Up : key == KEY_DOWN ? jarvis2::Direction::Down
                       : key == KEY_LEFT ? jarvis2::Direction::Left : jarvis2::Direction::Right;
      if (static_cast<Jarvis2RecoveryUI*>(GetUI())->SetMenuDirection(direction)) return kHighlightDown;
    }
    if (visible && (key == KEY_HOME || key == KEY_HOMEPAGE)) return kGoHome;
    if (visible && (key == KEY_BACK || key == KEY_ESC || key == KEY_BACKSPACE)) return kGoBack;
    return Device::HandleMenuKey(key, visible);
  }

  void StartRecovery() override {
    GetUI()->SetTitle({"Jarvis2 LCARS Recovery", "OFFLINE PORT - UNTESTED"});
    GetUI()->ShowText(true);
  }

  bool PreWipeData() override { return false; }
};

Device* make_device() { return new Jarvis2RecoveryDevice; }
