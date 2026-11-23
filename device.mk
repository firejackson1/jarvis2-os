# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota.mk)

PRODUCT_SHIPPING_API_LEVEL := 34
PRODUCT_CHARACTERISTICS := tv
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# The prebuilt Android 14 vendor image requires the platform VNDK runtime.
PRODUCT_PACKAGES += com.android.vndk.v34 jarvis2_vndk_manifest

# Enable authenticated USB debugging on a fresh LineageOS install.
PRODUCT_SYSTEM_PROPERTIES += persist.sys.usb.config=mtp,adb


# Android TV launchers use the TV input framework content provider.
PRODUCT_PACKAGES += TvProvider

# The stock audio policy XML selects the configurable engine and its plugin.
PRODUCT_PACKAGES += libaudiopolicyengineconfigurable libparameter \
    libpolicy-subsystem libremote-processor

PRODUCT_COPY_FILES += \
    device/onn/jarvis2/android.software.leanback.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/android.software.leanback.xml

# Use the TV SystemUI from the shared Android TV product.
PRODUCT_PACKAGES += TvSystemUI

# Skip the swipe lock on newly provisioned TV users.
PRODUCT_SYSTEM_PROPERTIES += ro.lockscreen.disable.default=true

# Native remote behavior; F10/F11 interception needs a separate framework fail-safe.
PRODUCT_COPY_FILES += \
    device/onn/jarvis2/keylayout/Vendor_0957_Product_0031.kl:$(TARGET_COPY_OUT_PRODUCT)/usr/keylayout/Vendor_0957_Product_0031.kl
