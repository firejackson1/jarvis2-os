# SPDX-License-Identifier: Apache-2.0
# Recovery-only bring-up. Do not use this tree to generate a normal Android boot.
DEVICE_PATH := device/onn/jarvis2_recovery
TARGET_BOOTLOADER_BOARD_NAME := jarvis2
TARGET_NO_BOOTLOADER := true
TARGET_NO_KERNEL := true
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_VARIANT := generic
TARGET_IS_64_BIT_KERNEL := true

BOARD_BOOT_HEADER_VERSION := 4
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := true
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := true
BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true
BOARD_RAMDISK_USE_LZ4 := true
TARGET_RECOVERY_UI_LIB := librecovery_ui_jarvis2
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery/recovery.fstab

# Existing hardware budget; packaging still preserves the stock container.
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 67108864
