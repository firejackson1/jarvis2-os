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

The exact upstream download, byte length and checksum are machine-readable in
`manifests/gapps-input.json`. Obtain the ZIP directly from that upstream URL and
verify its SHA-256 before using it. A checksum establishes exact bytes, not a
redistribution grant or compatibility with an arbitrary ROM.

## Public delivery gate

The pinned upstream [license](https://gitlab.com/MindTheGapps/vendor_gapps_tv/-/raw/40b7bab4cd0afd8fe38d6dfc7e71cc3ae12d0514/LICENSE)
excludes proprietary APK inputs from the maintainer's GPL grant and refers their
licensing to their authors. No affirmative grant to mirror those Google APKs has
been established. Preserve access to the exact ZIP through its upstream download
link; keep our local copy and GApps-integrated images private pending permission.
LineageOS likewise documents Google apps as proprietary and separately obtained.
The installer scripts' license does not license the complete binary ZIP.

Separate delivery also needs an EROFS-compatible, verified composition/install
procedure against the published base ROM and its AVB chain. The successful
private repack is evidence for that candidate, not support for arbitrary sideload.

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
paths. Play Store launched and the Google sign-in screen rendered. Account login
and Play Store downloads were subsequently verified; certification, Cast, voice
and media playback remain unverified.

An existing provisioned user did not automatically receive all newly installed
Google TV Bluetooth defaults. The remote and firmware-update services crashed
without BLUETOOTH_CONNECT. Applied only requested Bluetooth grants listed in the
upstream default-permissions XML; no location grant or account setup was automated.
Fresh-user/default-permission behavior needs separate testing.

## Landscape feature correction

Play Store initially marked both VLC and YouTube for Android TV incompatible.
The device declared Leanback but omitted `android.hardware.screen.landscape`.
VideoLAN's official ARMv7 APK explicitly reports an implied landscape requirement
because its manifest contains landscape activities. Android's
[Play filtering documentation](https://developer.android.com/google/play/filters)
describes feature-based filtering.

Added the actual landscape capability to the device permission XML. A regression
fails with the old declaration and passes with the correction. A RAM test made
the feature visible to PackageManager; a successful Google device check-in and
reset of Play Store's local data refreshed the server/catalog view. The Google
account was retained. Both apps then installed directly from Play Store with
ARMv7 splits, demonstrating that these rejections were not an ARM32 limitation.

The persistent private A patch changed only system_a and vbmeta_system_a. Exact
readback hashes, unchanged captured super metadata and protected A/B boot/recovery
hashes passed. After reboot, PackageManager reported landscape support without a
RAM bind mount, SELinux was enforcing, and both Play-installed apps launched.
Userdata was not wiped and the temporary stay-awake setting was restored.
This does not establish compatibility with ARM64-only apps or Google certification.
