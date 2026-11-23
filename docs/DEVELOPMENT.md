# Development ledger

## 2026-11-23 — new repository baseline

- Created a separate Git repository for unofficial Jarvis2 OS development; older
  experiments remain intact outside it. No device partition or slot changes.
- Imported current controls app and its seven pure-Java suites, current TV
  Settings resources, device configuration and independently authored offline
  audio/Bluetooth patch tooling. No firmware, APK, APEX, kernel or vendor binary.
- Removed PRODUCT_ADB_KEYS from the public device tree; its regression test
  failed against the imported development configuration and passed after removal.
  The running device's trusted keys/debug settings are unchanged.
- Source privacy scan checks candidates for keys, personal identifiers, private
  network addresses and forbidden binaries. Scanner and release-policy tests pass.
- Excluded the DTS replacement and its directly dependent test because no upstream
  redistribution grant was found. The private experiment remains outside Git.
- Added standalone offline app/RRO build/signature verification with no device
  operations. It still needs its first compilation from this repository.
- Added source product module definitions and a device integration fragment;
  they are not yet a passing full Android product build.
- Static release RRO defaults are scoped to this device; preinstalled behavior is
  not yet tested. The live development overlay remains a separate app update.

## Evidence boundary

The live device is a userdebug/test-key build on slot A with enforcing SELinux.
Current Settings/controls/launcher app updates live under /data/app. Audio HAL,
policy libraries, Bluetooth compatibility and remote keylayout currently depend
on RAM mounts. The older offline seven-image candidate predates those latest app
updates and is explicitly unflashed. A public build must remove those accidental
runtime dependencies and pass a separately authorized installation/rollback test.

## Next

1. Port native Bluetooth Settings and pairing changes into reproducible source
   patches with preserved attribution.
2. Compile the app/RRO from this Git snapshot and capture hashes/signature reports.
3. Export exact Android source revision pins and make product integration repeatable.
4. Assemble a clean candidate without unlicensed DTS/Google binaries and without
   owner-specific debug trust. Audit release assets, sizes and AVB chains.
5. Conduct authorized RAM/device tests and clean-install/recovery/rollback tests.
6. Publish only the verified, properly licensed unofficial developer preview.

## 2026-11-23 — reproducibility checkpoint

- Initial commit 9a6948d passed the GitHub Source checks workflow.
- Clean snapshot compiled both app and RRO offline with verified signatures.
  Build identity: app SHA256 abeedc9f9ab72d62266b18fabc63cd28496eae2faaecf31153c26cd38e26000c;
  RRO SHA256 3399d774df5dd1e10823b6c24282f612f072b62904195f3fa199577e65a71ab7.
  These are private development/test-key artifacts, not publicly released APKs.
- Flattened device configuration to the Git root so cloning at device/onn/jarvis2
  gives AndroidProducts.mk/BoardConfig.mk the expected paths.
- Exported 1507-line Android manifest of exact source revisions; replaced relative
  GitHub fetch URL with an absolute public URL and dropped an unused SSH remote.
- Imported existing pairing instructions patch and ported the live AirPods row
  into a normal Java-source patch, preserving original upstream source headers.
- Added patch application/changed-Java compilation verification using copies and
  existing build classpaths. Original Android checkout remains read-only.
- Expanded privacy scanner to audit staged blob content, not only working files;
  regression tests catch a secret staged before the working file is cleaned.
- Added Matter/Thread roadmap after read-only vendor Thread interface discovery.
  No Thread network or radio state changed; operation is not yet verified.

## Native patches and build isolation

The TV Settings source patch verifier passed: two Java source files compiled to
four class files against pinned upstream 26fd224082c96fa32e0bfe60b288093c6e7522f3.
No source-tree or device writes were performed by that verifier.

Added a native Bluetooth-source patch scoped to AACP PSM 0x1001. Host C++ tests
execute the patched function for 24 combinations and confirm the original
function fails the same fallback regression. This ports the previously verified
RAM binary workaround to rebuildable source; it is not native on-device proof
of the new compiled stack yet.

The original build filesystem is read-only. A separate writable thin snapshot
is used for integration; original filesystem stays read-only and the owner's
desktop VM stays running. Thin pool utilization and build resource use must be
monitored. No automatic reboot, flash or partition change is part of this work.

## Public preview launcher/package preparation

- Selected upstream-signed LTvLauncher v2026.11.23 as the bundled OSS candidate;
  pinned exact APK/source hashes, signer and source commit in launcher-inputs.json.
  FLauncher and Bridge remain installed optional choices on the development box.
- Collected exact upstream source archive, GPL text and expanded dependency
  notices outside Git. Further dependency-source inventory is pending.
- Added a standard presigned Android Make module with APK-local native libraries,
  preserving APK bytes and official update compatibility. All inputs are staged
  only after checksum, signer, alignment and ARM32 validation.
- This module overrides the unlicensed Google TV launcher/recommendation modules.
  A source patch makes TV Settings replace the handset Settings package.
- Added validated lz4hc12/64KiB EROFS settings. Image sizes still must be checked
  against the actual slot-A budgets (system483131392, system_ext96161792,
  product541949952 bytes); no repartitioning or slot-B modification is allowed.
- Owner authorized temporarily shutting down the desktop VM to accelerate builds,
  with a separate automatic restart guard. Restore and verify guest health after
  builds complete or fail. This supersedes the earlier always-running constraint.

## Release review and image build retry

