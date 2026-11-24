// SPDX-License-Identifier: Apache-2.0
#include <cassert>
#include <initializer_list>
#include "recovery/button_mapping.h"

int main() {
  using jarvis2::BoxAction;
  using jarvis2::BoxButton;
  assert(BoxButton(KEY_POWER, false, true) == BoxAction::Next);
  assert(BoxButton(KEY_POWER, true, true) == BoxAction::Select);
  assert(BoxButton(KEY_POWER, false, false) == BoxAction::Reveal);
  assert(BoxButton(KEY_POWER, true, false) == BoxAction::Reveal);
  for (int key : {KEY_ENTER, KEY_UP, KEY_DOWN, KEY_BACK, KEY_VOLUMEUP}) {
    assert(BoxButton(key, false, true) == BoxAction::Delegate);
    assert(BoxButton(key, true, true) == BoxAction::Delegate);
  }
}
