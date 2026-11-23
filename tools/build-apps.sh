#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Compile only. This script never connects to a device or flashes a partition.
set -eu
if [ "$#" -ne 4 ]; then
 echo 'Usage: build-apps.sh ANDROID_TREE TV_SETTINGS_APK SIGNING_DIRECTORY OUTPUT_DIRECTORY' >&2
 exit 2
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_tree=$(realpath "$1")
target_apk=$(realpath "$2")
keys=$(realpath "$3")
out=$(realpath -m "$4")
case "$out/" in "$root/"*|"$source_tree/"*) echo 'Output must be outside source directories' >&2; exit 2;; esac
if [ -e "$out" ]; then echo 'Output already exists; choose a fresh output directory' >&2; exit 2; fi
jdk="$source_tree/prebuilts/jdk/jdk17/linux-x86/bin"
tools="$source_tree/out/host/linux-x86/bin"
sdk="$source_tree/prebuilts/sdk/34/public/android.jar"
for file in "$target_apk" "$keys/platform.x509.pem" "$keys/platform.pk8" "$sdk"; do
 test -f "$file" || { echo "Missing build input: $file" >&2; exit 2; }
done
mkdir -p "$out/classes" "$out/dex"
"$jdk/javac" --release 11 -cp "$sdk" -d "$out/classes" "$root/apps/RemoteSettings/src/app/jarvis2/remote/"*.java
"$jdk/java" -Xmx256m -cp "$source_tree/prebuilts/r8/r8.jar" com.android.tools.r8.D8 --min-api 28 --lib "$sdk" --output "$out/dex" "$out/classes/app/jarvis2/remote/"*.class
"$tools/aapt2" compile --dir "$root/apps/RemoteSettings/res" -o "$out/app-res.zip"
"$tools/aapt2" link --manifest "$root/apps/RemoteSettings/AndroidManifest.xml" -I "$sdk" -o "$out/app-unsigned.apk" "$out/app-res.zip"
(cd "$out/dex" && zip -q "$out/app-unsigned.apk" classes.dex)
"$tools/aapt2" compile --dir "$root/overlays/TvControls/res" -o "$out/overlay-res.zip"
"$tools/aapt2" link --manifest "$root/overlays/TvControls/AndroidManifest.xml" -I "$sdk" -I "$target_apk" --auto-add-overlay --package-id 0x7e --allow-reserved-package-id -o "$out/overlay-unsigned.apk" "$out/overlay-res.zip"
for part in app overlay; do
 case "$part" in app) name=Jarvis2RemoteSettings;; overlay) name=Jarvis2TvControlsOverlay;; esac
 "$jdk/java" -Djava.library.path="$source_tree/out/host/linux-x86/lib64" -jar "$source_tree/out/host/linux-x86/framework/signapk.jar" "$keys/platform.x509.pem" "$keys/platform.pk8" "$out/$part-unsigned.apk" "$out/$name.apk"
 "$jdk/java" -jar "$source_tree/prebuilts/sdk/tools/linux/lib/apksigner.jar" verify --verbose --print-certs "$out/$name.apk" > "$out/$name.signature.txt"
done
python3 "$root/tools/build-manifest.py" "$root" "$target_apk" "$out"
printf 'Build and signatures verified: %s\n' "$out"
