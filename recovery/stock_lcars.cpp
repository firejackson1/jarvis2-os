// SPDX-License-Identifier: Apache-2.0
#include <dlfcn.h>
#include <otautil/boot_state.h>
#include <recovery_ui/device.h>
#include <recovery_ui/screen_ui.h>

#include "recovery/button_mapping.h"
#include "recovery/lcars_layout.h"

void gr_color(unsigned char red, unsigned char green, unsigned char blue, unsigned char alpha);

namespace {

class StockLcarsMenu final : public Menu {
 public:
  StockLcarsMenu(const std::vector<std::string>& headers, const std::vector<std::string>& items,
                 size_t selected, const DrawInterface& draw, int width, int height,
                 int char_width, int char_height)
      : Menu(std::min(selected, items.size() - 1), draw),
        headers_(headers),
        items_(items),
        width_(width),
        height_(height),
        char_width_(char_width),
        char_height_(char_height) {}

  int Select(int selected) override {
    const int count = items_.size();
    selection_ = (selected % count + count) % count;
    return selection_;
  }

  jarvis2::LcarsGeometry Geometry() const {
    return jarvis2::LcarsLayout(width_, height_, char_width_, char_height_,
                               items_.size(), selection_, headers_.size());
  }

  int DrawHeader(int, int) const override {
    const auto layout = Geometry();
    const int max_chars = (width_ - 2 * layout.margin) / char_width_;
    gr_color(246, 174, 98, 255);
    draw_funcs_.DrawHighlightBar(layout.margin, layout.margin,
                                 width_ - 2 * layout.margin, std::max(4, char_height_ / 3));
    gr_color(237, 241, 248, 255);
    draw_funcs_.DrawTextLine(layout.margin, layout.margin + char_height_,
                             "JARVIS2 // RECOVERY", true);
    for (size_t index = 0; index < headers_.size(); ++index) {
      draw_funcs_.DrawTextLine(layout.margin, layout.margin + (index + 2) * char_height_,
                               headers_[index].substr(0, max_chars), false);
    }
    return layout.header_bottom;
  }

  int DrawItems(int, int, int, bool held) const override {
    const auto layout = Geometry();
    if (layout.rail > 0) {
      gr_color(246, 174, 98, 255);
      draw_funcs_.DrawHighlightBar(layout.margin, layout.header_bottom, layout.rail - 4,
                                   layout.footer_top - layout.header_bottom);
    }
    for (const auto& tile : layout.tiles) {
      const bool focused = static_cast<size_t>(tile.index) == selection_;
      if (focused && held) {
        gr_color(246, 174, 98, 255);
      } else if (focused) {
        gr_color(182, 160, 218, 255);
      } else {
        gr_color(21, 27, 37, 255);
      }
      draw_funcs_.DrawHighlightBar(tile.x, tile.y, tile.w, tile.h);
      if (focused) {
        gr_color(11, 14, 20, 255);
      } else {
        gr_color(237, 241, 248, 255);
      }
      const std::string label =
          std::to_string(tile.index + 1) + " / " + items_[tile.index];
      draw_funcs_.DrawTextLine(tile.x + char_width_, tile.y + char_height_,
                               label.substr(0, tile.w / char_width_ - 2), focused);
    }
    gr_color(174, 184, 202, 255);
    draw_funcs_.DrawTextLine(layout.margin, layout.footer_top,
                             "Tap: next   Hold: select   Arrows: move   Enter: select", false);
    return layout.footer_top - layout.header_bottom;
  }

 private:
  const std::vector<std::string> headers_;
  const std::vector<std::string> items_;
  const int width_;
  const int height_;
  const int char_width_;
  const int char_height_;
};

class StockLcarsUI final : public ScreenRecoveryUI {
 public:
  KeyAction CheckKey(int key, bool held) override {
    if (key == KEY_OK || key == KEY_SELECT || key == KEY_KPENTER) {
      EnqueueKey(KEY_ENTER);
      return IGNORE;
    }
    switch (jarvis2::BoxButton(key, held, IsTextVisible())) {
      case jarvis2::BoxAction::Reveal:
        ShowText(true);
        return IGNORE;
      case jarvis2::BoxAction::Next:
        EnqueueKey(KEY_DOWN);
        return IGNORE;
      case jarvis2::BoxAction::Select:
        EnqueueKey(KEY_ENTER);
        return IGNORE;
      case jarvis2::BoxAction::Delegate:
        return ScreenRecoveryUI::CheckKey(key, held);
    }
    return IGNORE;
  }

