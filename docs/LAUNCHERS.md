# Launcher choices and release inputs

The working development device offers Android TV Home, LTvLauncher, FLauncher and
Bridge Console TV. The public preview must not redistribute Google's TVLauncher-
NoGMS or TVRecommendationsNoGMS without an established license grant. The Apache
header on their prebuilt makefile does not establish a license for their APKs.

LTvLauncher is selected as the open-source bundled candidate, pending clean-boot
and Home-role/default selection tests. FLauncher and Bridge remain optional
choices when installed. This does not change the owner's running default.

## Pinned LTv inputs

- Release v2026.11.23, package com.leanbitlab.ltvL, ARMv7 APK.
- Source commit f9db652edaac2da3ea2e6a1ed220d1396ccea82b, GPLv3.
- Build workflow: Flutter3.24.5, Java21, Android SDK35; pub get, build_runner,
  drift schema generation, then split-per-ABI Android APK build.
- Exact APK/source download hashes and upstream signer are recorded in
  manifests/launcher-inputs.json. The input preparation tool checks these and
  ZIP alignment before staging anything.

```sh
python3 tools/prepare-launcher.py /outside/repo/launcher-materials /path/to/android --download
```

The tool copies only verified build inputs under ignored apps/Launcher/prebuilts.
It never installs or flashes. Upstream APK/native files are not in Git. All three
ARM32 native libraries are extracted beside the system APK in lib/arm. This
preserves the upstream signature and allows a bundled app to find its libraries.
The standard Android Make prebuilt replacement path preserves APK bytes and
installs the verified JNI libraries through LOCAL_PREBUILT_JNI_LIBS. This avoids
rewriting compressed native payloads inside an upstream-signed APK. Independent
hash, signature, ABI and ZIP alignment checks run before inputs are staged.

## GPL/source release materials

Provide equivalent access to the exact source archive, GPL text, dependency
notices, locked dependencies and build/install instructions alongside any ROM
containing the APK. Preserve upstream NOTICES.Z inside the unchanged APK and
include accessible extracted notices. Audit dependency corresponding-source
requirements; a source tarball alone is not automatic compliance for everything
embedded in an APK. These materials are collected outside Git for release assets.
Use a recipient's own signing key for modified builds; installation/replacement
must remain possible on the unlocked developer-preview target. The original
upstream private signing key is not distributed or required for a modified build.

FLauncher0.18.0 source pin4930cd738a5ab32967953fe8b12790bc4b452872 uses Flutter3.7.5
and a Firebase-dependent build configuration. If later bundled, its corresponding
source/configuration/signing and dependency obligations need their own review.
Bridge Console TV is owner-controlled; audit development dependencies and retain
its Antonio font OFL and third-party notices before bundling. Neither optional
APK is silently downloaded by the ROM at boot.