- Native Settings, remote controls, overlay and Bluetooth APEX compilation passed.
- Image packaging stopped at the launcher uses-library check. Its APK declares
  optional AndroidX window libraries; the Make module now declares both explicitly.
  No global check bypass was enabled.
- Added regression tests for debug-trust filenames, deleted secrets in Git history,
  output-directory containment and missing staging trees. All 16 Python tests and
  seven Java host suites pass; the full current Git history passes the source audit.
- The desktop VM restarted automatically after the failed build, and its guest
  agent responded. Image generation, final AVB verification and hardware release
  tests remain incomplete. No device partitions were changed.

## Extracted-image verification preparation

- Added a separate offline EROFS extraction/content inspector. It checks actual
  image decoding, required/forbidden package filenames, known debug trust files
  and the bundled launcher's pinned hash, recording before/after image hashes.
- Four fixture regressions cover missing packages, leftover handset/debug-trust
  files, changed launcher payload and a complete scoped fixture. All 21 Python
  tests and seven Java suites pass. These are tool tests, not image results.
- Native review confirmed the five earlier source-review findings are fixed.
  GitHub CI at e3ae5fb passed including full-history privacy scanning.
- Full image generation is active; extracted-image results and AVB remain pending.

## Reproducible launcher dependency sources

- Replaced private source-collection-only provenance with a committed collector
  that checks the exact launcher archive/lockfile and hosted source hashes.
- A real cache verification exposed a valid leading-underscore Dart package;
  added its regression and corrected name validation. All 137 hosted archives
  now verify through the public-source helper with downloads disabled. Five SDK
  dependencies are explicitly recorded separately, not falsely marked collected.
- Full source/license assembly and public image redistribution review remain open.

## Persistent feature gaps and local boot artwork

- Read-only live checks confirm slot A, Android 14 userdebug and enforcing SELinux.
  HAL/policy/config, Bluetooth JNI and remote keylayout still have RAM mounts.
- Added a persistent integration ledger rather than treating those mounts as ROM
  features. Framework review found no safe native fallback for F10/F11 aliases;
  aliases have not been persisted. Native Power/Mic recovery is a release gate.
- Added optional local custom-animation preparation and product selection. Exact
  no-delay archive hash matches the running box; interruptible parts/stored ZIP
  and PNG signatures validate. The older completion-required file is rejected.
  No artwork binary is committed and redistribution review remains pending.
- The running image build has not been modified mid-build; the animation product
  change requires a later cached refresh and extracted-image/boot verification.

## Read-only restore baseline and AVB audit

- Captured sixteen current slot-A partitions privately, matching block sizes and
  device hashes before/after each streamed read. Slot A remained active; no B,
  userdata, bootloader or environment reads/writes were part of the capture.
- All signatures and leaf descriptors passed offline verification for the root
  and boot/oem/vbmeta_system children. Explicit child embedded-key comparison
  against parent descriptors passed as well; follow-chain verification alone
  in this avbtool version is insufficient to establish that key binding.
- This is the existing development baseline, not stock firmware or the candidate.
  Hardware trust for a new key and real restoration remain untested. Added the
  restore evidence/requirements document without claiming an unbrick guarantee.

## Repeatable AVB verification

- Ported the private current-backup audit into an offline source tool with generic
  input paths. It checks full child key binding, native signatures/leaf descriptors,
  fresh output boundaries, cycle detection and optional independent root pin.
- Five integration regressions passed on the build host using real temporary
  RSA-signed AVB fixtures, including a wrong child signer that upstream follow-chain
  verification alone accepts, corrupted signatures and an unsigned root.
- Ordinary host tests skip those integration cases explicitly when no built Android
  checkout is provided. No test or source includes a private signing key.
- The new image build remains in progress; these results do not certify the new
  image set or authorize an installation.
- Re-ran the reusable tool against the complete captured slot-A development
  baseline: signatures, leaf descriptors and parent/child key bindings passed.
  Hardware root trust and restoration remain explicitly unverified in the report.

## Native Power/Voice replay flags

- Framework review confirmed FLAG_FALLBACK bypasses normal single-key gesture
  handling. ButtonRouter now clears it only for replayed POWER/VOICE_ASSIST, which
  native policy consumes before accessibility. Other keys retain their replay guard.
- Added an eighth Java suite for native flags, canceled events and ordinary-key
  recursion protection; all host suites pass. CI's pinned standalone AVB setup
  also passed all five signed-image tests (34 total Python tests without skips).
- This change is separate from the unimplemented alias fail-safe. No permanent
  F10/F11 keylayout or live app update has been installed; native behavior still
  needs a hardware test, including configured multi-press/long-press actions.
- Clean source clone at 58dd0f0 compiled the updated app and matching RRO offline;
  APK signatures and build-manifest generation passed. Artifacts remain private
  development/test-key outputs, not installed or released. The current heavy image
  job predates this source change; the next cached refresh will integrate it.

## Source material and attribution follow-up

- The source collector verified all 137 hosted archives plus four SDK package
  paths in the exact Flutter framework archive; sky_engine remains uncollected.
  Three added regressions cover valid, changed and absent framework material.
- License review identified missing engine and transitive Android/Maven material
  (including the native SQLite AAR/build recipe); complete source/license flags
  remain false. Bridge inventory is simpler but its default has not been changed.
- Added explicit modification/upstream provenance comments to the five adapted
  TV Settings XML files while retaining their original notices verbatim.
