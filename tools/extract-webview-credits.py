#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract embedded Chromium Brotli Credits; requires system libbrotlidec."""
import argparse
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import struct
import zipfile

MAX_PAK_BYTES = 8 * 1024 * 1024
MAX_RESOURCE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024


def extract(apk, output):
    with zipfile.ZipFile(apk) as archive:
        members = [m for m in archive.infolist() if m.filename == "assets/resources.pak"
                   or m.filename.startswith("assets/resources.pak+")]
        if len(members) != 1:
            raise ValueError("Expected one resources.pak entry")
        if members[0].file_size > MAX_PAK_BYTES:
            raise ValueError("resources.pak exceeds 8MiB bound")
        data = archive.read(members[0])
    if len(data) < 12:
        raise ValueError("Truncated DataPack header")
    version, encoding, count, aliases = struct.unpack_from("<IB3xHH", data)
    if version != 5 or encoding not in (0, 1, 2):
        raise ValueError("Unsupported DataPack header version or encoding")
    table_end = 12 + 6 * (count + 1) + 4 * aliases
    if table_end > len(data):
        raise ValueError("Truncated DataPack table")
    entries = [struct.unpack_from("<HI", data, 12 + i * 6) for i in range(count + 1)]
    offsets = [offset for _, offset in entries]
    if (offsets[0] < table_end or offsets[-1] != len(data)
            or offsets != sorted(offsets) or any(offset > len(data) for offset in offsets)):
        raise ValueError("Invalid DataPack resource offset")
    resources, total = [], 0
    for i, (resource_id, start) in enumerate(entries[:-1]):
        payload = data[start:offsets[i + 1]]
        if not payload.startswith(b"\x1e\x9b"):
            continue
        if len(payload) < 8:
            raise ValueError("Truncated Brotli header")
        size = int.from_bytes(payload[2:8], "little")
        total += size
        if not size or size > MAX_RESOURCE_BYTES or total > MAX_TOTAL_BYTES:
            raise ValueError("Brotli decoded resource budget exceeded")
        resources.append((resource_id, payload[8:], size))
    library = ctypes.util.find_library("brotlidec")
    if not library:
        raise ValueError("System libbrotlidec is required")
    lib = ctypes.CDLL(library)
    decompress = lib.BrotliDecoderDecompress
    decompress.argtypes = [ctypes.c_size_t, ctypes.c_void_p,
                           ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
    decompress.restype = ctypes.c_int
    found = []
    for resource_id, compressed, size in resources:
        buffer = ctypes.create_string_buffer(size)
        written = ctypes.c_size_t(size)
        if decompress(len(compressed), compressed, ctypes.byref(written), buffer) != 1:
            raise ValueError("Brotli decoding failed")
        if written.value != size:
            raise ValueError("Brotli decoded length differs from declared length")
        decoded = buffer.raw[:written.value]
        if b"<title>Credits</title>" in decoded and decoded.lower().count(b"copyright") > 100:
            found.append((resource_id, decoded))
    if len(found) != 1:
        raise ValueError("Expected exactly one embedded Credits resource")
    resource_id, decoded = found[0]
    # Exclusive creation also refuses existing files and symlinks.
    with output.open("xb") as stream:
        stream.write(decoded)
    return {"resource_id": resource_id, "bytes": len(decoded),
            "sha256": hashlib.sha256(decoded).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("html_output", type=Path)
    args = parser.parse_args()
    try:
        result = extract(args.apk, args.html_output)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(2, str(error) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
