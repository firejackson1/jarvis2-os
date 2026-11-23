# SPDX-License-Identifier: Apache-2.0
PRODUCT_IS_ATV := true
# Keep the verified stock vendor ramdisk, DTB, and recovery fragment.
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := false

$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)
$(call inherit-product, device/onn/jarvis2/device.mk)
$(call inherit-product, device/onn/jarvis2/tv-controls.mk)
$(call inherit-product, vendor/lineage/config/common_full_tv.mk)
$(call inherit-product, device/onn/jarvis2/apps/Launcher/launcher.mk)

$(call inherit-product, device/onn/jarvis2/boot-art.mk)

PRODUCT_NAME := lineage_jarvis2
PRODUCT_DEVICE := jarvis2
PRODUCT_BRAND := onn
PRODUCT_MODEL := onn 4K Pro Streaming Device
PRODUCT_MANUFACTURER := onn
