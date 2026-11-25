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
- Exact APK/source hashes and project signer are recorded in
  manifests/launcher-inputs.json. The input preparation tool checks these and
  ZIP alignment before staging anything.

```sh
# First supply the pinned controlled APK as LTvLauncher.apk locally.
# --download obtains available upstream source inputs, not an unpublished APK.
python3 tools/prepare-launcher.py /outside/repo/launcher-materials /path/to/android --download
```

The tool copies only verified build inputs under ignored apps/Launcher/prebuilts.
It never installs or flashes. Upstream APK/native files are not in Git. All three
ARM32 native libraries are extracted beside the system APK in lib/arm. This
preserves the controlled APK signature and allows a bundled app to find its libraries.
The standard Android Make prebuilt replacement path preserves APK bytes and
installs the verified JNI libraries through LOCAL_PREBUILT_JNI_LIBS. This avoids
rewriting compressed native payloads inside a signed APK. Independent
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

The Make module identifies the launcher as GPL-3.0-only and includes its upstream
license and expanded dependency notices in Android NOTICE generation. This metadata
applies to the launcher payload; our packaging scripts retain their own licenses.

Source collection has verified all 137 hosted archives against pubspec.lock
checksums outside Git. Five SDK dependencies require the matching Flutter SDK;
Flutter 3.24.5 source commit dec2ee5c1f98f8e84a7d5380c05eb8a3d0a81668
and engine revision a18df97ca57a249df5d8d68cd0820600223ce262 are recorded.
Final corresponding-source assembly and dependency license review remain pending.

To reproduce the hosted dependency collection, install Python's PyYAML package
on the build host and run:

```sh
python3 tools/collect-launcher-sources.py /outside/repo/launcher-materials --download
```

Omit `--download` to verify an existing cache without network access. The helper
first verifies the pinned launcher source archive, then reads its exact lockfile
without unpacking arbitrary paths. It validates hosted package archive checksums
and records SDK dependencies as not collected. The resulting JSON deliberately
does not claim complete corresponding source or completed license review.

The framework archive pin is now also recorded in launcher-inputs.json. If that
verified archive is present, the collector maps flutter, flutter_localizations,
flutter_test and flutter_web_plugins to their actual source package paths.
The exact engine-addressed generated `sky_engine` 0.0.99 ZIP is now pinned in the
same manifest. Place it beside the other verified inputs to map the fifth SDK
package. The collector checks its checksum, revision, package identity, required
license/UI sources and ZIP member safety. The real cached run verifies 137 hosted
archives and all five SDK packages. Generated package availability is separate
from the native Flutter engine's full DEPS closure; all complete-source/license
flags remain false.

The release runtime dependency inventory must also include Android/Maven code,
not just pub archives. Concrete inputs found in plugin build files include
`eu.simonbinder:sqlite3-native-library:3.50.3`, AndroidX DataStore 1.1.3,
Preference 1.2.1, Core 1.13.1, ExifInterface 1.3.7 and Activity 1.9.3. Resolve the
actual transitive runtime graph before assembling source/notices; plugin test or
example dependencies should not be mistaken for shipped code. Verify the native
SQLite build recipe/version for libsqlite3.so separately from its Dart wrapper.

Additional pinned native materials are recorded in
`manifests/launcher-native-materials.json`. The Maven 3.50.3 ARMv7 SQLite library
matches the shipped APK byte-for-byte. Its sources JAR contains only a manifest;
the actual native build recipe and SQLite source archive were collected separately.
The recipe pins NDK 27.2.12479018. Four rebuilds from the staged source
companion match the shipped ARMv7 library outside its 20-byte GNU build ID.
Fixed debug paths also yield an identical rebuilt ELF from fresh directories.
[SQLite build and readback](LAUNCHER_SOURCE_BUILD.md#reproducing-the-armv7-sqlite-library)

## Controlled release input — 2026-11-24

The default APK pin now selects our controlled source build and project signing
certificate, rather than the earlier upstream prebuilt. Until a matching release
asset exists, its URL is deliberately null: provide the verified signed APK
locally as `LTvLauncher.apk`. Preparation fails before any download if it is
missing, even with `--download`; it never substitutes the upstream binary.
See [controlled build instructions](LAUNCHER_SOURCE_BUILD.md) and
`manifests/launcher-source-bundle.json` for the completed 445-file source delivery,
resolved runtime graph, native sources and cumulative notices. Earlier collection
checkpoints above describe their original limited scope, not missing materials
in this controlled source bundle. Recipient-built or differently signed APKs
require an explicitly reviewed pin/certificate update. Switching from the
upstream certificate is a package-signature migration; fresh-data testing and
new-key hardware acceptance remain mandatory release gates.

The running full build was started with the older upstream pin. Its inputs remain
frozen until completion; this source change alone does not put the controlled
launcher into that artifact. A subsequent incremental build and final-image
inspection must establish integration.
