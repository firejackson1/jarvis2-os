#!/usr/bin/env python3
"""Stage local Jarvis2 stock inputs into a fresh Android source workspace."""

import argparse
from hashlib import file_digest
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


def stage(source, destination):
    checksums = Path(__file__).with_name("stock-inputs.sha256")
    expected = {name: digest for digest, name in
                (line.split() for line in checksums.read_text().splitlines())}
    for name, digest in expected.items():
        with (source / name).open("rb") as image:
            if file_digest(image, "sha256").hexdigest() != digest:
                raise ValueError(f"Stock image hash mismatch: {name}")

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        work = Path(temporary) / "stock"
        images = work / "images"
        images.mkdir(parents=True)
        for name in expected:
            shutil.copyfile(source / name, images / name)

        with (images / "boot.img").open("rb") as boot:
            header = boot.read(4096)
            magic, kernel_size, ramdisk_size = struct.unpack_from("<8sII", header)
            version, = struct.unpack_from("<I", header, 40)
            if magic != b"ANDROID!" or version != 4 or ramdisk_size or not kernel_size:
                raise ValueError("Unexpected Jarvis2 boot image header")
            kernel = boot.read(kernel_size)
            if len(kernel) != kernel_size:
                raise ValueError("Truncated kernel")
            (work / "kernel").write_bytes(kernel)

        (work / "files").mkdir()
        for partition in ("vendor", "odm"):
            subprocess.run([
                "fsck.erofs", f"--extract={work / 'files' / partition}",
                str(images / f"{partition}.img"),
            ], check=True)
        work.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ota_images", type=Path)
    parser.add_argument("android_tree", type=Path)
    args = parser.parse_args()
    stage(args.ota_images.resolve(), args.android_tree.resolve() / "vendor/onn/jarvis2/stock")
