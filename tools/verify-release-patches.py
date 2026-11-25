#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Replay each release patch series in scratch space and verify the build tree."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "Adb": "packages/modules/adb",
    "Bluetooth": "packages/modules/Bluetooth",
    "Music": "packages/apps/Music",
    "ReleaseTools": "build/make",
    "SetupWizard": "packages/apps/SetupWizard",
    "TvSettings": "packages/apps/TvSettings",
}


def git(directory, *args):
    return subprocess.check_output(["git", "-C", directory, *args])


def read_series(directory):
    names = (directory / "series").read_text().split()
    actual = {patch.name for patch in directory.glob("*.patch")}
    if not names or len(names) != len(actual) or set(names) != actual:
        raise ValueError(f"{directory.name}: series does not list each patch exactly once")
    return [directory / name for name in names]


def patch_paths(stage, patches):
    paths = set()
    for patch in patches:
        records = git(stage, "apply", "--numstat", "-z", patch).split(b"\0")[:-1]
        if not records:
            raise ValueError(f"{patch.name}: no changed paths")
        for record in records:
            fields = record.split(b"\t", 2)
            if len(fields) != 3 or not fields[2]:
                raise ValueError(f"{patch.name}: unsupported patch path")
            path = Path(fields[2].decode())
            if path.is_absolute() or ".." in path.parts or path == Path("."):
                raise ValueError(f"{patch.name}: unsafe patch path")
            paths.add(path)
    return sorted(paths)


def verify_series(project, revision, patches):
    head = git(project, "rev-parse", "HEAD").decode().strip()
    if head != revision:
        raise ValueError(f"{project}: HEAD {head} differs from pinned revision {revision}")

    with tempfile.TemporaryDirectory(prefix="jarvis2-patch-check-") as scratch:
        stage = Path(scratch)
        git(stage, "init", "--quiet")
        paths = patch_paths(stage, patches)
        for relative in paths:
            entry = git(project, "ls-tree", "HEAD", "--", relative)
            if not entry:
                continue
            mode = entry.split(b" ", 1)[0]
            if mode not in (b"100644", b"100755"):
                raise ValueError(f"{project}: expected a regular file at {relative}")
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(git(project, "show", f"HEAD:{relative.as_posix()}"))
            path.chmod(0o755 if mode == b"100755" else 0o644)

        for patch in patches:
            git(stage, "apply", patch)

        mismatches = []
        for relative in paths:
            expected = stage / relative
            actual = project / relative
            if expected.is_symlink():
                raise ValueError(f"{project}: expected a regular file or deletion at {relative}")
            if expected.is_file():
                matches = (actual.is_file() and not actual.is_symlink()
                           and expected.read_bytes() == actual.read_bytes()
                           and (expected.stat().st_mode & 0o100) == (actual.stat().st_mode & 0o100))
            else:
                matches = not expected.exists() and not actual.exists() and not actual.is_symlink()
            if not matches:
                mismatches.append(relative.as_posix())
    return {"revision": revision, "patches": [patch.name for patch in patches],
            "files_checked": len(paths), "mismatches": mismatches}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("android_tree", type=Path)
    args = parser.parse_args()

    try:
        patch_root = ROOT / "patches"
        if {directory.name for directory in patch_root.iterdir() if directory.is_dir()} != PROJECTS.keys():
            raise ValueError("Release patch directories differ from the project map")
        manifest = ET.parse(ROOT / "manifests/lineage21-pinned.xml")
        pins = {entry.get("path"): entry.get("revision") for entry in manifest.findall("project")}
        report = {
            name: verify_series(args.android_tree / path, pins[path], read_series(patch_root / name))
            for name, path in PROJECTS.items()
        }
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"Cannot verify release patches: {error}\n")

    print(json.dumps(report, indent=2))
    return int(any(series["mismatches"] for series in report.values()))


if __name__ == "__main__":
    raise SystemExit(main())
