# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_minimal.mk)
PRODUCT_NAME := lineage_jarvis2_recovery
PRODUCT_DEVICE := jarvis2_recovery
PRODUCT_BRAND := onn
PRODUCT_MODEL := Jarvis2 Recovery Prototype
PRODUCT_MANUFACTURER := onn
PRODUCT_CHARACTERISTICS := tv
PRODUCT_PACKAGES += recovery
PRODUCT_BUILD_BOOT_IMAGE := false
PRODUCT_BUILD_INIT_BOOT_IMAGE := false
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := false
PRODUCT_BUILD_USERDATA_IMAGE := false

# Keep upstream recovery ADB policy: no owner keys, no blanket permissive policy.
# The deliverable is ramdisk-recovery.img, not a complete vendor_boot or ROM.
