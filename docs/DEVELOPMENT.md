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

## Full-image checkpoint and cached retry

- The full image job reached 95% but stopped while dexpreopting the resource-only
  Settings RRO: dex2oat could not find classes.dex. The manifest already declares
  hasCode=false; the import now explicitly disables dex_preopt for this overlay.
  This does not disable verification/optimization for the rest of the product.
- The desktop restore guard restarted the VM after that failure; guest-agent
  health will be verified again after the final build window.
- New product staging lacks the onn-specific keylayout. Added an explicit source
  mapping from observed codes/usages, keeping native Power/Voice and Settings F12.
  No F10/F11 aliases are persisted. Physical validation and the framework remapping
  fail-safe are still pending; the new mapping is not installed on the live box.
- Cached retry will also include the previously compiled replay fix and validated
  no-delay artwork. No device partition writes or slot changes are involved.

## First complete image set — source 73f62f6

- Cached image generation completed successfully after disabling overlay dexpreopt.
  Raw EROFS sizes: system 440750080, system_ext 66928640, product 122597376 bytes.
  All fit their current slot-A budgets including reserved AVB overhead.
- Extracted-image checks passed: filesystem decoding, required packages, pinned
  launcher payload and known debug-trust filenames; forbidden handset/Google
  package names were absent. This remains a scoped audit, not a complete license
  or privacy certification.
- Actual extracted product animation matches the verified no-delay archive;
  native keylayout matches source and Android validatekeymaps reports Success.
  Overlay XML entries and the updated replay class are present in the APKs.
- Extracted Bluetooth APEX JNI matches the freshly compiled source artifact by
  SHA-256. Native behavior on a newly booted image remains untested.
- Desktop VM restored after completion; running state and guest-agent response
  verified. No device partitions were written and slot B remains unchanged.
- At the owner's request, packaged an unsigned/untested raw-image build archive
  with SHA256SUMS, source manifest, checks and license-review material. It contains
  no updater/flash script, boot/recovery/vendor image or complete AVB chain and
  must not be treated as an installer. Private draft delivery completed; GitHub
  reports the ZIP uploaded and its SHA-256 matches the local archive.

## First slot-A hardware test and shared-metadata correction

- Owner requested the test. Built a private AVB set from the exact raw images and
  captured A baseline, reusing the existing root key. Filesystem payload bytes,
  descriptor lists, signatures, chain links, verification flags and rollback
  indices passed offline checks; metadata reports actual build properties.
- Read-only preflight confirmed baseline hashes, no snapshot state and linear
  mappings. Saved controls APK/data backups. Fastbootd reported slot A/unlocked
  and matching sizes; only system_a/system_ext_a/product_a/vbmeta_system_a/vbmeta_a
  were explicitly flashed. No wipe or slot switch was performed.
- New ROM booted A with SELinux enforcing and boot_completed=1. Owner confirmed
  LTv Home and remote navigation/Select. Replaced an older data-installed controls
  update with the exact candidate APK while retaining app data.
- All five installed partitions match full-image hashes. Eleven unchanged A
  boot/recovery/vendor-related partitions match backups. Crash buffer empty.
  This was an existing-data upgrade, not a clean-install test.
- Correction: stock fastboot sent automatic resize commands, and fastbootd writes
  shared metadata views. We cannot claim untouched B metadata from suffixes alone.
  Current B logical entries are unallocated; B is not a verified fallback. Owner
  explicitly chose keeping B unchanged while either-slot support is developed.
- Added read-only explicit-slot planning with seven regression cases and native
  layout checks. Actual A planning succeeds; actual B planning refuses its empty
  foundation. Provisioning/writer support remains incomplete; see SLOT_INSTALLATION.

## Optional Google apps private test

- Target-files packaging completed, but META/ab_partitions.txt is absent;
  misc_info contains virtual_ab=true and allow_non_ab=true without ab_update.
  The artifact is not a configured A/B OTA installer.
- Owner requested GApps. Verified the upstream Android 14 ARM ATV minimal archive,
  rebuilt the exact tested filesystem checkpoint with only expected additions,
  checked APK signatures/content/ownership/modes and signed the matching AVB chain.
- Installed five A images from recovery through temporary linear mappings of
  validated extents. Full readback matched; captured super metadata and protected
  A/B boot/recovery hashes remained unchanged. No slot switch or userdata wipe.
- Android booted enforcing; Play Store reached Google sign-in. Existing-user
  Bluetooth runtime defaults needed explicit grants. Account login and app
  downloads remain untested; Google APKs are not added to public source/artifacts.
- Bazzite was stopped under renewed owner authorization for build acceleration,
  then automatically restarted after the heavy jobs completed. Trace continues.

## Play Store app compatibility correction

- Actual VLC ARMv7 APK badging reports an implied landscape feature requirement;
  the device did not report that feature. Added the truthful landscape declaration
  and a regression that fails against the previous XML.
- RAM verification plus device check-in/Play Store data refresh enabled both VLC
  and YouTube TV installation through Play Store, including their ARMv7 splits.