 protected:
  std::unique_ptr<Menu> CreateMenu(const std::vector<std::string>& headers,
                                   const std::vector<std::string>& items,
                                   size_t selection) const override {
    lcars_menu_ = nullptr;
    if (items.empty()) {
      return ScreenRecoveryUI::CreateMenu(headers, items, selection);
    }
    auto menu = std::make_unique<StockLcarsMenu>(headers, items, selection, *this, ScreenWidth(),
                                                ScreenHeight(), char_width_, char_height_);
    if (menu->Geometry().tiles.empty()) {
      return ScreenRecoveryUI::CreateMenu(headers, items, selection);
    }
    lcars_menu_ = menu.get();
    return menu;
  }

  std::unique_ptr<Menu> CreateMenu(const GRSurface* header,
                                   const std::vector<const GRSurface*>& graphics,
                                   const std::vector<std::string>& text_headers,
                                   const std::vector<std::string>& items,
                                   size_t selection) const override {
    lcars_menu_ = nullptr;
    return ScreenRecoveryUI::CreateMenu(header, graphics, text_headers, items, selection);
  }

  void draw_menu_and_text_buffer_locked(const std::vector<std::string>& help) override {
    if (!lcars_menu_ || menu_.get() != lcars_menu_) {
      ScreenRecoveryUI::draw_menu_and_text_buffer_locked(help);
      return;
    }
    gr_color(11, 14, 20, 255);
    DrawFill(0, 0, ScreenWidth(), ScreenHeight());
    lcars_menu_->DrawHeader(0, 0);
    lcars_menu_->DrawItems(0, 0, ScreenWidth(), IsLongPress());
  }

 private:
  mutable const StockLcarsMenu* lcars_menu_ = nullptr;
};

class StockActionDevice final : public Device {
 public:
  explicit StockActionDevice(Device* stock) : Device(new StockLcarsUI), stock_(stock) {}

  void PreRecovery() override {
    CopyBootState();
    stock_->PreRecovery();
  }
  void StartRecovery() override { stock_->StartRecovery(); }
  void PreFastboot() override {
    CopyBootState();
    stock_->PreFastboot();
  }
  void StartFastboot() override { stock_->StartFastboot(); }

  int HandleMenuKey(int key, bool visible) override { return stock_->HandleMenuKey(key, visible); }
  const std::vector<std::string>& GetMenuItems() override { return stock_->GetMenuItems(); }
  BuiltinAction InvokeMenuItem(size_t position) override { return stock_->InvokeMenuItem(position); }
  void RemoveMenuItemForAction(BuiltinAction action) override {
    stock_->RemoveMenuItemForAction(action);
  }
  bool PreWipeData() override { return stock_->PreWipeData(); }
  bool PostWipeData() override { return stock_->PostWipeData(); }

 private:
  void CopyBootState() {
    boot_state_.emplace(GetReason().value_or(""), GetStage().value_or(""));
    stock_->SetBootState(&*boot_state_);
  }

  std::optional<BootState> boot_state_;
  const std::unique_ptr<Device> stock_;
};

}  // namespace

extern "C" __attribute__((visibility("default"))) Device* make_device() {
  constexpr const char* kFactoryLibrary = "/system/lib/librecovery_ui_onn_stock.so";
  void* handle = dlopen(kFactoryLibrary, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "Cannot load stock Recovery UI: %s\n", dlerror());
    return new Device(new ScreenRecoveryUI);
  }
  using MakeDevice = Device* (*)();
  auto factory = reinterpret_cast<MakeDevice>(dlsym(handle, "make_device"));
  if (!factory) {
    fprintf(stderr, "Cannot resolve stock Recovery factory: %s\n", dlerror());
    return new Device(new ScreenRecoveryUI);
  }
  Device* device = factory();
  if (!device) {
    fprintf(stderr, "Stock Recovery factory returned no device\n");
    return new Device(new ScreenRecoveryUI);
  }
  // Vendor GetUI uses a separate member. Own the vendor device without changing its UI.
  return new StockActionDevice(device);
}
