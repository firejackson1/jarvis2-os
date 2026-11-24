# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_minimal.mk)
# Lineage's media product puts this SDK jar on the system-server classpath.
# Install its matching packages so the product's dexpreopt graph is complete.
include vendor/lineage/config/lineage_sdk_common.mk
PRODUCT_NAME := lineage_jarvis2_recovery
PRODUCT_DEVICE := jarvis2_recovery
PRODUCT_BRAND := onn
PRODUCT_MODEL := Jarvis2 Recovery Prototype
PRODUCT_MANUFACTURER := onn
PRODUCT_CHARACTERISTICS := tv
PRODUCT_PACKAGES += recovery
PRODUCT_BUILD_BOOT_IMAGE := false
PRODUCT_BUILD_INIT_BOOT_IMAGE := false
# Enable vendor_boot resource rules; build only the explicit recovery ramdisk target.
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := true
PRODUCT_BUILD_USERDATA_IMAGE := false

# Keep upstream recovery ADB policy: no owner keys, no blanket permissive policy.
# The deliverable is ramdisk-recovery.img, not a complete vendor_boot or ROM.
