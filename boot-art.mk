# SPDX-License-Identifier: Apache-2.0
# Optional owner-provided artwork, validated by tools/prepare-boot-animation.py.
# No artwork binaries are distributed in this source repository.
ifneq ($(wildcard device/onn/jarvis2/prebuilts/bootanimation.zip),)
TARGET_BOOTANIMATION := device/onn/jarvis2/prebuilts/bootanimation.zip
endif
