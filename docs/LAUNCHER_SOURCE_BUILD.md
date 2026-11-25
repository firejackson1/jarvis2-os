# LTvLauncher controlled source candidate

This source set identifies the controlled ARMv7 candidate built from LTvLauncher
`f9db652edaac2da3ea2e6a1ed220d1396ccea82b`, version `2026.11.23`, code `8117`.
The original 298 application source files were unchanged. This candidate uses
the canonical neutral workspace `/build/jarvis2-launcher` to prevent embedding
private owner/build paths in Dart generated-plugin source URIs. The resulting
URI is `file:///build/jarvis2-launcher/app/.dart_tool/flutter_build/dart_plugin_registrant.dart`.
This is a source/build environment fix, with no binary patching. Every one of
the 590 APK entries matches the previous controlled candidate except libapp.so;
the actual 93-component/78-artifact runtime graph, original dependency locks and
strict verification metadata remain unchanged. The unsigned candidate
SHA256 is `8d68a7b83a56a5759ef3bf9a06b026e6b153795ad2fb9c1750bd75b36c102e25`.
The separately signed project candidate SHA256 is
`ac585d5a0bb3c13c2ea346d052d1fa5140a6bb35bbe90a20002f776f92c03347`.
The signing key is not distributed. This document does not change a ROM artifact
pin or authorize installation on hardware.

## Source layout and verification

`SOURCE-BUNDLE.json` is the exact file whitelist, SHA256/size map and upstream
source URL index. Verify every file against it before extracting nested archives. A few exact
upstream source archives have relative test symlinks to sibling checkouts; the
manifest explicitly records each such external source link. They remain inert
metadata inside the bundled archive. Extract source archives only into a fresh
isolated source workspace using a safe extractor that rejects traversal and
external links, or provision the expected upstream sibling layout after review.
Do not blindly follow links or extract over existing files.
Sources remain byte-for-byte upstream archives, preserving copyright, license,
NOTICE and build files. `sources/application/` contains the original application;
`sources/flutter/` the framework and generated sky_engine package (five SDK
packages in total); `sources/pub/` all 137 locked hosted packages;
`sources/maven/` the selected published source jars, POMs and module metadata;
`sources/native/` the 43 pinned engine/Dart/Skia/native/header source archives;
`sources/supplements/` the SQLite recipe/amalgamation and protobuf/AndroidX recipe.
`sources/assets/material-icons/` supplies the exact Material Icons font,
codepoints and its upstream CC BY 4.0 license. Its provenance identifies the
official Flutter font ZIP/member, not framework Git. Copyright 2019 Google LLC.
All Rights Reserved. The original font is unchanged here; Flutter icon tree
shaking subsets it in the APK. Attribution and the CC BY 4.0 link are retained
in cumulative notices and `catalogs/material-icons-provenance.json`.
The native set is a source/header/build-input superset. Optional platform, test
and tool targets are not all asserted to ship.

