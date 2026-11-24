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
| Linux kernel / kernel modules | GPL-2.0 obligations apply to stock prebuilts too | No public stock kernel image until exact corresponding source/build material is established |
| Stock firmware, vendor/ODM/HAL binaries | Redistribution rights not established by a local backup | Keep out of Git and release assets pending review; require users' local stock inputs where needed |
| Experimental DTS replacement | Pinned upstream has no explicit grant for this file | Excluded; do not distribute copied/derived source or compiled replacement |
| FLauncher 0.18.0 | GPL-3.0-only | Pin and provide corresponding source/build material/notices before bundling its APK |
| LTvLauncher | GPL-3.0 | Pin exact release, source/dependencies and notices before bundling |
| Bridge Console TV | Owner-controlled original app; public repository hosts releases, not full development source | Audit development dependencies and preserve font/third-party notices; do not label it open source without a license |
| Google applications / Android TV Home | Proprietary, not granted by LineageOS source access | Do not bundle in public ROM without a verified redistribution license |

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

## Additional launcher inventory

The exact Bridge Console TV 0.61 preview APK contains owner application classes,
ZXing 3.5.3 and NanoHTTPD 2.3.1, with no native libraries or Flutter assets found.
Its packaged notices include Apache/BSD terms, Antonio OFL, and a jai-imageio BSD
notice retained conservatively. Owner-authorized binary inclusion is distinct
from a grant to label the whole application open source. Available historical
0.38 build source is not exact provenance for the 0.61 release; preserve the
actual APK hash/signature/notices and review later assets/code before bundling.
No bundled-default change has been made on the basis of this inventory.

LTv source collection now identifies four SDK packages inside the verified
Flutter framework archive and a fifth in the pinned generated sky_engine ZIP.
The exact engine archive, matching SQLite binary, native build recipe and SQLite
source were collected separately. Full engine DEPS, resolved Android/Maven runtime
sources/notices, rebuild provenance, and generated Android userspace NOTICE/GPL
inventory remain open. Kernel/vendor exclusion alone is not a userspace license
audit. Keep both complete_corresponding_source and license_review_complete false.

Modified Settings XML now retains its original notices and explicitly records
local modification and the pinned upstream file/revision. This does not change
upstream ownership or the license of bundled application payloads.
