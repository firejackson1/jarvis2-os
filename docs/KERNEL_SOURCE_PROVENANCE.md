# GKI kernel source correspondence

The retained compressed kernel payload is byte-identical to Google's certified
Android 14 GKI January 2026 release 1. This establishes a specific core-kernel
origin; it does not establish the origin or redistribution rights of the whole
stock firmware, vendor modules or device tree.

Google's [release table](https://source.android.com/docs/core/architecture/kernel/gki-android14-5_15-release-builds#january-2026-releases)
identifies version 5.15.196 and source revision
`3d26c188ef7e87e52ea1fa0092db760a55e2ae4c`. The
[annotated release tag](https://android.googlesource.com/kernel/common/+/refs/tags/android14-5.15-2026-01_r1)
also identifies build 14657224. The revision matches the embedded version string
in the retained kernel; the binary comparison below is stronger than that
version-string match alone.

## Executed comparison, 2026-11-24

Downloaded the official `gki-certified-boot-android14-5.15-2026-01_r1-lz4.zip`,
read its sole image member without extracting arbitrary paths, and used the
existing AOSP boot-image unpacker. Compared its kernel payload to the retained
input used by the ROM/recovery experiments:

| Input | Bytes | SHA256 |
| --- | ---: | --- |
| Google ZIP | 17,682,064 | `e349b953f0ab5dab0f026323938b1076047eee0e4e14e806829aba00b6947b16` |
| Google certified boot image | 53,477,376 | `cbe0cc3684dd723bf0c13d3ad90f146bf58074d507ea44419ab0e7fb5239e169` |
| Google and retained compressed kernel, independently hashed | 20,749,256 | `d9ef1096d33fe9f431f4d0cb54f5604a57f5f2fd41b2b86e7c9d499b1571dbae` |

The Google boot container is not the onn boot partition image. Only the kernel
payload equality is claimed. No downloaded image was installed or booted.

## Exact source/build pins

[kernel-gki-14657224.xml](../manifests/kernel-gki-14657224.xml) is the unmodified
public CI manifest, SHA256
`5e5ec3a1e82e9883da4e572132bad06114fe221808863f60b312fadde1351339`.
All 20 projects carry full commit revisions. Each commit's public Gitiles
metadata resolved to its expected revision. That is an availability check, not
an executed checkout, complete source delivery or local kernel rebuild.

The initial JDK metadata read was truncated by the local 256 KiB limit. A
bounded retry read the complete 325,826-byte response and verified its commit.
The ordinary branch manifest contains moving revisions; do not substitute it
for this CI manifest. The initial CI URL without `/raw/` returned HTML despite
HTTP 200 and was rejected as a manifest. Config/environment artifact guesses
returned 404; no missing build configuration is claimed recovered from them.

Use Google's [pinned-manifest source workflow](https://source.android.com/docs/core/architecture/kernel/gki-release-builds)
in a separate kernel checkout. Its exact common tree includes the GKI config,
Kbuild/Bazel files and license terms; the manifest also pins kernel/build and
toolchain projects. See [the scoped receipt](../manifests/kernel-gki-14657224-provenance.json)
for URLs and identities. A fresh source checkout/build and corresponding-source
delivery review remain open. Do not reuse or modify the frozen Android build
tree to perform that work.

## Remaining distribution gates

- Exact source and build recipes for the retained vendor modules are still
  unestablished. Their different vermagic cannot be resolved by assuming the
  generic kernel source includes them.
- A related public Amlogic source tree is useful for comparison, but its GPIO/
  Ethernet extensions differ from the shipped instructions. It is not evidence
  of exact correspondence for these module binaries.
- Device-tree source, firmware/vendor/HAL rights, notices and the final package
  still need their own review. The experimental DTS replacement remains excluded.
- The full public ROM release remains gated by installation/recovery, stability,
  corresponding-source delivery and rights checks. This finding does not clear
  those gates or authorize a binary publication.
