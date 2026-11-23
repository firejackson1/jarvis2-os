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
