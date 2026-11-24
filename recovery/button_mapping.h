// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <linux/input.h>

namespace jarvis2 {
enum class BoxAction { Delegate, Reveal, Next, Select };

constexpr BoxAction BoxButton(int key, bool held, bool visible) {
  if (key != KEY_POWER) return BoxAction::Delegate;
  if (!visible) return BoxAction::Reveal;
  return held ? BoxAction::Select : BoxAction::Next;
}
}  // namespace jarvis2