- Persisted only system_a and vbmeta_system_a from the checked image set. Full
  readback hashes matched; shared metadata and protected A/B boot/recovery hashes
  stayed unchanged. Booted A enforcing; the feature persisted without a RAM mount
  and both applications launched. No slot switch or userdata wipe.
- Source fix is 0311433. Local checks: 45 Python cases (five signed AVB integration
  cases explicitly skipped without the Android tree), source privacy audit and
  eight Java suites passed. The private candidate separately passed the complete
  AVB signature/descriptor/key-binding audit.
- Clean-checkout native overlay work is still unverified and separate from this
  fix. Its resource-bounded compile was stopped to prioritize the live regression;
  do not infer a successful native overlay build from these compatibility results.

## Release preparation checkpoint — 2026-11-24

- Native Settings overlay now builds directly from source against the actual
  TvSettingsTwoPanel resource library, with no staged overlay APK. The native
  build completed 1003 actions. APK v3 signature verification passed and matched
  the build's platform certificate; static overlay target/property scope was
  checked. This remains a development-key compile, not production signing or a
  fresh full-image hardware test. Existing product outputs need installclean
  when migrating away from the previous prebuilt installation path.
- Host checks: 62 Python cases, with five signed AVB integration cases explicitly
  skipped on the local host, source privacy audit and eight Java suites passed.
  These checks do not prove hardware behavior or image redistribution rights.
- Private no-Google candidate ZIP assembled from the preserved base plus the
  landscape correction. Extracted filesystem comparison found only the intended
  XML difference; the coherent five-image AVB set passed offline verification.
  The exact combined candidate has not been hardware tested and has no installer.
- The separate Google apps input is pinned in manifests/gapps-input.json. The
  original upstream ZIP is privately staged, but redistribution permission is
  unverified. Public delivery is its exact upstream URL and checksum; ordinary
  recovery sideload into these EROFS images is not supported.
- Private release keys were generated and an encrypted off-host backup restored
  in memory, with all 204 archived files verified against the backup manifest.
  The unlock secret is held separately in the owner's vault. No private key is
  included in this repository. Production keys have not signed a candidate or
  been accepted by the hardware; existing-data migration remains unproven.
- Built sign_target_files_apks, check_target_files_signatures and apksigner from
  the pinned Android tree; all three help/runtime checks passed. These are tools
  available for the next signing step, not evidence that signing is complete.
- Bazzite was automatically restored after host-tool compilation and remains
  running. This checkpoint performed no device flash, reboot, wipe or slot change.

- Signing-metadata preparation now has 14 malformed-input/content-preservation
  regressions. The real earlier target-files ZIP retained all 6,138 nonmetadata
  entry content hashes; only the two signing metadata files changed. The pinned
  Android signing implementation accepted 127 APK and 31 APEX identities. No
  signature or package image was changed. Full local checks now pass 76 Python
  cases (five AVB cases skipped without build tools), privacy audit and eight
  Java suites. A fresh full target-files build is separately in progress under
  bounded memory/CPU with temporary swap and Bazzite kept running.

- Read-only installation planning now cross-checks native JSON/text metadata and
  validates every logical extent against the reserved prefix, backing capacity,
  alignment and all other partition ranges. Only single-super linear layouts are
  supported. Fresh local checks passed 89 Python cases (five AVB cases skipped),
  privacy audit and eight Java suites. The preserved actual metadata/image set
  still plans A with executed=false and live_physical_identity_verified=false;
  B remains an unallocated foundation. This is not a writer or restore test.
- A bounded userspace artifact audit confirmed development APK/OTA trust remains
  in the earlier private candidate. The preserved launcher is separately signed.
  No preauthorized-key filenames or private-key headers were found in the scoped
  text scan, but binary privacy and vendor/ODM coverage were not established.
  Release signing and network-ADB/updater default policy remain open work.

## Public network-debugging and updater policy — source verification

- Stock vendor input enables network ADB. Product's explicit negative port loads
  after vendor properties, but upstream adbd still falls back to TCP when USB is
  absent. A pinned source patch now respects explicit disabled Android ports,
  preserves positive-port parsing and leaves host behavior unchanged.
- The actual patched helper passed 11 cases each for Android and host policy;
  the original negative-port/no-USB behavior failed before the fix. Its new host
  GTest source passed three tests against the pinned GoogleTest source. Patch
  application and reversal checked against the pinned original adb files.
- Product source sets service.adb.tcp.port=-1 while retaining authenticated USB
  debugging. Existing owner-device settings were not changed. Explicit listen
  addresses and user-enabled wireless debugging remain separate paths.
- The mandatory launcher now uses Android's existing module override mechanism
  to exclude stock Updater, removing its automatic and manual official-channel
  surface. OTA trust replacement remains a later signing step; recovery is not
  changed. If launcher packaging changes, preserve the Updater exclusion.
- These are source/host results. The active full build predates this patch;
  final adbd APEX, installed property precedence, absence of Updater and runtime
  listener state still need image/hardware verification before release.

