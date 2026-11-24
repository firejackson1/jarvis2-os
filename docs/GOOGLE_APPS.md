# Optional Google apps — private installation evidence

Google apps are not included in this source repository or the unsigned raw-image
archive. Personal installation does not establish redistribution permission for
a public ROM bundle. Account sign-in and Google device certification are separate
from boot and package installation tests.

## Package tested

The private ARM32 Android 14 TV test used the upstream
[MindTheGapps ARM ATV release](https://github.com/MindTheGapps/14.0.0-arm-ATV/releases/tag/MindTheGapps-14.0.0-arm-ATV-20240523_192108),
minimal archive `MindTheGapps-14.0.0-arm-ATV-minimal-20240523_192108.zip`.
SHA-256: `e36bc0dbbf8e0b592cd09ed52893712819616398307045dd5cf6fb8dfb62a652`.
Its package metadata specifies ARM/API 34; all APK native libraries are ARMv7.
The minimal package does not replace LTv with Google's TV launcher.

## EROFS and upgrade limits

The upstream recovery installer expects writable system/product/system_ext
filesystems. Our images use read-only EROFS, so ordinary sideload of this package
is not a supported installation route. Do not interpret this document as a
generic flash procedure.

For the owner's authorized test, rebuilt copies of the exact tested ROM images
contained only expected Google additions. A full extracted comparison found no
changes to existing file content, ownership or modes; added APK signatures passed.
All three images fit the existing A partition sizes with AVB overhead. Signed
vbmeta files preserved the accepted root key, flags and rollback indices, and
the full offline chain audit passed.

Recovery used temporary device-mapper tables for already allocated A extents,
without invoking fastboot's LP metadata writer. All five written A images matched
full readback hashes. The complete captured super metadata prefix and protected
A/B boot/recovery hashes remained unchanged. This is evidence for this specific
layout, not a general installer or proof that B is bootable.

Android completed boot on A with SELinux enforcing and userdata retained. Google
Play services, Play Store and Services Framework resolved to their system image
paths. Play Store launched and the Google sign-in screen rendered. Account login,
downloads, certification, Cast and voice operation remain unverified.

An existing provisioned user did not automatically receive all newly installed
Google TV Bluetooth defaults. The remote and firmware-update services crashed
without BLUETOOTH_CONNECT. Applied only requested Bluetooth grants listed in the
upstream default-permissions XML; no location grant or account setup was automated.
Fresh-user/default-permission behavior needs separate testing.
