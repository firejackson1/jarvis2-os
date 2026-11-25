# Licensing and distribution review

This is an unofficial LineageOS-based project. We do not seek official-device
status at this stage and do not imply LineageOS endorsement. Original integration
code is Apache-2.0; upstream component licenses, authorship and notices survive.
The assembled ROM is not covered by a single replacement license.

## Distribution gates

| Component | Finding | Public packaging rule |
|---|---|---|
| Original app/configuration/tooling | Local project source, Android API use | Preserve Apache-2.0, NOTICE and upstream resource headers |
| LineageOS / AOSP | Multiple licenses, predominantly Apache-2.0 | Preserve component licenses/notices and exact source provenance |
| Linux kernel / kernel modules | The core payload matches Google's exact GKI release; vendor-module correspondence remains open | See KERNEL_SOURCE_PROVENANCE.md. Complete required source/build delivery and module review before public images |
| Stock firmware, vendor/ODM/HAL binaries | Redistribution rights not established by a local backup | Keep out of Git and release assets pending review; require users' local stock inputs where needed |
| ARM32 LCARS Recovery plug-in | The exact build links one project object and resolves its four shared libraries from stock Recovery | Include the pinned source and compiler-input notices with this plug-in. Derive `vendor_boot` from the user's local stock image |
| Experimental DTS replacement | Pinned upstream has no explicit grant for this file | Excluded; do not distribute copied/derived source or compiled replacement |
| FLauncher 0.18.0 | GPL-3.0-only | Pin and provide corresponding source/build material/notices before bundling its APK |
| LTvLauncher | GPL-3.0 | Pin exact release, source/dependencies and notices before bundling |
| Bridge Console TV | Owner-controlled original app; public repository hosts releases, not full development source | Audit development dependencies and preserve font/third-party notices; do not label it open source without a license |
| Google applications / Android TV Home | Proprietary, not granted by LineageOS source access | Do not bundle in public ROM without a verified redistribution license |

## Stock-file boundary in neutral r2

The [r2 boundary receipt](../manifests/neutral-r2-stock-boundary.json) binds the
five packaged images to the reviewed release ZIP. The comparison used 14
partition images from the pinned stock OTA, including its bootloader, and
checked 996 regular files from seven stock filesystems and 312 entries from
three stock ramdisks. It compared whole-file bytes across the 22 ROM ZIP
members, 5,354 installed userspace files, all 31 APEX filesystems and 49,278
nested ZIP members.

Three nonempty payloads match stock bytes. `snapuserd.rc` and `mke2fs.conf`
match pinned platform source files. The third match is one newline in the
generated `vndkcorevariant.libraries.txt`. A stock placeholder with a Dolby
library filename contains that same newline. The actual OEM Dolby library
and Dolby Vision firmware have different hashes and were absent from the
compared files, as were exact stock bootloader, kernel, module and vendor HAL
payloads.