- A private signing-pipeline rehearsal used the preserved historical target-files
  archive. An output APK passed signature verification and its certificate matched
  the new project release certificate. The pipeline then failed at the first APEX
  because the input lacks avb_avbtool metadata. The partial archive is not a
  candidate or release. This establishes one APK key use, not complete package,
  APEX or image signing, hardware trust or migration compatibility. Key bytes and
  the verified backup remain unchanged; generation-time inventory flags are not
  current key-use status. Required metadata preparation is being corrected.

- The signing preparer now supplies only the missing avb_avbtool lookup required
  by the pinned APEX signer. Strict misc metadata regressions reject malformed or
  duplicate keys and preserve valid existing settings. Fresh local checks passed
  94 Python cases (five AVB skips), privacy audit and eight Java suites. Actual
  v2 preparation retained 127 APK/31 APEX identities and added precisely that one
  misc line, independently compared with the original. A second private signing
  rehearsal is running; no completion or hardware claim follows from preparation.

- The second private signing rehearsal completed. Independent API-34 checks
  validated 103 re-signed standalone APKs, 21 embedded APKs, all 30 re-keyed APEX
  payload signatures/hashtrees and intended keys, with preserved launcher/shim
  bytes. Strict non-signature APK comparison includes LICENSE/NOTICE/services.
  A separate native filesystem comparison covered 31 APEX images: 1,018 paths,
  modes/UID/GID and raw xattrs/SELinux labels matched; 742 non-APK regular files
  and 13 symlink targets matched. Only the 21 already-verified APKs changed.
  Timestamps, inode flags/layout and hardlink topology were outside that proof.
- The signer drops five prebuilt vendor/ODM/module reference images when their
  trees/build flags are absent. The rehearsal target-files is therefore not a
  complete OTA/full-image artifact. Preserve and verify those original reference
  inputs separately. Raw-image AVB, OTA trust and hardware acceptance remain open.
- Actual pinned-source launcher runtime resolution completed with 93 components,
  467 edges and zero unresolved dependencies, while all eight original config/
  lock hashes stayed unchanged. The relocated protobuf dependency's empty sources
  JAR is supplemented by its official release-linked source recipe and original
  4.28.2 sources. Evidence pins are in launcher-native-materials.json; complete
  corresponding-source/notice assembly and the controlled APK build remain open.

- Portable public package/filesystem verifier commands and a 77-role template
  are now available. Actual execution of the promoted code passed with a pinned
  78-record public inventory and pinned prior report; the optional extra record
  was only an image-key inventory check, not image AVB verification. Independent
  baseline/role-policy authentication limits remain explicit. Focused regressions
  cover META-INF integrity, native directory parsing, public-path/JSON boundaries
  and JDK environment selection. No keys or certificates are tracked here.
- A controlled ARMv7 launcher APK was built from the pinned source on PVE. Its
  classes.dex, Flutter runtime and SQLite library match upstream bytes; its Dart
  AOT library differs, so whole-APK upstream identity is not claimed. After project
  signing, all 590 non-signature entries matched the unsigned build and v1/v2/v3
  signatures plus native alignment verified. It remains separate from the active
  ROM build: no launcher input pin or device installation changed yet.

- Userspace notice review found existing GNU texts and embedded WebView Credits;
  missing module associations alone were not treated as missing licenses. Added
  verbatim supplemental texts, a source/recipe index and a bounded DataPack/Brotli
  extractor. Actual baseline extraction matched the indexed Credits digest.
  Ten real-decoder/malformed-input regressions joined the host checks. Generated
  Credits, SDKs, caches and notice archives are not tracked. Final-image version
  and notice-preservation checks remain separate.

- Controlled launcher corresponding-source delivery is now assembled from an
  explicit 441-file whitelist, with sources, build records and cumulative notices.
  Two independent assemblies produced SHA256
  `6d3a8f5ec402a895987769ba22bbfe9925f32893301a61615143f6e640749e94`;
  all members passed hash/size readback. Material Icons attribution correctly
  preserves CC BY 4.0 and identifies the APK's font subsetting. SDK executables,
  caches, private logs and signing keys are excluded. Twelve assembler regression
  tests pass; current full host suite passes 142 tests with five local AVB skips,
  source privacy audit and Java checks. This source delivery does not change the
  active ROM's launcher pin or establish hardware acceptance.

- Added a Google-free 27-file composition recipe and strict profile exporter.
  Native proof preserved metadata on 6,039 base paths and accepted exactly 42
  new paths; UID/GID/mode cross-checks and label/capability tampering fixtures
  passed. No regular-file byte-equality, complete rebuild, AVB composition or
  hardware acceptance is claimed by this stage. Current host checks: 142 tests,
  five local AVB skips, privacy audit and Java checks passed.

- Default source launcher pin now selects the controlled project-signed APK and
  its verified certificate. Missing local APKs fail before network access; no
  fake upstream URL is paired with the new digest. Two regressions first failed
  against the old pin, then passed. Current suite: 145 tests, five local AVB
  skips, privacy audit and Java checks passed. The active Android checkout was
  not modified; integration waits for its running full build to finish.
- Updated the release checklist to reflect current Bazzite-running policy, actual
  private signing/source/profile evidence, and remaining final artifact gates.
