// SPDX-License-Identifier: Apache-2.0
#include <recovery_ui/device.h>
#include <recovery_ui/screen_ui.h>
#include "button_mapping.h"

class Jarvis2RecoveryUI final : public ScreenRecoveryUI {
 public:
  KeyAction CheckKey(int key, bool held) override {
    switch (jarvis2::BoxButton(key, held, IsTextVisible())) {
      case jarvis2::BoxAction::Delegate:
        return ScreenRecoveryUI::CheckKey(key, held);
      case jarvis2::BoxAction::Reveal:
        ShowText(true);
        return IGNORE;
      case jarvis2::BoxAction::Next:
        EnqueueKey(KEY_DOWN);
        return IGNORE;
      case jarvis2::BoxAction::Select:
        EnqueueKey(KEY_ENTER);
        return IGNORE;
    }
    return IGNORE;
  }
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

  void StartRecovery() override {
    GetUI()->SetTitle({"Jarvis2 Android 17 Recovery", "OFFLINE PORT - UNTESTED"});
    GetUI()->ShowText(true);
  }

  bool PreWipeData() override { return false; }
};

Device* make_device() { return new Jarvis2RecoveryDevice; }