Recovery reconstruction continues to use the recipient's stock inputs. The
packaged AVB files retain the stock graph and bind the locally reconstructed
Recovery image. The comparison covers whole files from the specified inputs.
Review of transformed code, replaced stock userspace, companion assets and
complete distribution rights remains open.
[Stock foundation](STOCK_FOUNDATION.md) ·
[Pinned snapshot init source](https://github.com/LineageOS/android_system_core/blob/ec299bf6da55702b7b9675d60a0faf2815f0dc6d/fs_mgr/libsnapshot/snapuserd/snapuserd.rc) ·
[Pinned filesystem configuration](https://github.com/LineageOS/android_system_extras/blob/994315964c73b871ae882fcbc3f1d0ae57084647/ext4_utils/mke2fs.conf)

## Component-specific exclusions

The lossless upstream kernel helper has a GPL-2.0 declaration, but that does not
license the rest of its repository. Public visibility or credit is not a general
permission grant. Independent patch tooling in components is experimental and
must not be mistaken for permission to redistribute its proprietary inputs or
for a complete public audio implementation. No third-party DTS source is included.

## Primary references

- https://source.android.com/docs/setup/contribute/licenses
- https://www.apache.org/licenses/LICENSE-2.0
- https://www.kernel.org/doc/html/latest/process/license-rules.html
- https://raw.githubusercontent.com/torvalds/linux/master/LICENSES/preferred/GPL-2.0
- https://github.com/LineageOS/lineage_wiki/blob/main/pages/gapps.md
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- https://github.com/kushmint/ONN4k-Lossless-Audio/tree/132a28b2c724eea05a8d5c5f436f672b2bcc7812
- https://gitlab.com/api/v4/projects/26632151/repository/files/LICENSE/raw?ref=0.18.0
- https://github.com/leanbitlab-org/LtvLauncher/blob/master/LICENSE
- https://github.com/firejackson1/bridge-console-tv

Audit performed 2026-11-23. This records the evidence and unresolved obligations;
it is not a certification that a future artifact is legally distributable.

The 2026-11-24 [GKI provenance check](KERNEL_SOURCE_PROVENANCE.md) found an exact
Google kernel-payload match and its pinned 20-project CI manifest. It narrows
the core-kernel source question but does not establish vendor-module source,
complete corresponding-source delivery or whole-ROM distribution clearance.

## Additional launcher inventory

The exact Bridge Console TV 0.61 preview APK contains owner application classes,
ZXing 3.5.3 and NanoHTTPD 2.3.1, with no native libraries or Flutter assets found.
Its packaged notices include Apache/BSD terms, Antonio OFL, and a jai-imageio BSD
notice retained conservatively. Owner-authorized binary inclusion is distinct
from a grant to label the whole application open source. Available historical
0.38 build source is not exact provenance for the 0.61 release; preserve the
actual APK hash/signature/notices and review later assets/code before bundling.
No bundled-default change has been made on the basis of this inventory.

The controlled LTv candidate now has a reproducible 445-file corresponding-source
bundle: original application, 137 locked hosted packages, five framework SDK
source packages, the resolved 74-coordinate Maven source set and supplements,
43 native source/header/build-input archives, exact SQLite/protobuf recipes,
build records and cumulative notices. Material Icons attribution preserves its
CC BY 4.0 license and identifies APK font subsetting. See LAUNCHER_SOURCE_BUILD.md
and the exact source-bundle whitelist. The r2 audit verifies this launcher
APK inside the ROM and checks its SQLite library both in the APK and beside
it. The library rebuild matches the distributed ELF outside the GNU build
ID. The full ROM redistribution review is still open.
[SQLite rebuild evidence](LAUNCHER_SOURCE_BUILD.md#reproducing-the-armv7-sqlite-library)

Userspace review located embedded WebView Credits and existing GNU license texts.
The supplemental notice packet preserves component-specific license texts,
source/recipe links and reproducibly extracted Credits. See USERSPACE_NOTICES.md.
Recheck actual final-image versions, notice preservation and complete image
contents before publication. Kernel/vendor exclusion alone is not a userspace
license audit; historical broad collection flags do not substitute for this
component-level evidence or final-artifact review.

The [neutral r2 selected source review](USERSPACE_NOTICES.md#selected-native-source-materials-for-neutral-r2)
adds exact source snapshots and a tested installed-file inventory for 18 native
projects, plus the pinned WebView FFmpeg source and LineageOS build patches.
Independent release checks remain for the rest of Android and APEX dependencies,
the complete WebView rebuild/relink route and stock-input rights.

Modified Settings XML now retains its original notices and explicitly records
local modification and the pinned upstream file/revision. This does not change
upstream ownership or the license of bundled application payloads.

## LCARS Recovery plug-in notices

A diagnostic relink reproduced the published recipe's plug-in exactly. The
linker's archive extraction log was empty. Its shared dependencies are
`librecovery_ui.so`, `libdl.so`, `libc++.so` and `libc.so`. An identical-object
compile captured and hashed 156 source and header inputs. The notice companion
includes that index, the project license, and the exact notices for the AOSP
Recovery, Bionic, libc++ and Clang input revisions. Both builds of the notice
companion matched byte for byte. Its file and member hashes are pinned in
[the LCARS notice manifest](../manifests/lcars-notice-provenance.json).

The notice companion covers the pinned plug-in. Whole-ROM and proprietary stock
input reviews remain open.
[AOSP Recovery notices](https://android.googlesource.com/platform/bootable/recovery/+/2e6ff7bc40063d38fc5478389a47c0fafba20bfd/NOTICE),
[Bionic notices](https://github.com/LineageOS/android_bionic/blob/442faf6e7583037dfffdd49425f8659f6a3e3694/libc/NOTICE),
[libc++ license](https://github.com/LineageOS/android_external_libcxx/blob/106fdb332fcd4cab59bf694cf8272e71a67e7845/LICENSE.TXT),
[Clang prebuilt notices](https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+/7154d3eddcb62ff7909a6ae2bf0c03e445e65bc4/clang-r510928/NOTICE).