`catalogs/selected-source-coverage-summary.json` explains all 74 selected Maven
coordinates/78 external artifacts: 69 source-bearing published jars, two
zero-class compatibility placeholders, native SQLite, native Flutter, and the
AndroidX relocated protobuf supplement. Empty source classifiers are retained
as evidence and are not substituted for the supplemental actual source.
The AndroidX 1.1.3 release recipe pins protobuf 4.28.2 and its namespace
relocation. The supplied sources rebuild the exact published binary with the
[relocation recipe below](#reproducing-the-datastore-protobuf-jar). SQLite 3.50.3
source and the exact native build recipe are supplied separately.

`build-records/` contains sanitized actual dependency locks, strict verification
metadata, runtime graph/artifact hashes, generated test sources and R8 records.
Absolute build/cache locations in text records are replaced with generic
variables; raw private logs are excluded. These records describe the controlled
build, not an upstream signed build attestation. No byte-identical rebuild of the
original third-party APK is claimed or required to identify these source inputs.

`notices/` delivers the actual Flutter APK notices, retained APK notice files,
selected Maven copyright/license statements and supplemental license texts.
Per-file source headers and upstream license/NOTICE files remain in each source
archive. These notices must accompany redistribution; do not discard source
copyright/license files when modifying or repackaging. This archive assembly is
not a claim of complete legal clearance for an entire ROM.

## Reproducing the ARMv7 SQLite library

Extract the pinned recipe and SQLite amalgamation from
`sources/supplements/` into one fresh directory. Verify both archive hashes
against the source-bundle manifest first. The Maven library's Android ELF
note identifies NDK r27c and API 21. Use that NDK, CMake 3.31.6 and Ninja
1.12.1. [Android NDK r27c and download checksums](https://github.com/android/ndk/releases/tag/r27c)

Set `source_root` to the absolute extraction directory, `out` to a fresh
absolute build directory, and `ndk` to the r27c installation.

~~~sh
recipe="$source_root/sqlite-native-libraries-91884ccbe1f58edca999d94aa3b8bef33f176ddf"
amalgamation="$source_root/sqlite-autoconf-3500300"
flags="-O2 -g -DNDEBUG -fdebug-prefix-map=$source_root=/sqlite-source -fdebug-prefix-map=$out=/sqlite-build"
LC_ALL=C TZ=UTC cmake -G Ninja -S "$recipe/sqlite3-native-library/cpp" -B "$out" \
  -DCMAKE_TOOLCHAIN_FILE="$ndk/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=armeabi-v7a -DANDROID_PLATFORM=android-21 \
  -DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_C_FLAGS_RELWITHDEBINFO="$flags" \
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DFETCHCONTENT_SOURCE_DIR_SQLITE3="$amalgamation"
LC_ALL=C TZ=UTC cmake --build "$out" --target sqlite3 --parallel 1
"$ndk/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" --strip-unneeded \
  -o "$out/libsqlite3.stripped.so" "$out/libsqlite3.so"
~~~

Both path-normalized builds produced the same stripped SHA-256,
`3e8cdd54efd4ff6fa267f43a07af2087279593bea0c077c87bfcf2ea7fa98aaa`.
The shipped library copies in Maven, the r2 APK and its extracted JNI
directory are identical. All four local builds match those shipped bytes
outside the 20-byte GNU build-ID descriptor. The original Maven build ID
differs. [SQLite replay receipt](../manifests/launcher-sqlite-rebuild.json)

## Reproducing the DataStore protobuf JAR

Verify `sources/maven/protobuf-javalite-4.28.2-sources.jar` from the staged
source companion. Set `PROTOBUF_SOURCES` to the absolute path to that file,
`PROTOBUF_JAVAC` to the Temurin **11.0.25+9** `javac`, and `GRADLE` to the
Gradle **8.7-rc-1** executable. Run Gradle itself with OpenJDK **21.0.13.1**.
The release's wrapper identifies that Gradle distribution, and the AndroidX
recipe uses Shadow **8.1.1**. [AndroidX release recipe](https://android.googlesource.com/platform/frameworks/support/+/ae63f655454c1548483e3f34d8f47d98ae21119b/datastore/datastore-preferences-external-protobuf/build.gradle)

In a fresh directory, put the pinned
[Gradle dependency checksums](../manifests/launcher-protobuf-gradle-verification.xml)
at `gradle/verification-metadata.xml`. Save the following as `settings.gradle`:

```groovy
pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}
rootProject.name = 'protobuf-relocation-replay'
```

Save this as `build.gradle`:

```groovy
plugins {
    id 'java-library'
    id 'com.github.johnrengelman.shadow' version '8.1.1'
}

configurations {
    protobufInput
}

dependencies {
    protobufInput files('protobuf-input.jar')
}

tasks.register('replay', com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar) {
    from(sourceSets.main.output)
    configurations = [project.configurations.protobufInput]
    relocate 'com.google.protobuf', 'androidx.datastore.preferences.protobuf'
    archiveFileName = 'protobuf-relocated.jar'
    destinationDirectory = layout.buildDirectory.dir('relocated')
    exclude '**/*.proto', '**/*.proto.bin'
    preserveFileTimestamps = false
    reproducibleFileOrder = true
    manifest.attributes('Manifest-Version': '1.0')
}
```

Compile and relocate the classes:

```sh
set -eu
export LC_ALL=C TZ=UTC
printf '%s  %s\n' 2460a92938259e4441826e57638193d0bde9cb5cdd0dafd5367aacb833f9a971 \
  "$PROTOBUF_SOURCES" | sha256sum -c
mkdir source classes
(
  cd source
  jar xf "$PROTOBUF_SOURCES"
  find com -name '*.java' -print | sort > ../sources.args
  "$PROTOBUF_JAVAC" -J-Xmx384m -source 8 -target 8 -g -parameters \
    -d ../classes @../sources.args
)
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

classes = Path('classes')
with ZipFile('protobuf-input.jar', 'x') as archive:
    for path in sorted(classes.rglob('*.class')):
        archive.writestr(path.relative_to(classes).as_posix(), path.read_bytes())
PY
"$GRADLE" -Dorg.gradle.jvmargs=-Xmx512m --no-daemon --max-workers=1 \
  --console=plain --offline replay
printf '%s  %s\n' fcb3f373cf743426c85ebb0d3cc644aefaf26f39b7fa55bb90238d41b689eca7 \
  build/relocated/protobuf-relocated.jar | sha256sum -c
```

Use a cache populated from the official Gradle Plugin Portal and Maven Central.
Gradle may need an initial online run with the same strict verification metadata
to populate an empty cache. The verified offline replay compiled 159 source files
to 523 classes. The complete 529-member output matched the Google Maven JAR and
the launcher dependency lock. Separately, the same relocation of the pinned Maven
`protobuf-javalite` binary reproduced the same output. [Rebuild receipt](../manifests/launcher-protobuf-rebuild.json)

## Recipient tools

Use your own Linux x86-64 machine and the canonical neutral directory
`/build/jarvis2-launcher`, with Java 21 (the controlled build used
Android_PDK OpenJDK 21.0.1), Gradle 8.13, and Flutter **3.24.5**, framework commit
`dec2ee5c1f98f8e84a7d5380c05eb8a3d0a81668`, engine
`a18df97ca57a249df5d8d68cd0820600223ce262`, Dart 3.5.4 source revision
`88c9758ef131d430d8ce595c6bfb4c90574d3ddd`.
Obtain tools from their official distributions or provision the exact framework
Git checkout and engine assets. The Flutter checkout must have the official
3.24.5 tag/revision metadata so Flutter reports 3.24.5, not an unknown version.
Framework source is supplied; a runnable Flutter SDK additionally needs official
Dart/engine/gen_snapshot/font/tool artifacts. This bundle contains source, not
those executable SDK/tool distributions.

Obtain Android SDK command-line tools and platforms 31/34/35, build-tools 34/35,
and platform-tools through Google's supported SDK setup. The controlled build
used cmdline-tools 13.0 and platform-tools 37.0.3. Read the applicable SDK terms
and decide whether to accept them yourself. No acceptance records or automatic
license-acceptance command are supplied. Source redistribution does not grant
rights to redistribute Google's SDK archives. Host SQLite 3.46.1 was used by
Drift schema generation. The app's shipped native SQLite remains 3.50.3.

Install or copy the tools and caches into actual directories below that neutral
root. Avoid symlinks that resolve into an owner home or private host path. Start
from a fresh application source directory; regenerate package configurations,
Flutter plugin metadata, codegen and build outputs there. Do not copy old
`.dart_tool`, `.gradle`, local.properties or build outputs into the app. The
canonical neutral prefix matters: Dart can retain the generated plugin
registrant source URI in libapp.so even in a release build. Set:

```sh
export JAVA_HOME=/build/jarvis2-launcher/jdk21
export FLUTTER_ROOT=/build/jarvis2-launcher/flutter
export ANDROID_HOME=/build/jarvis2-launcher/android-sdk
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PUB_CACHE=/build/jarvis2-launcher/pub-cache
export GRADLE_USER_HOME=/build/jarvis2-launcher/gradle-cache
export PATH="$JAVA_HOME/bin:$FLUTTER_ROOT/bin:/build/jarvis2-launcher/gradle-8.13/bin:$PATH"
export CI=true FLUTTER_SUPPRESS_ANALYTICS=true DART_SUPPRESS_ANALYTICS=true
flutter --version
flutter precache --android
```

Flutter tooling bootstrap and Maven/tool resolution may need network access.
Use the pinned SDK and retained verification metadata; do not disable dependency
verification or silently upgrade application locks. Missing host-specific tool
checksums must be checked against primary upstream artifacts before narrowly
adding entries. Flutter's tool-only package dependencies are described by the
pinned framework's own lockfile; the 137 bundled hosted packages are the
application's locked source set, not every executable tool dependency.

## Application and generator commands

Extract `sources/application/LTvLauncher-source.tar.gz` into a fresh directory,
then move its `LtvLauncher-f9db652edaac2da3ea2e6a1ed220d1396ccea82b` directory to
**`/build/jarvis2-launcher/app`** and enter that directory. Do not compile it
under your owner-specific home or private host workspace.
To hydrate the application pub cache without changing dependency versions, use
the bundled `catalogs/dependency-source-index.json`: for each hosted entry,
verify its archive SHA256, extract the matching `sources/pub/<file>` into
`$PUB_CACHE/hosted/pub.dev/<name>-<version>`, and write its 64-character SHA256
**without a newline** to
`$PUB_CACHE/hosted-hashes/pub.dev/<name>-<version>.sha256`.
Do not merge arbitrary caches or overwrite versions from a different lock.
Standard `dart pub get` can alternatively download these exact locked versions;
compare the resulting original pubspec.lock before continuing.

Copy `build-records/gradle/gradle.lockfile` to `android/app/gradle.lockfile` and
`build-records/gradle/verification-metadata.xml` to
`android/gradle/verification-metadata.xml`. Keep the original app Gradle files
and pubspec.lock unchanged. The original source archive omits gradlew and its
wrapper jar. Flutter's normal project setup generates the standard wrapper
files while retaining the original Gradle 8.13 distribution URL. Provision the
Gradle 8.13 binary distribution in your own wrapper cache if working offline.
The official Gradle 8.13 binary ZIP SHA256 is
`20f1b1176237254a6fc204d8434196fa11a4cfb387567519c61556e8710aed78`.

First explicitly run Flutter's offline package/platform preparation. This
refreshes the native plugin lists required by Android settings.gradle. Plain
Dart pub get alone does not create them: omitting this step can yield a
successful APK missing native plugins, including SQLite. The verified metadata
contains eight Android plugins and all plugin paths use the neutral root.
Then run explicit offline Dart resolution and the pinned generators directly. This avoids Flutter pub-run implicitly fetching
because of a synthetic flutter_gen mapping with no generated pubspec:

```sh
DART="$FLUTTER_ROOT/bin/cache/dart-sdk/bin/dart"
flutter --no-version-check --suppress-analytics pub get --offline --no-precompile
test -s .flutter-plugins-dependencies
test -s .flutter-plugins
"$DART" pub get --offline --no-precompile
"$DART" --packages=.dart_tool/package_config.json \
  "$PUB_CACHE/hosted/pub.dev/build_runner-2.4.13/bin/build_runner.dart" \
  build --delete-conflicting-outputs
"$DART" --packages=.dart_tool/package_config.json \
  "$PUB_CACHE/hosted/pub.dev/drift_dev-2.19.1/bin/drift_dev.dart" \
  schema generate drift_schemas/ test/generated_migrations/
```

Retained source changes from generation are eight added test/migration files,
provided in `build-records/generated-codegen-source.tar.gz`. No original source
file was modified. Compare regeneration with that archive; generated paths and
local.properties are environment-specific and are not application source edits.

## ARMv7 Flutter engine and Dart AOT

The packaged `libflutter.so` matches the official Flutter Maven artifact
for engine `a18df97ca57a249df5d8d68cd0820600223ce262`. The Maven JAR and
the Linux x86-64 `gen_snapshot` binary also match the original build cache.
Both the APK members and the extracted JNI files in r2 have those same
hashes. [Flutter binary and AOT receipt](../manifests/launcher-flutter-aot-replay.json)

The saved Flutter kernel compiler record names 1,588 Dart inputs. The
launcher companion contains 1,587 matching files from the application,
Flutter framework and pinned Pub source archives. The generated plug-in
registrant also matches its saved cache hash. All 1,588 file-cache hashes
were replayed with the pinned Flutter implementation.

A fresh workspace unpacked the application, Flutter framework source,
`sky_engine` and all 137 locked Pub source archives from the companion.
The Flutter SDK already had its own tool cache, including 69 additional
host-tool packages. Every application package resolved at its locked
version offline, and Flutter regenerated the plug-in registrant byte
for byte. The new package configuration also includes the generated
`flutter_gen` entry. The compiler read the same 1,588 files and did not use
that additional entry. [Source-to-kernel receipt](../manifests/launcher-flutter-frontend-rebuild.json)

With the tools and source in the canonical workspace described above,
run the kernel target in the fresh application directory.

~~~sh
flutter --no-version-check --suppress-analytics pub get \
  --offline --enforce-lockfile --no-precompile
flutter --no-version-check --suppress-analytics assemble --output="$output_dir" \
  -dTargetPlatform=android -dAndroidArchs=android-arm -dBuildMode=release \
  -dTargetFile=lib/main.dart -dTrackWidgetCreation=false kernel_snapshot
~~~

Find `program.dill` under the new `.dart_tool/flutter_build` directory.
It matches the saved `app.dill` at the SHA-256 in the receipt.

To replay the AOT step, provide the ARM release `gen_snapshot` binary
from the receipt and the `app.dill` intermediate emitted by Flutter.
Use a fresh `output_dir` for each run.

~~~sh
"$gen_snapshot" --deterministic --snapshot_kind=app-aot-elf \
  --elf="$output_dir/libapp.so" --strip \
  --no-sim-use-hardfp --no-use-integer-division "$app_dill"
~~~

Two offline runs against the saved kernel and a third run against the
newly generated kernel reproduced the exact `libapp.so` from the unsigned
and signed launcher APKs. The r2 product image carries those same bytes.
A native Flutter engine rebuild remains open.
[Pinned Flutter AOT command construction](https://github.com/flutter/flutter/blob/dec2ee5c1f98f8e84a7d5380c05eb8a3d0a81668/packages/flutter_tools/lib/src/base/build.dart)

## Unsigned ARMv7 release and recipient signing

Use an isolated environment without existing signing configuration. Set
`KEYSTORE_FILE` to a path that does not exist; do not point it at a project key.
For a bounded build, write a private Gradle user properties file:

```properties
org.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=768m
org.gradle.workers.max=2
org.gradle.daemon=false
kotlin.compiler.execution.strategy=in-process
android.builder.sdkDownload=false
```

Then run the actual controlled APK command:

```sh
export KEYSTORE_FILE="$PWD/recipient-unsigned-no-keystore"
test ! -e "$KEYSTORE_FILE"
flutter --no-version-check --suppress-analytics build apk \
  --release --target-platform=android-arm --split-per-abi \
  --build-name=2026.11.23 --build-number=8117 --no-pub
```

The controlled build used an 8 GiB memory / 2 GiB swap / four-CPU process-tree
limit and completed with a 2.8 GiB peak. Expected output is
`build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk`. Inspect package,
version, ARMv7 ABI, signature absence and 16 KiB alignment with your SDK tools.
Verify that libapp.so, libflutter.so and libsqlite3.so are all present and
compare the selected runtime artifact hashes with the retained graph. Scan all
decompressed APK entries, native files and inflated Flutter NOTICES for your
private workspace/home prefixes, including UTF-16 forms. The controlled neutral
candidate passed this scan across all 590 entries. Its only native file URI is
the generic neutral registrant URI shown above; no private prefix was retained.
Exact byte identity can vary with build metadata; retained R8 records and
selected-artifact hashes make the actual produced candidate inspectable.

For installation in your own unlocked developer-preview ROM, align and sign
your APK using **your own** signing key and the supported Android build-tools.
Do not reuse or request the project's private signing key. Set the launcher APK
hash and signing-certificate pin in your own ROM input manifest to the resulting
artifact/certificate, then rebuild the ROM through its documented workflow.
A differently signed APK cannot update the installed package in place under the
original certificate. Review the ROM's installation, recovery, launcher HOME
selection and rollback instructions for your own device before installing;
this source recipe performs no flashing, rebooting, slot switching or data wipe.

## Reassembling the source delivery

The repository's `tools/assemble-launcher-sources.py` uses only the explicit
`manifests/launcher-source-bundle.json` whitelist. Supply named input roots of
your choosing; root names are logical, not fixed private paths:

```sh
python3 tools/assemble-launcher-sources.py \
  --manifest manifests/launcher-source-bundle.json \
  --root inputs=/your/verified-launcher-inputs \
  --root closure=/your/verified-source-materials \
  --root staged=/your/sanitized-build-records \
  --root repository="$PWD" --output /your/fresh/launcher-sources.tar.gz
```

Source URLs and SHA256 values in the manifest identify externally obtained
inputs. Sanitized staged build records are supplied by this source bundle,
not inferred from upstream POMs. Reassemble twice to different fresh paths and
compare SHA256. The assembler does not download, execute or recursively include
unlisted inputs. It rejects changed hashes/sizes, duplicate destinations, unsafe
paths and unsafe nested archive members, and normalizes outer archive metadata.
