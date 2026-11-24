# SPDX-License-Identifier: Apache-2.0
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := Jarvis2LtvLauncher
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_SRC_FILES := prebuilts/LTvLauncher.apk
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_LICENSE_KINDS := SPDX-license-identifier-GPL-3.0-only
LOCAL_LICENSE_CONDITIONS := reciprocal
LOCAL_NOTICE_FILE := $(LOCAL_PATH)/prebuilts/LICENSE.txt $(LOCAL_PATH)/prebuilts/NOTICES.txt
LOCAL_PRODUCT_MODULE := true
LOCAL_MODULE_TAGS := optional
LOCAL_MULTILIB := 32
LOCAL_DEX_PREOPT := false
LOCAL_OPTIONAL_USES_LIBRARIES := androidx.window.extensions androidx.window.sidecar
# Mandatory release launcher also excludes the unsupported official OTA client.
LOCAL_OVERRIDES_PACKAGES := TVLauncherNoGMS TVRecommendationsNoGMS Updater
# Preserve the pinned controlled-build APK bytes/signature. prepare-launcher.py independently checks
# hash, signer, ZIP alignment and ARM32 JNI libraries before staging these inputs.
LOCAL_REPLACE_PREBUILT_APK_INSTALLED := $(LOCAL_PATH)/prebuilts/LTvLauncher.apk
# Standard APK-local JNI install handling, not raw ELF PRODUCT_COPY_FILES.
LOCAL_PREBUILT_JNI_LIBS := \
    prebuilts/libapp.so \
    prebuilts/libflutter.so \
    prebuilts/libsqlite3.so
include $(BUILD_PREBUILT)
