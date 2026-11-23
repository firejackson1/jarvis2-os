#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
python3 -m unittest discover -s tests -v
python3 tools/release_audit.py
classes=$(mktemp -d)
trap 'rm -rf "$classes"' EXIT HUP INT TERM
files=''
for name in AirPodsInfo ResumeState WearState SyncMath HdmiCaps ButtonGesture VoiceServer ReplayFlags; do
 files="$files apps/RemoteSettings/src/app/jarvis2/remote/$name.java apps/RemoteSettings/tests/${name}Test.java"
done
# Paths below are repository-relative and deliberately contain no whitespace.
javac --release 11 -d "$classes" $files
for name in AirPodsInfo ResumeState WearState SyncMath HdmiCaps ButtonGesture VoiceServer ReplayFlags; do
 java -cp "$classes" "app.jarvis2.remote.${name}Test"
done
