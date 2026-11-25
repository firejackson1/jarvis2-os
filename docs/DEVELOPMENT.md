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

- Exercising the pinned native OTA-key replacement exposed a Python 3 bytes/text
  TypeError and nested certificate ZIPs retaining host paths. A two-line source
  patch decodes the metadata and uses certificate basenames. Clean application
  to the exact pinned source and isolated execution of both actual native
  functions passed explicit/empty-key-list and system/recovery cases. No real
  certificate signing or active Android source change occurred. CI now repeats
  the source-hash-pinned native regression; full host suite still passes 145
  tests with five local AVB skips, privacy and Java checks. Actual final-image
  trust replacement/verification remains pending.

- GitHub source checks passed at 741b02b, including actual checksum-pinned
  releasetools patch application/native OTA-key fixtures and signed AVB tests.
  Reconciled stale license/signing matrix text with completed component source
  and private rehearsal evidence; final-image and hardware gates remain open.

- Read-only OTA trust inventory of the preserved target-files found one system
  otacerts.zip, an empty META/otakeys.txt and an extra Lineage recovery identity.
  Isolated actual native replacement with public-only project material passed:
  exact approved certificate, basename-only ZIP member and no old system test
  certificate. No recovery trust archive exists in that input; full target-files
  signing/final-image/recovery trust remain unproved. Explicit mapping of the
  extra recovery identity is required in the final signing plan.

- Final extracted-image policy now explicitly rejects the unsupported official
  Updater APK, supplementing its source-level package exclusion. A fixture that
  retained it failed before this guard and passes after the correction. Full
  working-tree suite passed 153 tests with five local AVB skips, including seven
  in-progress composer tests not yet part of this commit; privacy/Java passed.
  Actual final-image package absence remains a separate required check.

- Added the local Google composer and ten regressions. Root review corrections
  enforce 4KiB AVB geometry, rehash all five baseline inputs and fail on prefix
  EOF. Actual native rehearsals used the exact upstream Google ZIP, synthetic
  EROFS/AVB references and disposable keys: 27 files/16 APK signatures, unchanged
  existing bytes/links/ownership/modes/raw labels/caps, full baseline/final AVB
  and deterministic five-image outputs passed. Independent readback rehashed
  all ten actual outputs and confirmed equality. No project private key, owner
  firmware, device or slot was used. Full checks passed 156 tests, five local
  AVB skips, source audit and eight Java suites. Final signed-ROM composition,
  hardware trust, installation and restoration remain open.

- Full bounded policy target-files build completed successfully (2h40m13s) with
  Bazzite running. Preliminary archive inspection found 103 standalone APKs,
  31 APEX packages, the single native system_ext overlay, no official Updater,
  authenticated USB defaults, product network-port -1 and generic build identity.
  The package verifier now distinguishes the observed 104-APK legacy rehearsal
  from the 103-APK no-Updater input while keeping APEX/embedded counts strict;
  the regression failed before this update and passes afterward. Host checks
  passed 157 tests with five local AVB skips, privacy and Java suites. This
  archive still contains the old launcher; controlled integration/signing and
  final extracted-image verification remain pending.

- Current signing v1 completed and independent package checks passed 78 public
  key records, 103 standalone APKs, 31 APEX and 23 embedded APKs. OTA archive
  inspection nevertheless rejected it: the command selected a stale Soong-copy
  signer rather than the rebuilt installed executable, retaining a host path.
  Preserved that rejected output and started v2 with the exact installed binary
  hash and host-first tool path. No artifact from v1 was installed or published.
- Added the separate raw-EROFS AVB assembler, leaving the Google composer intact.
  Six regressions and two actual native runs passed on synthetic references and
  disposable keys; root independently rehashed all ten output files and verified
  identical five-image results. Full host checks passed 163 tests, five local
  AVB skips, source audit and Java checks. Final payload content/metadata intent,
  actual firmware/key acceptance, installation and restore remain separate gates.

- Neutral launcher replacement is signed and independently verified: unsigned
  `8d68a7b83a56a5759ef3bf9a06b026e6b153795ad2fb9c1750bd75b36c102e25`,
  signed `ac585d5a0bb3c13c2ea346d052d1fa5140a6bb35bbe90a20002f776f92c03347`.
  All 590 non-signature entries survived signing. Original 298 source files,
  93 runtime components/78 selected artifacts, DEX/engine/SQLite and other assets
  match the earlier controlled build; only libapp.so changed. Its generated Dart
  URI now uses the documented neutral workspace. The first neutral build was
  rejected for missing native plugin metadata; explicit offline Flutter pub-get
  preparation restored the verified plugin/dependency set before rebuilding.
- Refreshed 445-member corresponding-source bundle reproduced independently:
  SHA256 `aa26fe3cc3395559730983c7248e3d2d5243847f18e46c730bd9e2e6776b2966`,
  474377768 bytes. All members passed hash/size readback; 179 textual records
  have no matching private paths/key markers. Prior source bundle is preserved.
- Added stock-template AVB mode without requiring private owner bootstrap or old
  replaced userspace images. Actual stock template signatures/chain binding and
  all 11 reference file pins passed; ten references are AVB-covered, odm_ext is
  explicitly pinned but unbound in the stock graph. Dynamic policy derives all
  nine userspace fingerprint/version/patch properties from canonical payload
  build.props; security patch explicitly uses the system-global value. Synthetic
  stock-mode runs were deterministic, coherent-mode property update passed, and
  root rehashed all 15 actual proof images. No production key/device was used by
  those proofs. New final payload integration/signing/hardware tests remain open.
- Documented explicit source-revision build number and commit-time build date,
  supported by the pinned Soong frontend, to remove default host/time identity
  variability. Current full host suite: 167 tests, five local AVB skips, privacy
  audit and Java checks passed. Final-image properties must be inspected again.

### Final candidate checkpoint — 2026-11-24

- Source `1ac457e6b28b3138ba9bf1eccdb642fe881bca2b` built with explicit
  `jarvis2.1ac457e6b28b` identity and source epoch `1795514834`.
  Signed target-files SHA256:
  `6329613453164426fe89d19d351677c5222c0f12961ebce3466946bcbe6dbfe5`.
  Production package verification passed 103 standalone APKs, 31 APEX containers,
  30 APEX payloads and 23 embedded APKs. The OTA certificate archive contains
  only the project release certificate, with no signing-host path.
- All 31 APEX filesystem comparisons passed: 1,018 paths, 765 regular files,
  13 symlinks and 21 explicitly expected embedded-APK changes, no unexpected
  metadata changes. Timestamps, inode flags/layout and hardlink topology remain
  outside this verifier's scope.
- Actual stock-template AVB assembly passed with FEC enabled, stock boot
  references and project image key. Independent comparison matched all nine
  payload-derived properties in leaves and owning parents, all verification flags
  zero. Assembly report SHA256:
  `b22c863c26e1637a8356e8284d66567b85699afc790176d8a42123c46840a7f6`.
  Replaced historical userspace bytes are not authenticated by this mode;
  unchanged stock references and the complete resulting graph are verified.
- Fresh extracted-image privacy scan covered 6,119 regular files, 31 APEX,
  50,502 ZIP entries and 67 decoded streams with zero coverage gaps. Reviewed
  matches are upstream public constants and bodyless PEM-format markers;
  the neutral launcher contains its declared public build workspace URI.
  No open privacy finding. Native intent comparison found only 137 approved
  signing/package/trust changes with all 6,030 native paths' metadata preserved.
- Source repository made public after exact-commit CI and full-history privacy
  audit. No image is published or installed by this checkpoint. Hardware key
  acceptance, clean setup, full feature tests, installation and actual recovery
  remain open. Matching GApps composition is local-only and still in progress.

- Matching GApps composition against the stock-based candidate passed twice; all
  five outputs were identical and all ten actual files independently rehashed.
  Determinism report SHA256
  `d32b46b31361674dcde5dffbb9de902071280f943b57759489fa77e353674a23`.
  This proves repeatability of composition from these inputs, not a second full
  Android source rebuild or hardware behavior.
- Google-free offline candidate ZIP: 560062731 bytes, SHA256
  `553167d323e40946a50416767c3f3cab1ec124cfad9f4a7bf56748984fcf284d`.
  Local-only GApps candidate ZIP: 777922581 bytes, SHA256
  `01405a81f37024a419ba06fc79634c347dd0cf2c7fa6e7a2ecb8b0cef14ffc0e`.
  Every ZIP member passed independent hash/length readback. Neither ZIP is an
  installer or OTA; neither has been hardware qualified or publicly released.
  Google payload redistribution is not authorized; public instructions use the
  upstream input and local composer. Exact seven-partition dependencies and
  interruption limits are recorded in RESTORE_PLAN.md.

### Candidate held after static permission review — 2026-11-24

The `1ac457e` ZIPs are retained as offline evidence and must not be installed or
published. A subsequent static security review found that the RemoteSettings
`prebuilt_etc` allowlist was installed under its extensionless module name.
Android SystemConfig only loads `.xml` permission files. The XML also omitted
`MEDIA_CONTENT_CONTROL`, a requested privileged permission under the enforced
allowlist policy. Earlier scoped packaging/privacy/AVB checks did not cover this.

The source fix preserves the XML source filename and adds the missing grant.
Image inspection now requires the actual system_ext XML, correct package and all
three required privileged grants; extensionless and wrong-package fixtures failed
before the check was added and pass afterward. A clean offline rebuild and all
candidate signing/content/AVB/package checks must run again before promotion.
This is a packaging correction, not evidence of runtime permission success.

- Added a portable vanilla five-image packager with caller-pinned proof binding,
  explicit metadata whitelist, deterministic ZIP metadata, full streamed member
  readback and input/proof rehash. Seven focused tests passed, including a real
  CLI run and two independent byte-identical archives. Full host suite: 176 tests,
  five local AVB skips, source audit and eight Java suites passed. Companion
  source/notice/public-key assets are documented separately; packaging does not
  establish hardware readiness, source correspondence or redistribution rights.
  This tooling update does not alter the frozen `f38da52` product build.

### Read-only recovery transport checkpoint — 2026-11-24

On the working development installation, USB ADB entered recovery with UID 0,
read the current super metadata prefix and boot-control record, entered userspace
fastbootd, performed only getvar queries, and returned to a completed Android boot
with USB ADB available. Initial and final active slot: A. No flash, wipe or slot
selection command was issued. This does not test the new production-key candidate.

Fastbootd reported `snapshot-update-status: none`; the valid version-2 misc
Virtual A/B record also had raw merge status 0. Both fresh logical metadata views
matched and passed the planner's extent/layout checks. A has an allocated
foundation; B does not. Boot-control flags alone do not establish B bootability.
Metadata's filesystem was not mounted; these are the fastbootd and raw-record
observations at this checkpoint, not a promise about future snapshot state.

Current recovery/fastbootd/Android round-trip transport is verified. Restoration
after an interrupted multi-partition update, pre-recovery failure recovery, clean
setup and new signing-key acceptance remain untested. Raw captures stay private.
The first exec-out captures mixed dd diagnostics with binary stdout and are
retained as non-authoritative; clean shell-v2 captures have exact expected lengths
and the boot-control CRC validates.

### Corrected candidate and installer checkpoint — 2026-11-24

- Product source `f38da52af274a0e50c92a10cf279e62f44125358` completed a clean
  offline build. Frozen original target-files SHA256
  `bf6fa729cbc4df1d03fbe1eeb27f8abf861a00c01d38a6c780cf47b600845a2f`;
  project-signed archive `b16c9d3bfbe0539dae01f328554718225525abeb43a2c238c9f16259bc92295f`.
  Staging initially expected a versioned filename and verification initially
  supplied a duplicated bin path; both wrappers stopped before promotion and
  were corrected without rebuilding or re-signing. Rejected logs are retained.
- Package/APEX signatures, native filesystem comparisons, system OTA certificate
  replacement, image contents and complete stock-template AVB passed. Independent
  fresh audit summary `774a819f5b13f6634bab41f603b610be72bc65e8a63b53262f08c4007de3f1a5`
  has no open scoped findings. Actual loadable XML, all three grants, APK requests,
  intended signer, native metadata and enforced allowlisting passed; runtime grants
  remain untested. Whole-image AVB report
  `8cee26a88cb20c97b282152ebf831412cba530784be23200a67171508f592f72`.
- Portable vanilla ZIP: 560062457 bytes, SHA256
  `870fce6c604b144f0a5eeeedb7b9208efa76a8aa98e51d961b52b683b2e0077f`.
  Local-only GApps ZIP: 777922321 bytes, SHA256
  `f48dbde4381e9c146fdb68a51fd14f5eeaa74445ec8742943d6ded5e0540541b`.
  Both passed full member readback. Two actual GApps compositions produced
  identical five-image sets, all ten files independently rehashed. No hardware
  install or public binary publication follows from these checks.
- Current device hashes differ from the older restore set in five partitions,
  exactly explained by the recorded Google-app and landscape installations. A
  separate current sixteen-partition private restore set now matches live hashes
  before/after capture and passes AVB signature/leaf/key-binding consistency.
  Old backups remain intact. This is verified backup consistency, not an actual
  restoration or external hardware root-of-trust proof.
- Added a recovery-only raw writer with pinned inputs, RAM linear mappings,
  protected-byte checks and durable before-write/readback journals. Seventeen
  file-backed flow tests cover partial writes, resume/restore, seven-target
  transitions and distinct protected A/B data. Review fixed hidden metadata
  mounts, unsafe staging, stale post-transfer targets/maps, completed-journal
  misuse, mixed transition proofs and Recovery ADB state. Surviving dd processes
  block resume; no automatic kill, boot, wipe, activation or LP writer exists.
  Full host suite: 193 tests passed, five local signed-AVB skips, source audit and
  eight Java suites passed. Actual recovery ABI, read-only metadata setup,
  installation, fresh boot and interruption restoration remain unqualified.

### Frozen candidate source closure, 2026-11-24

- Audited all 1,430 pinned project HEADs and reconstructed eleven changed/new
  files across five upstream projects. Published the previously missing
  SetupWizard Bluetooth permission patch as a separate supplement; frozen product
  commit and images remain unchanged.
- Exercised frozen launcher and animation preparation in a fresh sparse workspace
  using pinned SDK/JDK inputs. APK, three libraries, license, notices and animation
  matched staged inputs byte-for-byte; temporary bootstrap link was removed.
  This verifies input preparation, not a complete clean rebuild or hardware boot.
- Full host checks passed: 193 Python tests, five local signed-AVB skips,
  source privacy audit and eight Java suites. No device writes or slot changes.

### Recovery helper hardware check, 2026-11-24

- Authorized read-only check on the current development slot A recovery: the
  pinned ARM32 dmctl executable ran from tmpfs RAM and listed device-mapper
  devices/targets successfully. No existing mapper devices were present.
- Mounted metadata as F2FS read-only with recovery replay disabled; OTA state
  was absent and the snapshots directory empty. Unmounted it afterward; full
  metadata hashes before and after matched. No persistent payload writes,
  installer execution or slot activation occurred.
- This qualifies the helper and read-only inspection setup on the existing
  recovery only. Raw-writer dry-run, candidate recovery, installation and actual
  restoration are still separate hardware gates.

### Recovery installer dry-run, 2026-11-24

- The exact committed raw writer completed its first authorized native Recovery
  dry-run using the corrected f38 production-key candidate and explicit stock
  init_boot/vendor_boot transition inputs. Twenty physical and eight allocated
  logical partitions were captured; both native LP views agreed, and all seven
  targets matched their pinned old restore images. No --execute was supplied.
- The writer created read-only RAM mappings and a durable host journal containing
  only its header. Result: executed=false, final_set=not_written. All physical
  partition hashes and the protected super prefix matched after the check.
  Android returned fully booted on slot A; Bazzite remained running.
- An initial host-only staging attempt stopped at an EXDEV hard-link error before
  invoking the installer. Moving staging to the same build volume resolved it;
  that failed capture and its logs remain intact. Both attempts returned Android.
- This qualifies this dry-run and existing Recovery transport only. Persistent
  installation, replacement stock recovery, data/signing-key migration, rollback
  and interruption restoration remain untested; no installation approval follows.


### Replacement recovery transport review, 2026-11-24

- Inspected stock vendor_boot ramdisks offline without extracting or executing
  their programs. Compared default properties, init service launch configuration
  and executable hashes to the existing development recovery.
- Stock sets secure/authenticated ADB and non-debuggable properties; development
  recovery enables debugging and uses an adbd rather than su root launch label.
  The adbd executable is identical. Therefore native dry-run success in the
  development recovery does not establish replacement-stock root ADB or restore
  availability. No stock recovery hardware boot or device change was performed.

### First production-key hardware installation, 2026-11-24

- After explicit owner approval, wrote and fully read back the exact corrected
  f38 seven-image slot A set: system, system_ext, product, init_boot, vendor_boot,
  vbmeta_system and vbmeta. The journal recorded every before-write and verified
  event followed by completion. No LP writer, snapshot cancel or slot switch ran.
- All non-target physical hashes and the protected super prefix remained
  identical at post-install verification. The driver then requested Recovery,
  which enumerated over USB. Its pulled default-properties file matched stock.
- Stock Recovery's ADB shell attempt failed while setting a subprocess SELinux
  context. This is an observed restoration-transport issue, not successful root
  Recovery qualification. No repeated shell-crash tests were performed.
- The owner completed the approved shared-data reset and reported Android setup
  appearing. Setup completion, remote pairing and device-side build checks remain
  unverified; USB detection currently fails before an ADB connection. This does
  not establish rollback, interruption recovery or public readiness.
- The next installation rehearsal must follow the published normal-user process
  on a standard computer. Private host scripts/captures, access to our servers,
  manually authored trust assertions or an AI operator cannot be prerequisites.


### Recovery product direction, 2026-11-24

The owner requires the public ROM to include a compatible custom recovery rather
than replace it with stock Recovery. The stock-recovery f38 installation remains
an engineering trial, not the final release package. The owner selected an LCARS
interface and requested onn Bluetooth remote pairing/navigation. A separate
recovery-only project is implementing that interface offline; no replacement
recovery has been flashed. The public installation rehearsal must still work
without private scripts, server access or an AI operator.

### Clean-install side-panel activation, 2026-11-24

- Read-only inspection found the companion installed at its system_ext
  privileged path, with injection, audio-routing, media-control and privileged
  Bluetooth permissions granted. Its accessibility setting was off and no key
  service was enabled. This was missing activation, not missing side-panel code.
- Saved the previous settings privately, enabled only the companion's key
  service while preserving any existing service entries, and verified it bound
  with no pending or crashed accessibility services. Direct Bluetooth activity
  launch succeeded. The owner then verified both Bluetooth on Settings hold and
  left widgets on double-press. No APK install, partition write, wipe, slot
  operation or reboot was needed.
- This live setting does not change the frozen f38 images. Added a release
  gate for visible normal-user activation without ADB/AI and updated the
  integration ledger. No personal service lists/preferences were added to source.
- The later powered keep-awake setting is also device configuration, not part
  of the frozen ROM. It does not qualify the unresolved genuine suspend fix.
- Validation after these documentation updates: host suite ran 193 tests with
  five local AVB-tool skips; all executed tests and eight Java suites passed.
  Source privacy audit and `git diff --check` passed. No product source changed.

### Discoverable shortcut activation candidate, 2026-11-24

- Controls source now shows its own accessibility-service state and an
  Enable/Manage button before controller selection, including with no paired
  controller. Disabled state receives initial focus. Returning from Android
  Settings re-renders the status. The app opens the standard Accessibility
  action and never writes the enabled-service list; a missing handler gets a
  visible explanation. Version code advances to 2, version name to 1.1.
- Actual TV Settings source and a device-side intent-resolution query confirm
  ACCESSIBILITY_SETTINGS resolves to its TV accessibility activity. A specific
  service-details action was not registered, so the source uses the general
  supported action. This is route availability, not a completed UI test.
- Private app-only build from clean source
  `46c1c1be8683aa919893ea7903c3e4e7d5ba4877` completed against public SDK 34,
  with signing/verification and a clean Git-bound build manifest. Companion:
  78,293 bytes, SHA256
  `85c4e773a3665cc72f1f4fc0fa9827cf70e94ab6277aec66823f349ceda95da9`.
  The unchanged Settings RRO is 25,277 bytes, SHA256
  `0ff950ad737885c2d1cc288c4d56eae80655741804a4f0a5415dfb1fe56d44ef`.
- An earlier source-archive attempt compiled/signed but failed the final
  provenance step because the archive lacked Git metadata. It was retained as
  failed, then replaced by an actual clone of a verified bundle. No checks were
  disabled. Final bounded job completed in 7.9 seconds at 354.5 MiB peak with no
  swap. Bazzite remained running throughout.
- Host suite ran 193 tests with five local AVB-tool skips; all executed tests
  and eight Java suites passed. These tests do not exercise the new Android UI.
  Review was inline self-review, not an independent review.
- UI hierarchy capture produced no XML; the screenshot was black. Power state
  showed deliberate Power-button sleep, so the screen was left off. No RED UI
  test, visual success or app installation is claimed. Matching the installed
  signer, both status states, another enabled service, no-controller behavior,
  the consent route and return navigation remain live tests. No partition
  flash, slot change, reboot, user-data wipe or binary publication occurred.

### Bound sleep traces and temporary mixer experiment, 2026-11-24

- Compared retained module files to current filesystem hashes and loaded GNU
  build-ID notes. Three complete file hashes and all five selected notes match;
  early-module live files remain unavailable after switch-root. See
  SLEEP_AUDIO_INVESTIGATION.md for the identities and limits.
- A 30-second isolated boot-clock trace captured five suspend/resume cycles with
  speaker GPIO mute/unmute writes. A second 30-second capture with the standard
  `SPK mute` control temporarily On captured five further cycles without the
  card worker's unmute. The original Off value was restored and read back.
  Neither trace lost events, and both private instances were removed with
  global tracing unchanged. No kprobe, sleep/wake request or forced power action.
- TinyALSA source was clean at `2ed34d52a7a7b83dba0d1c27d777f8eb70b3f3e9`.
  The diagnostic ELF was 8,468 bytes, SHA256
  `58797e91015f3af6e312d8bf18aa2d499899a3cff2a85ed2a0e2322b54752033`.
  Its installed library hash matched. The temporary device copy was removed;
  the newly created build-output install file was also removed after preserving
  the diagnostic privately. Existing ROM images and frozen archives were not
  rebuilt. Compilation caches were retained.
- Operational error: a shell continued after a failed memory preflight and
  launched the small native build. The stop request found it already completed
  successfully. Actual runtime was 18.2 seconds, peak 4 GiB memory/2 GiB swap.
  Bazzite stayed running; no VM action was taken. Future resource gates must
  launch jobs from the checked control flow, never a following shell command.
- REA recognized an input ELF but had no configured decompiler. Used LLVM
  instruction/relocation inspection; no successful decompilation claim. Kept
  vendor binaries, captures and runtime state out of the repository.
- This is a narrowed mechanism, not a completed sleep fix. Audible confirmation,
  the initiating wake trigger, normal audio and genuine wake remain open.
- Validation: `tools/test-host.sh` ran 193 tests with five local AVB-tool skips;
  all executed tests and eight Java suites passed. Source privacy audit and
  `git diff --check` passed. No product source changed in this checkpoint.

### Music session cleanup candidate, 2026-11-24

- Read-only source inspection at pinned Music revision
  `c119d5a52f80289c7f939746ddc31c8bcee2a3ca` found a MediaSession created in
  onCreate and an empty onDestroy. A live service start/stop left additional
  inactive sessions (20 before, 22 afterward), with no service running at the
  end. Bluetooth browsing can concurrently recreate this service, so this is
  not an isolated per-cycle leak measurement or a demonstrated sleep cause.
- The diagnostic script stopped after one cycle because it required exit zero:
  this Android shell's successful `am stopservice` prints "Service stopped"
  but returns -1 (255). Inspected its pinned implementation and independently
  confirmed that the service was absent afterward. No force-stop, UI launch,
  sleep/wake request, reboot, APK update or slot action was used.
- Added a future-build Music patch to release/null its session and call the
  superclass. A pinned-source fixture regression first failed for the missing
  patch; after implementation the patched callback passed normal, repeated
  and null-session cleanup, while the original failed its resource-leak
  assertion. This exercises actual callback statements with instrumented
  ownership/superclass counters, not an Android framework simulation.
- Compiled the complete changed class against SDK 34 and the existing matching
  Music javac jar in a fresh private directory. Javac exited zero in 1.7 seconds,
  capped at 256 MiB heap/512 MiB cgroup/no swap. Bazzite stayed running. The
  original Android project remained clean and byte-unchanged; no Soong graph,
  APK, ROM image or frozen archive was rebuilt.
- Original source SHA256
  `f1c30950182cd36f08ff8dfede5ff9f31815ac77524f22c8081d7ec7b9a8bf14`;
  patched source `9683f799b48024f953fd28eaf3224f1670c158fde6a1439e91f0a879d17a0a13`;
  patch `7987a702175bffbec5c4f17b5a27b792ff65f0457c68bea2873448aa445a4911`.
  SDK hash `802de40af3f2967e56c4d1e9b75a19963815bf4b6c73ce2bbd24ecd9f7561e10`;
  matching classpath `3e2235e65429097a78e8408df4a3bf6867951cf47b20ae3f60c24d2bb51022df`.
- The patch is not installed. Future-image integration, an on-device lifecycle
  check, browser reconnect and normal playback remain open. Speaker/suspend
  qualification is unchanged.
- Validation: host suite ran 194 tests with five local AVB-tool skips; all
  executed tests and eight Java suites passed. Source privacy audit and diff
  checks passed. A separate read-only reviewer found no actionable code issue
  and confirmed the callback regression's framework-testing limits.

### Exact public GKI core source origin, 2026-11-24

- Google's January 2026 Android 14 GKI release record and annotated tag identify
  kernel common revision `3d26c188ef7e87e52ea1fa0092db760a55e2ae4c`, build
  14657224, version 5.15.196. Downloaded its official certified LZ4 ZIP and
  unpacked its sole boot image with the existing AOSP tool.
- The 20,749,256-byte compressed kernel payload independently matches the
  retained ROM/recovery kernel byte-for-byte: SHA256
  `d9ef1096d33fe9f431f4d0cb54f5604a57f5f2fd41b2b86e7c9d499b1571dbae`.
  This is a payload comparison, not a claim that Google's boot container is the
  onn's partition image. No downloaded image was booted or installed.
- Preserved the unmodified 20-project CI manifest and scoped public provenance
  receipt. All 20 exact project commit metadata endpoints resolved. The initial
  JDK response was truncated locally; a bounded retry verified its full response.
  No complete source checkout or local kernel rebuild is claimed.
- See KERNEL_SOURCE_PROVENANCE.md for exact archive/manifest identities and the
  failed/non-manifest URL checks. Vendor-module source correspondence, device
  tree/firmware rights and complete required source delivery remain unresolved;
  the full binary release is still gated.
- Validation: exact manifest SHA and all 20 pinned project revisions checked;
  host suite ran 194 tests with five local AVB-tool skips, all executed tests
  and eight Java suites passed. Source privacy audit and diff checks passed.
  No product source or ROM image changed.

### Network ADB reset source audit, 2026-11-24

- After the authorized power cycle, the known device answered Ethernet probes,
  but TCP 5555 refused connections, ADB listed no device and no target wireless
  debugging service was advertised. No new Android boot-completion, uptime or
  slot evidence was obtained. Power was restored; the desktop VM stayed running.
- Native TV Settings project HEAD matches pinned
  `26fd224082c96fa32e0bfe60b288093c6e7522f3`. Its DevelopmentFragment, development
  XML and English Lineage strings each matched their pinned Git contents.
  The first writes temporary `service.adb.tcp.port` values 5555/-1; the XML
  requires main ADB enabled; the summary explicitly says reset on reboot.
- Added the normal-user reconnect route in DEBUGGING.md. This source finding
  identifies the intended reset behavior and next action; it does not prove
  the current device property value or a successfully completed UI flow.
- Source SHA256s, in that order:
  `70ba2d2967640bac5b25fac77d58fcfd9dc4c440c35c25fbcc0a1ba4dde2dc05`,
  `d130d8448c0d34a2406ddc812a184d8c5e4c334a19297fc060278ae50e4aa8f9`,
  `60fb37c61f9f66839e60f2042c9cc94b8e66cd1d731b87169d853bd51a251da4`.
  No persistent network listener, key copy, authentication change, flash, slot
  change, wipe or further reboot was performed.
- Validation: `tools/test-host.sh` ran 194 tests with five local AVB-tool skips;
  all executed tests and eight Java suites passed. Source privacy audit and
  `git diff --check` passed. This documentation does not change ROM behavior.

### Network debugging restored; complete Music compile, 2026-11-24

- The owner subsequently confirmed Android Home and enabled ADB over network
  through Developer options. The existing authorized connection returned;
  boot completion, slot A, cold boot reason and port 5555 were read back.
  Device uptime agreed with elapsed time since the authorized power cycle.
  Root debugging was then verified under the owner's standing authorization.
  No key was copied or release debugging default changed.
- Built the complete Music application from pinned revision
  `c119d5a52f80289c7f939746ddc31c8bcee2a3ca`, applying the previously documented
  session-cleanup patch in a private extracted source directory. Compiled all
  four Java sources, generated resources, dexed 19 classes and aligned the APK.
  This was a standalone build against SDK 34, not a native Soong/ROM build.
- The first build failed its package-metadata comparison: the SDK defaulted the
  compile/platform version name to UpsideDownCake instead of the native APK's
  14. Kept the comparison and supplied explicit compile SDK 34/name 14 values.
  The second run completed in 6.668 seconds; two independent empty output
  directories produced identical unsigned APKs, 778,619 bytes, SHA256
  `88d3c095c5b3c6fd5cba1a4006cf532b947e707e649872221ab30823e18f4ea4`.
  DEX SHA256 was
  `997233912011be31bf3a567f29270f006f02c245383dbe4654051eaac82208ca`.
- Package remained com.android.music, version 34/14, min API 19/target API 30.
  Preserved the upstream source and original native APK byte-for-byte. The job
  used a 768 MiB/no-swap limit; the desktop VM remained running. The candidate
  is unsigned and uninstalled; native image integration, Android lifecycle,
  Bluetooth browsing and playback tests remain open.

### ADB observer check and audible sleep onset, 2026-11-24

- Verified root ADB and the actual TCP peer; its socket had a roughly one-second
  keepalive timer. Recorded three 35-second connected/disconnected/connected
  sleep windows using a private tracefs instance and host wall-clock timing.
  There were 6/3/6 machine-suspend entries and Ethernet wake-source activations.
- The disconnected condition had three cycles before an unsolicited HDMI
  framework wake about 21 seconds into the window. That wake confounds a
  whole-window rate comparison. A header-only peer capture independently
  established no target TCP traffic for 34.005 seconds between close/reconnect,
  excluding an established ADB connection as a necessary cause of those cycles.
  The capture-window parser initially selected unrelated probe connections;
  preserved the bad summary and corrected it using exact phase receipts.
- All trace buffers had zero loss. Removed only the owned instance, verified
  global tracing unchanged/off/nop, restored Android awake with ADB connected.
  Network wake stayed enabled. No flash, slot change, reboot, wipe or desktop
  action occurred. The owner reports clicking immediately at sleep onset;
  stopped further sleep requests rather than claiming the sound is fixed.
- Added SUSPEND_AUDIO_INVESTIGATION.md with the evidence, confound and next
  driver qualification. A related public GPL driver matches the broad mute
  sequence, but is not verified source correspondence for the shipped module.
  No module patch or release image change is claimed.
- Validation: `tools/test-host.sh` ran 194 tests with five local AVB-tool skips;
  all executed tests and eight Java suites passed. Source privacy audit and
  `git diff --check` passed. Private captures and unsigned APKs remain outside
  the tracked source tree.

### Frozen image feature correspondence audit, 2026-11-24

- Root network ADB remained unavailable after the preceding diagnostic return
  request. Used the retained frozen vanilla build instead of claiming a fresh
  device inventory. Matched 15 selected files to signed target-files archive
  `b16c9d3bfbe0539dae01f328554718225525abeb43a2c238c9f16259bc92295f`,
  freshly rehashed that archive, and verified the three extracted filesystem
  data prefixes against the final delivery images. All five final image hashes
  matched the recorded packaging proof. This did not repeat complete AVB crypto,
  full image privacy, installation, hardware or rollback tests.
- Recorded file hashes, versions and these limited observations in the frozen
  feature receipt. Controls is 1.0/code 1; its ReplayFlags DEX method already
  branches on 26/231 and clears mask 1024 there. Corrected ledger wording that
  could imply that replay fix was still missing from f38. The separate native
  Power/Voice interception/fallback bridge remains unimplemented.
- Product keylayout bytes contain native Power/Voice mappings. The pinned
  frameworks/native source is unchanged at
  `9cb036fcafd5cf46ccafbb642f967993ad39393c`; its lookup checks product before
  system for the same basename. Both product and system mappings are present;
  this does not identify the live selected file or exclude version-specific
  configuration and vendor/odm candidates.
- Music's current DEX onDestroy is only return-void, so the later session-release
  candidate is not included. LineageSetupWizard requests BLUETOOTH_CONNECT;
  all four audio-policy engine libraries, TV SystemUI, the pinned animation and
  controlled launcher are present. Every animation part is interruptible `p`;
  no new boot-time measurement was made.
- The compiled 1.1 controls candidate has the same project signer as f38.
  Compared all DEX class names: generated R/R$xml exist only in f38 and a new
  controller-settings lambda only in the candidate; no other class is missing.
  This supports a future app-update test, not an install/behavior claim. Initial
  tool checks assumed SetupWizard.apk rather than LineageSetupWizard.apk, a host
  apksigner executable rather than the SDK JAR, and UTF-8-only dexdump output.
  Corrected those assumptions, retained the initial record and verified actual
  paths/raw output before drawing conclusions. No package was rebuilt, installed
  or re-signed in this audit; the desktop VM stayed running.
- Pinned the existing source supplement
  `225a2828d025ea9967d27ed2d0ee6455d555d395` in the frozen reproduction recipe,
  keeping it distinct from the frozen product-source commit.
- Validation: 194 host tests ran with five local AVB-tool skips; all executed
  tests, eight Java suites and the source privacy audit passed. The receipt
  parses as JSON and `git diff --check` passed. Full release qualification
  remains open.

### Signed Music cleanup candidate, 2026-11-24

- Verified the actual frozen Music APK's signature across API 19 through 34.
  It uses the project's release-app certificate, distinct from the controls
  app's platform role. Matched that certificate to the existing role inventory
  before signing the previously compiled standalone cleanup candidate. No key
  was exported, generated, changed or added to source control.
- The private signed candidate is 807,467 bytes, SHA256
  `478c9776d4879ecdc28d5fa9c20404ecca79f1c89028a8bbfcf673a69e678a7b`.
  Its v1/v2/v3 signatures verify across API 19 through 34 and its certificate
  matches frozen Music. All 181 non-signature ZIP files remain byte-identical
  to the unsigned input; four-byte alignment and package/version/SDK metadata
  checks passed. DEX hash remains
  `997233912011be31bf3a567f29270f006f02c245383dbe4654051eaac82208ca`.
- Inspected the signed DEX callback: a null guard precedes MediaSession.release,
  the session reference is cleared, and MediaBrowserService.onDestroy is called.
  This does not establish Android lifecycle correctness or a sleep/audio fix.
  Recorded scoped public evidence in `manifests/music-cleanup-candidate.json`;
  the APK and detailed tool outputs remain private.
- No APK was installed and no frozen archive, product image, original Music
  source or original APK changed. Soong integration, installed-signer/update
  checks, lifecycle, Bluetooth browsing and playback tests remain open.
- Validation: the public receipt matches the private artifact report and the
  tracked cleanup patch hash. JSON parsing, source privacy and whitespace checks
  passed; the prior host-suite result is unchanged because this checkpoint adds
  only documentation and a receipt.

## 2026-11-24 — Verified image integration for Controls and Music

- Compared the frozen signed feature inventory with the current patch series.
  All eight patch files apply to the pinned revisions. Eleven previously
  patched source files matched the frozen build tree, with the Music cleanup
  newly outside that baseline.
- Replaced Controls 1.0 with the pinned signed 1.1 APK in system_ext and
  inserted the matching signed Music cleanup APK in product. Verified both
  package identities, version codes, certificates and embedded DEX. Removed
  only the two stale ART files for each updated package.
- Re-extracted both rebuilt EROFS filesystems. All other file bytes, symlink
  targets and supported metadata matched. Preserved the system filesystem and
  checked the complete AVB chain with the existing key pins. Two bounded native
  runs produced the same five final image sizes and SHA-256 digests. Independent
  readback confirmed all ten files.
- Recorded the public metadata receipt in
  `manifests/f38-app-integration-rehearsal.json`. The images retain the frozen
  build identity and stay private. This is file-level integration evidence.
  Fresh full-source target-files, matching release ART precompilation, normal
  setup, Recovery, rollback and live feature validation remain required.
  Bazzite stayed running. No device writes or slot changes occurred.

## 2026-11-24 — Installed Recovery layout audit

- Matched the retained USB-Linux RAM image to its packaging report and UART
  trace. The owner confirmed physical-button navigation and Android reboot in
  the earlier RAM menu, then confirmed the SanDisk desktop from the updated
  menu. The USB-Linux RAM profile stops recovery ADB and uses a permissive
  domain for this experiment. Its hardware results are recorded independently
  of the installed-image work.
- Repacked the stock vendor-boot container offline with the independently
  reproduced ARM64 Recovery ramdisk. The repack retained the stock platform
  fragment, boot configuration and device tree. The unsigned result occupies
  26,707,968 bytes against a 67,108,864-byte reference limit. The stock generic
  archive contains two `dev` directory entries with equal metadata. The layout
  comparison collapsed the duplicate in memory and preserved the input bytes.
- The modeled replacement keeps stock first-stage ARM32 init and switches
  Recovery and ADB to ARM64. Both modeled vendor fragment orders resolve the
  Fastbootd init declaration but lack its executable. The pinned Fastbootd
  code also needs the boot-control service for A/B slot data. Stock declares
  that service and the vendor Fastboot HAL via AIDL. Following their ELF
  interpreters and transitive `DT_NEEDED` links within the stock ramdisk located
  21 and 30 ARM32 paths respectively. All are absent from the modeled ARM64
  replacement. Namespace, Binder and SELinux compatibility remain open, along
  with verified boot, USB authorization, hardware startup and restoration.
  No device changes were made.
- Tried adding the existing Fastbootd module in an isolated native checkout.
  The Soong graph generator repeatedly stalled on memory within the 4 GiB
  RAM and 2 GiB swap job limits. The previous successful graph generation
  peaked near 26 GB RSS. Stopped the private test before it emitted a ramdisk
  to keep Bazzite online. The original recovery image hash still matches.
- Retained the no-drive UART trace. It shows a 45-second SanDisk wait ending
  with Recovery still running. The later image confirmed direct-drive Linux
  startup with the revised USB role. Neither test covered installed Fastbootd.

## 2026-11-24 — Release patch coverage check

- Added `tools/verify-release-patches.py` to replay every tracked series in
  scratch against pinned project revisions. It checks the exact resulting
  files and executable bits in the proposed build tree. Unlisted patches,
  incorrect revisions and mismatched files fail the check.
- The frozen build tree failed with one expected mismatch in Music. A private
  checkout that applied the Music patch and referenced the same five other
  projects passed all six series, eight patches and twelve files. This verifies
  source coverage. The full build and final image audit are separate.
- The ROM host suite passed all 194 cases with the pinned AVB tool and all
  eight Java suites. Recovery's checkout passed its C++ checks and ran 86
  Python tests with seven AOSP-tool cases skipped on this host.
- Rehashed the private rehearsal `system_ext` image and extracted it again.
  `TvSettingsTwoPanel` and `LineageSetupWizard` matched their signed
  target-files copies byte for byte. Verified the AirPods update call in DEX,
  the Back-and-Home resources, and the Bluetooth connect permission in the
  compiled manifest. Handheld Settings is absent from the signed archive.
  Behavior during a fresh installation remains unverified.

## 2026-11-24 — Stock-compatible LCARS and source rebuild

- Started a private source build from `cb9334ee26ccd80d9f5e5d9276905440b93eaeba`.
  The source overlay contains the exact release device revision and the Music
  patch. The patch verifier accepted all eight patches in that build's mount
  namespace. The staged launcher and boot animation match their existing pins.
  The frozen Android tree and output are read-only inputs. This job uses a
  separate writable output overlay and a new unofficial build identity.
- Found the stock ARM32 `make_device` extension hook. The LineageOS 21 header
  probe produced larger `Device` and `ScreenRecoveryUI` vtables than stock.
  At AOSP revision `2e6ff7bc40063d38fc5478389a47c0fafba20bfd`, the sizes match
  stock at 64 and 308 bytes. Four comparable `Device` slots and 69 comparable
  screen slots also matched. [Pinned Android 14 Recovery source](https://android.googlesource.com/platform/bootable/recovery/+/2e6ff7bc40063d38fc5478389a47c0fafba20bfd/)
- The first factory activated the stock and custom libraries separately in
  Bionic, but its `ResetUI()` test failed: the stock Amlogic getter reads a
  separate member. Replaced that approach with an adapter that owns the
  original device and delegates stock actions while holding its own LCARS UI.
  An isolated ARM emulator verified the two factories, four stock menu labels
  and matching visible/hidden dispatch for seven keys. The fixture had no
  framebuffer, USB controller, linker configuration or device properties.
- Built and independently reproduced the ARM32 adapter and its unsigned
  vendor-boot repack. Both images are 27,183,104 bytes and share SHA-256
  `30625d390c1fdd10e4465619bbbd9f66df0ec48652f716ba80371e850fd58862`.
  The stock Recovery binary, Fastbootd, boot-control and vendor Fastboot AIDL
  services are among 481 byte-identical archive records. The original vendor
  plug-in is kept under a second path. The stock platform fragment, device tree
  and boot configuration also matched. Hardware startup, actual Fastbootd and
  AVB/rollback remain open. No Jarvis2 state changed. Bazzite stayed online.
- The ROM host suite passed 194 cases with the pinned AVB fixture and all eight
  Java suites. The source privacy and whitespace checks passed.

## 2026-11-24 — Publish the ARM32 Recovery prototype recipe

- Added the LCARS adapter and local stock image build recipe at Recovery
  source commit `1409c21924d1040024c9521749248e05d7f78315` on `recovery17-lcars`.
  The recipe verifies the original stock image and all four AOSP headers. It
  reuses the recovery archive readback and protected-fragment repacker.
- An initial CPIO mismatch was isolated to the inserted alias's inode. The
  corrected recipe includes the stock trailer's inode when allocating the
  alias. The regression test checks that case and exact metadata retention.
  All 84 Recovery Python tests, C++ tests and pinned packing fixtures passed.
- A fresh export of the committed source reproduced the exact plug-in and
  unsigned `30625d39` image. An unpinned stock input was rejected before
  creating output. Recovery CI passed. The image remains private and off-device.
- Added the stock-format `vendor_boot` hash footer and rehearsed the binding
  against the verified private f38 image set with an ephemeral root key.
  The protected leaf is 67,108,864 bytes, SHA-256
  `c9cc31121ee165b5cc45adc85af500589d34cf9cbb4a7b6bed499e3212c7d65e`.
  The new root binds the prototype and retains the other 28 descriptors and
  the baseline flags and rollback policy. Full signature, child-key and leaf
  checks passed. Substituting stock `vendor_boot` failed the new hash binding.
  The production key was unused and hardware acceptance remains open.
- The ROM host suite passed its 194 cases with pinned AVB and all eight Java
  suites. Bazzite stayed running. Both release ZIPs are still drafts.

## 2026-11-24 — Portable local Recovery and archive verification

- Recovery source `708e088ed57eb83805753d9213717965a3c61e2c` prepares a
  four-script, checksum-pinned tool kit. The local materializer takes the
  user's stock image and the reviewed plug-in. Linux `lz4` 1.10.0 reproduces
  the same output as the Android checkout's 1.9.4 tool. The complete 64 MiB
  leaf matched the independently generated AVB rehearsal image. A mismatched
  output hash produced no staging directory. A new native build from the
  committed source also reproduced the original plug-in and unsigned image.
- The packager's LCARS format binds the plug-in, stock input, derived image and
  recipe revision. Its five-image mode remains available for historical
  packages. Both private temporary-key rehearsal ZIPs contain 21 members and
  are 560,063,183 bytes, SHA-256
  `ad85d522b0e4edfbed2bde16fadb3ce9f40f6b6f55bd879743b752dbdca13384`.
  The archived plug-in recreated Recovery from local stock. The complete AVB
  check passed using the extracted ROM images and that reconstructed leaf.
  The ZIP carries the plug-in and manifest alongside the five ROM images.
- Recovery host checks passed 84 cases with pinned fixtures and the three
  native tests. ROM host checks passed 195 cases with pinned AVB and all eight
  Java suites. CI passed on the Recovery branch. The artifacts use the older
  private app rehearsal and temporary root key. Fresh production signing,
  installer qualification, hardware boot and redistribution review remain open.
  The native ROM source build is still running. Bazzite stayed online.

## 2026-11-24 — LCARS archive intake and saved rollback fit

- Added `tools/prepare-lcars-install.py`. It verifies the authenticated format
  2 ZIP, all member hashes, exact stock profile, pinned Git recipe and local
  Recovery reconstruction. It prepares five ROM inputs and two bootstrap
  inputs. The host check verifies four signed nodes, their parent/child keys,
  zero flags and 13 distinct image bindings, including the root `vendor_boot`
  hash. The tool exports no live authorization or capture-based approval.
- Ran the tool against the exact 560,063,183-byte LCARS archive. The normal
  path rejects the temporary-key archive. The explicit offline rehearsal
  produced all seven inputs, with both bootstrap images byte-identical to
  their reviewed references. The wrong-root pin was rejected before output.
  A targeted parser test verified that a missing root Recovery hash is refused.
- The existing slot planner accepted the saved matching slot-A LP views and
  exact sizes. Verified all seven historical rollback files against the pinned
  capture, and all untargeted stock reference hashes matched that capture.
  Slot B lacked a complete logical foundation in the saved data. The result
  covers offline fit and saved rollback bytes only. The 17 file-backed raw
  writer tests also passed. Jarvis2 was untouched and Bazzite stayed online.
- The ROM host suite passed 195 cases with pinned AVB and all eight Java tests.

## 2026-11-24 — LCARS compiler inputs and notices

- An instrumented relink reproduced the exact LCARS plug-in. The archive
  extraction trace recorded zero compiler-runtime members. The four stock
  shared libraries remain dynamic references. A dependency-recording compile
  reproduced the same source object and pinned all 156 inputs across five
  source revisions.
- Matched the Bionic, libc++ and Clang notices to the exact build sources,
  and fetched the AOSP Recovery notice at its verified header revision.
  Built the seven-member notice companion twice and read back every member.
  Both archives are 31,772 bytes and match the published notice receipt.
  The archive remains private pending final release-asset review.

## 2026-11-25 — Local Google composition with LCARS

- Exported the metadata profile from the exact f38 two-app rehearsal that
  includes Controls 1.1, the Music cleanup and the ARM32 LCARS binding. The
  profile SHA-256 is
  `cc2b8b86b96ead9fb13a5229d6ff3c9b2a26ff9650b46888b06fb955d30191b5`.
  Inputs matched the prior signed archive, five-image proof, Google download
  pin and derived Recovery image hash.
- The initial portable tool kit lacked `fec`, so assembly stopped on the first
  hashtree footer. Copied the matching executable and verified its hash. The
  corrected run passed with the stock FEC policy, 27 Google additions, 16 APK
  signature verifications, existing file and metadata checks and full offline
  verified boot. The portable preflight independently checked all 13 image
  bindings, including the root hash for the same derived `vendor_boot`.
- Both corrected runs produced five matching image hashes. Independently
  extracted the Controls and Music APKs from the composed EROFS images and
  matched both to their existing pins. The root Recovery descriptor is
  byte-identical to the baseline descriptor.
- Packed a private 777,819,197-byte rehearsal ZIP and read back all nine
  members. SHA-256 is
  `08c89caed4ef93896c49af94b83f702293fda71cca2fcc0cc31c5394ad60272e`.
  The archive includes the pinned LCARS plug-in and notices. The stock
  Recovery reference is supplied separately.
- Ran 195 Python and eight Java host tests. The rehearsal used disposable
  signing keys. Final-baseline installation, restore, hardware trust and
  distribution qualification remain open. Bazzite stayed online.

## 2026-11-25 — LCARS notices in the candidate ZIP

- LCARS format 3 binds the reviewed compiler-input notice archive to the
  exact plug-in and Recovery source revision. The packager and local preflight
  both verify that binding. Preflight preserves the notice archive in the
  output beside its verification receipt. Format 2 continues to read earlier
  archives with separate notices.
- Used the exact private f38 LCARS rehearsal images and matching notice bytes to
  produce two identical 22-member ZIPs. Each is 560,093,800 bytes with SHA-256
  `61454a9822fa3905f2e0945cb72551fd2eaebf267a5239529c786fe39f4bd9c7`.
  Ran portable preflight against the ZIP and locally sourced stock references.
  It reconstructed the expected Recovery image, prepared seven images,
  verified all 13 AVB bindings and copied the 31,772-byte notice archive
  with its pinned hash intact.
- All 197 Python tests and eight Java suites passed. The new cases exercise
  format 3, mismatched notice bytes and a notice pin paired with the wrong
  plug-in. The archive remains a private temporary-key rehearsal. Hardware and
  final-image qualification remain open. Bazzite stayed online.

## 2026-11-25 — Reproducible LCARS AVB assembly

- The public AVB assembler now accepts the independently pinned LCARS image
  alongside the verified stock templates. It verifies the original chain,
  checks the reconstructed leaf against the stock footer policy and binds
  the new hash in root `vbmeta`. The final audit checks the complete signed
  chain. The stock reference and local Recovery image remain separate inputs.
- Two native runs with the same f38 rehearsal payloads and disposable keys
  produced five matching ROM images. An independent readback matched all ten
  complete files and found all 13 expected AVB image bindings. Verification
  rejected substituting stock Recovery for LCARS with a `vendor_boot` digest
  mismatch. The private audit receipt SHA-256 is
  `3d07696945a01b1110bfb20879420c7756b1407c440473b81532b895a5e21600`.
- Passed all 198 Python tests and eight Java suites. The Recovery binding
  fixture rejects the wrong pin, missing root descriptor, changed salt and
  corrupt payload. Final release images, device trust and installation still
  require their own checks. Bazzite stayed online.

## 2026-11-25 — Bind final filesystems to signed target files

- The image inspector now optionally verifies the trusted signed target-files
  digest and byte-compares the complete EROFS prefixes of `system`,
  `system_ext` and `product` against the archive's embedded images. The receipt
  also retains the whole final-image hashes, which include the AVB data.
- The real f38 signed archive and its assembled final candidate matched across
  625,442,816 filesystem bytes. The same inspection refused the private LCARS
  rehearsal composed with different Controls and Music APKs when checked
  against that f38 archive. It stopped before creating an inspection output.
  Positive image-content receipt SHA-256 is
  `4cfc997235967dec92963962325e39ebba1745cf6e184105625470c29c49199b`.
- All 199 Python tests and eight Java suites passed. The exact new product
  build still needs its own signed archive and final-image binding. Device
  state was untouched and Bazzite stayed online.

## 2026-11-25 — Portable saved-layout and rollback-file verification

- LCARS preflight can now check a private saved capture using pinned native
  `lpdump`. The same offline operation verifies both LP views, fits the seven
  candidate files, checks the matching restore bytes and compares all untouched
  stock references. The receipt records the capture, prefix and tool hashes.
- Re-ran format 3 preflight against the exact saved slot-A trial. Both native
  LP views matched, seven candidate sizes and seven restore files matched,
  and all nine untouched stock references matched. Asking for B against the
  same saved capture failed for an incomplete logical foundation before preparing
  output. The private slot-A receipt SHA-256 is
  `1be60bb24087fcf04357592543a69e750204db02ebdafae93127fd6d389cc345`.
- All 200 Python tests and eight Java suites passed. The saved evidence covers
  offline fit and exact restore files. Recovery transport, fresh live state
  and actual restoration still need separate qualification. Bazzite stayed online.

## 2026-11-25 — Complete hosted draft asset readback

- Added an offline release-asset verifier for the existing receipt and checksum
  formats. It requires a trusted receipt hash and rejects extra, missing,
  changed or duplicate listed files. It reports exact bytes and digests.
- Downloaded all 11 files from the retained f38 draft and checked all
  1,059,715,684 bytes against the receipt and GitHub's asset records.
  Six payloads matched the earlier reviewed receipt. The three later payloads
  matched their separately recorded source supplement, launcher and animation
  pins. The private reconciliation receipt SHA-256 is
  `aa86fb67481c0af005c94171e3612d8ba5298983ab7c8b639c4f3560a5d5c271`.
- All 203 Python tests and eight Java suites passed. The older release remains
  a draft. The current candidate still needs its own audit and download check.

## 2026-11-25 — Current ROM target-files build completed

- The pinned product source `cb9334ee26ccd80d9f5e5d9276905440b93eaeba` finished
  all 218 native build steps in 58 minutes 30 seconds. All eight patches were
  present across six series and twelve checked files. The original wrapper
  looked for a versioned filename after the native build emitted the fixed
  `lineage_jarvis2-target_files.zip` name. Verified that archive independently.
- The fresh archive is 1,244,895,746 bytes with 6,131 entries. Archive SHA-256
  `802dfa5a8795499f87ae183cfc6fb6480d31849cb6b912884f9bb90a0cd9b428`.
  Whole-archive CRC, embedded build identity and source epoch, Controls 1.1,
  Music APK plus odex/vdex, TV Settings, SetupWizard, Bluetooth/ADB APEX entries,
  and pinned launcher and animation checks passed. Private readback receipt
  SHA-256 `38633a06724b8759daa92c1882c6d0bf4c31f7aec2a49b782ad7f4e92971ad1c`.
- The unused fallback stayed idle and the temporary build swap was removed.
  Signing metadata preparation started on the verified archive. Production
  signatures, final AVB, hardware and public release remain pending. Bazzite
  stayed online.

## 2026-11-25 — Current production-key image inclusion

- Signed the exact fresh build with the existing offline project keys.
  The 1,203,792,431-byte archive is pinned in the
  [candidate receipt](../manifests/current-cb9334-inclusion.json).
  Whole-archive CRC and source identity passed. Public-key verification passed
  for 103 standalone APKs, 31 APEX containers, 30 APEX payload signatures and
  23 embedded APKs. The preserved shim matched byte for byte. All 31 APEX native
  filesystem comparisons passed with zero unexpected differences.
- Built the final five AVB-bound images with the stock-compatible ARM32 LCARS
  binding. The signed archive and final images matched across all three full
  EROFS filesystem ranges and 21 selected readback members. The exact project
  system OTA certificate matched in the signed archive and the final image.
- The host suite passed all 203 Python tests and eight Java suites. The
  private images remain off-device. Hardware trust, installation, clean setup,
  recovery transport, rollback, artifact review and release packaging remain open.
  Bazzite stayed running.

- Packaged the private format 3 LCARS ZIP. An independent preflight read all
  22 entries, rebuilt the exact `vendor_boot`, verified all 13 AVB bindings
  and checked seven candidate sizes, seven restore files and nine untouched
  stock references against a saved slot-A capture. See the candidate receipt
  for the ZIP and preflight hashes. The capture is historical.
- Repeated the scoped userspace privacy scan on the three final filesystems,
  including 6,119 regular files and the 31 APEX payloads. All address matches
  were traced to upstream constants or examples. The three PEM header matches
  were format strings with no key body. No remaining findings in this scan.
  The ZIP remains private while licensing and hardware checks are open.

- Checked all 1,430 pinned source project HEADs using the selected build inputs.
  Only the twelve expected paths across the six patched projects had changes.
  Re-staged the eleven stock images in a fresh directory and matched the
  kernel bytes and extracted vendor/ODM contents and links. `fsck.erofs`
  reported timestamp-setting warnings on some links. The check did not compare
  timestamps or recreate the full ROM.
- Rechecked native EROFS metadata and found only the 137 approved package,
  build-tag, and public-trust content changes during signing, with zero
  unexpected metadata differences. Checked the exact allowlist, secure USB
  defaults, the launcher source archive's 445 payloads, and notices for the
  launcher, WebView and native tools. Runtime permissions and complete
  redistribution review remain open.
- Staged and independently checked all ten private delivery files. The
  [artifact receipt](CANDIDATE_PACKAGING.md#verify-the-complete-download-set)
  binds the matching ROM, source, notices and build inputs to their hashes.
- Finished the private Google composition against the exact current LCARS
  baseline. Two runs with temporary keys matched all five image hashes. The
  independent review verified 27 additions, 16 APK signatures, all 21 tracked
  unchanged feature files and all 13 AVB bindings. Read back all nine private
  ZIP entries. The public staging set is Google-free.
- Sampled the exact private animation and identified onn lettering and the
  LineageOS emblem. Record those marks in the artwork review before release.

## 2026-11-25 — Neutral artwork candidate

- Added an original interruptible boot animation to the existing preparation
  tool. Two host generations matched byte for byte. All 204 Python tests and
  eight Java suites passed.
- Derived two identical raw product images from the pinned signed build.
  Read back all 198 product filesystem metadata entries and all archive
  entries. The animation was the only product file change. The only final
  image changes were product and root `vbmeta`. The same AVB release key and
  LCARS binding passed independent verification.
- Verified all 22 ZIP entries, all 13 AVB bindings, seven saved slot-A target
  sizes, seven restore files, and the ten-file private delivery set. The
  [neutral receipt](../manifests/current-neutral-artwork.json) records the
  hashes. No live hardware checks took place. Bazzite stayed running.

## 2026-11-25 — Stock download and current USB baseline

- Downloaded the full Google-hosted `15640252` OTA and verified the archive,
  embedded payload hash, device and target build. The extractor reproduced
  the eleven stock references and the two `vbmeta` template inputs. The
  template copies match after the documented zero-padding step. Repeated
  the documented extraction in a fresh directory.
- Reconstructed LCARS and checked all 13 AVB bindings from the neutral ZIP
  using the downloaded stock files. It produced the same preflight receipt
  as the prior offline test, including the seven historical target sizes and
  restore files. [Stock input workflow](STOCK_FOUNDATION.md)
- Private neutral GApps composition reproduced all five images twice with
  disposable keys. Verified all 27 additions, 16 APK signatures, 21 unchanged
  feature files, and 13 AVB bindings. All nine private ZIP entries matched on
  readback.
- Read the currently booted Android over existing USB ADB. The box reported
  slot A, completed boot, enforcing SELinux, and the earlier `f38da52` ROM.
  Four of six selected installed packages already match the candidate. The
  Controls and Music APKs are the older builds. The neutral candidate still
  awaits a fresh device test. Bazzite stayed running.
- Reconstructed the seven-image stock rollback set from the same OTA. The
  full stock AVB chain and seven target sizes passed the saved slot-A check.
  Live recovery access and restoration remain untested for this candidate.

## 2026-11-25 — File-backed rollback and signer continuity

- Used the exact neutral ZIP inputs, seven saved restore files and native LP
  parser in the file-backed installer rehearsal. It restored the exact saved
  images after both an interrupted product write and a complete installation.
  It refused rollback while a writer was simulated as active. The protected
  metadata and partition fixture hashes matched throughout.
- Separately rebuilt and verified all 13 AVB bindings for the saved restore
  chain. The [rollback report](RESTORE_PLAN.md#exact-neutral-candidate-rollback-rehearsal)
  states what was simulated and which hardware checks remain.
- Compared the verified signatures on signed f38 and neutral cb9334. The
  126 APK signer sets, 31 APEX container signer sets, 30 verified APEX
  payload keys and system OTA certificate matched. Runtime userdata
  compatibility remains open. Bazzite stayed running.

## 2026-11-25 — Pinned preflight-to-writer handoff

- Added an offline [writer input staging command](CANDIDATE_INSTALLATION.md#stage-writer-inputs-from-a-pinned-review)
  that binds both proof files to the reviewed preflight, capture and slot.
  It rehashes all seven image inputs and independently reruns native LP and
  restore checks. The result records no device contact or installation approval.
- Exercised the command with the exact neutral candidate and saved capture.
  A mismatched review digest failed before creating output. Generated proofs
  also drove the file-backed installer dry run for all seven targets, with
  zero write requests. The offline confirmation uses simulated authorization
  evidence solely for the file-backed fixture. Live Recovery remains untested
  for the candidate. Bazzite stayed running.
- Repacked the operator tools as a source-only companion. Ran the extracted
  companion's tests and repeated the exact native handoff with identical proof
  files. Verified the refreshed private neutral delivery set with nine
  payloads and two metadata files.

### Neutral r2 release coverage — 2026-11-25

- Replayed eight source patches against the exact six-project build view.
  Twelve modified source files matched, and the output hash matches the
  original build receipt. Compared all 200 shipped product source files and
  their executable modes with the pinned Git revision.
- Read all 22 staged ZIP members. Extracted its three EROFS filesystems, bound
  their complete filesystem bytes to the derived target-files archive, and
  matched all 21 tracked payload files. The embedded Known Issues page still
  described the older stock Recovery trial, so r2 updates that page and its
  manifest record. All 20 other payload members matched the prior ZIP.
- Repeated the complete r2 LCARS preflight using the matching stock OTA.
  All 13 AVB bindings and seven prepared images matched, including the
  reconstructed LCARS image. Native checks matched the saved A fit and seven
  restore inputs. The r2 ZIP has a new hash, so archive-bound writer reviews
  must reference the r2 preflight explicitly.
- Staged all 69 files from the matching public LCARS source revision in a
  source archive. Tested an extracted copy with pinned host tools. All 84
  Python tests and the Recovery C++ host checks passed. The ROM project
  passed 209 Python checks with AVB fixtures and eight Java suites.
- Verified the complete 13-file staging set. The
  [r2 coverage receipt](../manifests/neutral-r2-release-coverage.json)
  pins the candidate, source coverage, binary readback and Recovery source.
  The [neutral delivery receipt](../manifests/current-neutral-artwork.json)
  records the matching private staging hash. Hardware installation, data
  migration, physical rollback and distribution review remain open.

### Release patch and feature readback — 2026-11-25

- Replayed every ROM patch in the read-only Beercan build view, including the
  captured Music checkout. All eight patches across six projects matched the
  twelve resulting source files. The report reproduced SHA-256
  `a26cb736826c379589538a3156aa8b122a1511f8fd8cbcb99df6284556a39da2`.
  The current product source and the pinned candidate have the same patch,
  app, overlay, keylayout and device configuration files.
- Rehashed all 15 staged delivery files, compared 200 product and 69 LCARS
  source files with their pinned Git revisions, read all 22 entries in the
  vanilla ZIP and freshly extracted its three EROFS filesystems. All 21
  tracked feature files and the three signed target-files filesystem bindings
  matched. Read all nine entries in the private GApps rehearsal and extracted
  its corresponding three filesystems. The same 21 feature hashes and LCARS
  plug-in and notices matched there too.
- Confirmed the build identity, authenticated ADB and lock-screen default
  in the extracted properties. Checked the Controls APK's shortcut,
  button editor, AirPods, audio delay, launcher and Smart Home classes.
  Updated the [feature inventory](PERSISTENT_FEATURES.md#release-candidate-inclusion)
  with exact image locations and the remaining development features.
- The host suite passed all 221 Python checks with AVB fixtures and eight
  Java suites. The audit ran on the build hosts without a device session.

### Exact r2 package reproduction — 2026-11-25

- Recovered the original [image-proof bytes](../manifests/neutral-r2-packaging-proof.json)
  bound by the r2 ZIP. Verified the archived product source and packaging tool
  hashes and extracted them into a fresh workspace. Used the committed
  `152b5da` Known Issues blob, the reviewed LCARS inputs and the standalone
  signed images. The staged release ZIP was used only for output comparison.
- The independently staged run reproduced the 547,469,604-byte archive with
  all 22 entries. The ZIP, manifest and verification receipt matched the
  original bytes using Python 3.13.5 and zlib 1.3.1.
  [Packaging recipe](CANDIDATE_PACKAGING.md#reproduce-the-staged-neutral-r2-zip)
- Host checks passed with AVB fixtures (221 Python and eight Java suites).
  This rehearsal fixes a missing packaging input in the published source
  record. Clean image compilation and hardware tests remain open.

### Exact r2 verified-boot states during install and restore — 2026-11-25

- Rehashed the fixed r2 and saved restore inputs. Independently verified four
  authenticated metadata nodes and 13 leaf bindings per state using the
  pinned avbtool. The complete saved and r2 endpoints passed. All 126 mixed
  combinations of whole images failed.
- The ordered install and restore traces failed at the same steps. Userspace
  mismatch begins with the first write. The root's bootstrap checks fail after
  changing `init_boot_a` and then `vendor_boot_a`. Before the final root write,
  the previous root also rejects the replacement `vbmeta_system_a` key.
- The [state receipt](../manifests/neutral-r2-avb-intermediate-states.json) and
  [test target](DEVICE.md#developer-preview-test-target) document those
  boundaries. Whether the actual bootloader still reaches Recovery or
  Fastboot after an interruption remains unverified.

### Exact r2 interruption and Recovery helper check — 2026-11-25

- Ran the extracted staged operator installer against exact r2 and historical
  restore images, native LP metadata and a host-only backing model. After
  a dry run with zero writes, interrupted each target once during its write,
  including the boot and verified-boot images. Each of the seven cases
  exercised a genuinely mixed image, refused an active writer and directly
  restored the full old set once quiescent. All 56 model write requests stayed
  in A, with the protected prefix and the 16 physical and five logical
  fixtures unchanged.
- Freshly extracted ARM32 `dmctl` from the r2 system image and matched its
  exact digest to the previous development Recovery run. Verified the linker,
  six direct library paths and all 117 required dynamic symbols against
  the reconstructed LCARS Recovery payload. This was a static check.
- The [matrix and helper receipt](../manifests/neutral-r2-rollback-matrix.json)
  records the inputs and results. Host tests passed with AVB fixtures
  (221 Python and eight Java suites). Physical power interruption, re-entry
  and restoration remain open.

### Exact r2 VNDK import history — 2026-11-25

- Fetched the complete eight-commit history of the original Google snapshot
  and checked the 120 ARM shared libraries against the exact signed r2 APEX
  readback. The current bytes first appeared in three imports. Build
  10185551 accounts for 115 libraries, 10357257 for one and 10951026 for four.
- Matched all 120 installed library paths to generated Blueprint rules.
  Of the 109 explicit module rules, three carry GPL-family identifiers.
  Those three libraries match build 10185551. The remaining 11 libraries
  inherit the snapshot-wide license metadata. Raw CI manifest requests for
  all four historical VNDK imports returned HTTP 404.
- Re-extracted system, system_ext and product from the verified official
  stock OTA. Compared all 120 ARM libraries in stock
  `com.android.vndk.current.apex` by size and SHA-256, including the nested
  `lib/hw` path. All relative paths match. The Clang UBSan runtime matches
  byte for byte. The other 119 differ.
- The [VNDK history receipt](../manifests/neutral-r2-vndk-history.json)
  records the public imports, exact matched members and stock APEX identity.
  The staged r2 ZIP is unchanged. Completing source correspondence and
  verifying hardware remain open.

### Clean WebView prebuilt checkout — 2026-11-25

- Reproduced the initial clean ROM sync failure in the ARM WebView prebuilt
  project alone. Repo had installed a local skip-smudge filter that invokes
  Git LFS. The host lacked that executable.
- Extracted the verified Debian Git LFS 3.6.1 package into the isolated job
  workspace. The same local sync then checked out WebView Git revision
  `1c11dffe87310d3c81e2ad93b9f0a7e8c09adfc0`. A repository-local LFS
  install and pull resolved the 133-byte pointer to the 98,528,166-byte APK,
  matching SHA-256 `f7ccf01cf3ec8555fd4500ddc7512430cb2cd3cadd1806a166be2092d25c7298`.
- The interrupted sync also left five empty Git metadata directories across
  the ARM64 and x86 WebView projects. Preserved those incomplete directories
  outside the checkout and verified all three repaired project revisions.
  Resumed the original workspace with the existing objects and separate
  fetch and checkout phases. The queued compiler requires the verified
  WebView APK receipt. The full clean compile remains open.

### Exact neutral r2 stock-file boundary — 2026-11-25

- Compared 14 pinned stock partition images, 996 regular files from seven
  stock filesystems, 312 stock ramdisk files, the GKI kernel and boot metadata
  against the exact r2 ROM. Independently read all 30 files from the two
  ext-family stock inputs by native inode and verified the extracted bytes.
- Bound the check to each of the five released image hashes and all 31 APEX
  archive hashes. Read 22 ROM ZIP members, 5,354 regular userspace files,
  765 APEX files and 49,278 nested ZIP members. The scan found three
  whole-file matches with stock and classified all three.
- Compared the two configuration matches with pinned Git source. The third
  match was a single newline shared by generated VNDK metadata and an ODM
  placeholder. The actual OEM Dolby library and firmware had no whole-file
  match. See the [scoped receipt](../manifests/neutral-r2-stock-boundary.json).
- Host checks passed with AVB fixtures (221 Python and eight Java suites).
  The audit ran without device access and left the ROM ZIP unchanged.
  Remaining userspace source and distribution review is tracked in
  [Licensing](LICENSING.md#stock-file-boundary-in-neutral-r2).

### Latest staged r2 release audit and recipient preflight — 2026-11-25

- Replayed all eight ROM patches with the current source and the captured
  build inputs, and reproduced the exact 12-file patch report. The patch,
  app, overlay, keylayout and product configuration still match the r2
  product revision.
- Verified the current 18-file private delivery and compared all 200 product
  source files and 69 Recovery source files with their pinned commits.
  Rechecked all 22 ROM archive entries, the three signed filesystem bindings
  and all 21 tracked feature files. The nine-entry private GApps rehearsal
  still contains the same tracked feature files and LCARS payload.
- Extracted the verified operator archive and verified 13 stock inputs from
  the pinned OTA. Fetched the pinned LCARS source and four host scripts in a
  fresh workspace. LZ4 1.10.0 and 1.9.4 reproduced the same seven images,
  notices and reports with all 13 AVB bindings passing both times.
  [Recipient preflight](../manifests/neutral-r2-recipient-preflight.json)
  matches the prepared images from the earlier saved-layout rehearsal.
- Host checks passed with AVB fixtures (221 Python and eight Java suites).
  All steps ran on build hosts. Physical installation, first boot and
  rollback of this ZIP remain open.

### Portable native partition-layout reader — 2026-11-25

- Matched the installed Linux x86-64 lpdump and its 11 Android shared libraries
  byte for byte to the pinned Android host build. Verified the ELF dependency
  closure and the host's glibc and libgcc dependencies. The runtime uses the
  adjacent lib64 directory.
- Replayed 36 Soong license metadata nodes for the 12 ELF outputs. Bundled
  the generated Notice and bill of materials, 16 tracked notice or source
  attribution inputs including the Clang runtime notices, and
  [16 pinned checkout revisions](../manifests/lpdump-host-source.json).
- Two archives of the reviewed files matched byte for byte. The extracted
  archive passed all 33 internal checksums on Linux x86-64 with glibc 2.41.
  Both saved metadata views produced the same JSON and text as the reviewed
  original. With an empty environment and no custom library path, the
  extracted tool reproduced the exact neutral r2 preflight receipt.
- Verified all 14 files in the new private delivery. The
  [neutral receipt](../manifests/current-neutral-artwork.json) pins the
  host archive, executable and notice graph. The ROM ZIP hash stays the same.
  The check used saved metadata and contacted no device. Production device
  installation, actual recovery transport and rollback remain separate gates.
- The project host suite passed 209 Python checks with AVB fixtures and eight
  Java suites.

### Read-only Recovery inspection command — 2026-11-25

- Added a separate host CLI to inspect an already connected USB Recovery
  session. It pins ADB and lpdump, checks the selected device and settled
  Recovery state, reads a bounded 1 MiB super metadata prefix, and repeats the
  identity, geometry and snapshot observations before writing the report.
  The inspector does not produce writer proofs, restore files or a capture
  that can be used to install.
- The previous saved layout exposed metadata slot count three and first
  logical sector 2048. Native lpdump reads from the new 1 MiB prefix produced
  the same two views as the old 4 MiB capture.
- Exercised the actual CLI with an isolated ADB protocol fixture driven by the
  saved layout and the portable native lpdump. The matched layout was stable.
  Unmounted metadata and a persisted OTA entry remained unverified. An
  unprivileged session read zero partition bytes. The truncated case left no
  report. Live Recovery transport still requires separate authorization and
  verification.
- The refreshed operator source archive includes the inspector, writer and
  preflight code and their tests. All 29 extracted-companion tests passed.
  Its CLI matched the expected observations on five simulated transport
  cases with the actual saved native layout and reproduced the same r2
  offline writer inputs. Verified all 14 staged files. The full host suite
  passed 216 Python tests and eight Java suites.

### Read-only seven-image rollback backup — 2026-11-25

- Added a host command for an explicitly chosen slot in an already qualified
  Recovery session. It reuses the Recovery inspector, validates the physical
  parent disk and ranges, requires the reviewed dmctl hash, and reads the exact
  native logical extent order directly from super. It saves only the seven
  target images and hashes the full required physical and allocated logical
  inventories. Before publishing, it independently reads those hashes again,
  checks old image sizes and content, and revalidates Recovery and the layout.
- Host regressions cover logical extent order with reversed physical offsets,
  short or changed partition reads, overlapping physical geometry, unexpected
  snapshot state and an invalid dmctl pin. The full suite passed 221 Python
  checks and eight Java suites.
- Ran the actual CLI using a file-backed transport, the portable lpdump and
  the exact saved r2 layout. All seven restore files were byte-identical to
  the historical rollback originals. Fed the generated capture to the exact
  r2 preflight and verified all seven target fits, seven restore files, nine
  unchanged stock references and 13 AVB bindings. An offline fixture review
  then produced paired writer inputs with zero partition write requests.
  File model only. Live capture, hardware installation and rollback remain open.
- The operator companion now includes the exact backup command. All 34 tests
  passed from its extracted source. Verified all 14 staged delivery files.
  See the private delivery record in the
  [neutral receipt](../manifests/current-neutral-artwork.json).

### Native userspace source companion — 2026-11-25

- Read the exact build's Android module-installed inventory for 18 selected
  native source projects. Their 1,112 installed paths matched the staged r2
  filesystem copies, including symlink targets. Matched all 16,085 archive
  members to the pinned Git blob bytes and executable/symlink modes. Exported
  zstd's stored blobs directly to preserve bytes where Git export applies CRLF
  conversion.
- Re-read the r2 NOTICE files, WebView APK and native library and extracted
  the exact embedded Credits. The Chromium FFmpeg archive independently
  reconstructed the pinned Git tree with 11,351 files and its matching
  CREDITS.chromium. The LineageOS WebView patch snapshot matched all 13
  expected patches and its build README.
- Two outer source companions reproduced byte for byte. Verified all 24
  members including 20 source archives, and all 15 files in the new staging
  set. The [neutral receipt](../manifests/current-neutral-artwork.json) pins
  the result. A full WebView rebuild and relink, remaining dependency source
  coverage and stock-input rights remain open.

### ARM32 WebView build preparation — 2026-11-25

- Checked out the full Chromium source at the pinned 157.0.8103.78 commit
  and matched its Git tree and DEPS digest. Fetched the DEPS-pinned
  depot_tools and started the Android dependency sync with hooks disabled.
  The [WebView rebuild record](WEBVIEW_REBUILD.md) describes the exact inputs.
- Replayed the 13 LineageOS patches using pinned Chromium source bytes.
  Compared all 100 original text files and 47 paths absent upstream to the
  checked-out Git tree. Found the five Chromium icon source paths and checked
  every destination against the patched GN file. The historical README uses
  outdated icon directories and an enable_nacl argument absent from this tree.
- Compared the complete prebuilt and staged r2 APK payloads. The only
  non-signature difference is the omitted Crashpad trampoline. The main ARM32
  WebView library and all other 641 payloads match. Four exact Chromium icon
  densities reproduce the prebuilt pixel data. The fifth referenced by patch
  0002 is absent from the prebuilt's icon table, so the documented patch series
  does not establish the exact original build steps. Full dependency sync,
  ARM32 rebuild and modified-FFmpeg relink remain open.

### ARM32 WebView graph and profile pins — 2026-11-25

- Completed the Chromium Android dependency sync and repeated
  `gclient revinfo -a` with PGO enabled. All 304 records matched byte for
  byte. Published the [dependency list](../manifests/webview-r2-deps.txt)
  and [GN arguments](../manifests/webview-r2.args.gn) used by the build.
- Installed Chromium's prerequisites inside a separate Debian 13 root.
  Verified the architecture-independent Linux headers after the installer
  flagged the i386 alias. Initialized the pinned depot_tools wrappers.
  GN 2595 verified all arguments and generated 66,382 targets from 4,759
  files. The PGO-enabled hooks fetched both Android AFDO profiles and the
  Android ARM32 profile data. Their hashes are in the
  [rebuild receipt](../manifests/webview-r2-rebuild.json).
- Confirmed Siso entered offline compilation for the ARM32 WebView APK.
  Matched an FFmpeg error message in the shipped ARM ELF to the pinned
  `libavutil/error.c` source and its compile rule. Checked that a one-line
  diagnostic patch applies to that revision. The diagnostic build is
  pending the baseline APK and will compare the two ELF payloads. The
  staged ROM still uses the pinned r2 prebuilt.

### Neutral r2 APEX source provenance — 2026-11-25

- Rehashed the exact original and signed target-files archives. Read all 31
  APEX and CAPEX members, and matched each original archive member to the
  binary produced by its Soong license metadata root. Independently
  rehashed the extracted r2 packages and matched all 31 to the signed bytes.
- Ran AOSP's `compliance_listshare` on those roots. All 260 resolved source
  project paths map to pinned revisions. The annotated graph found direct
  source-sharing conditions on 1,603 modules across 28 projects, including
  build-time dependencies. The combined Soong consistency check returned
  `PASS`. The [APEX receipt](../manifests/neutral-r2-apex-sources.json) pins
  the tools, metadata and package hashes.
- Matched all 120 regular ARM shared libraries in VNDK v34 to the Android
  prebuilt tree. Mapped the snapshot indexes to 114 source module paths.
  The original import names build 10951026 and branch `udc-gsi-release`.
  The exact historical source manifest remains open.
- Matched `libmainlinecronet.121.0.6103.2.so` inside the signed tethering APEX
  to its Soong output from `external/cronet`. Exported all 45,638 tracked
  files and checked every archive member's Git blob and mode. Staged the
  verified source archive and the APEX index alongside the private candidate.
  This work used existing build artifacts and source outside the device.

### Neutral r2 APEX notice companion — 2026-11-25

- Generated text and XML notices from the 31 artifact-matched Soong roots
  and a separate VNDK v34 set. Compared all notice text hashes and path names
  to the three extracted partition notice archives. The partition XML was
  missing exact copies of 55 of 229 APEX notice texts and 731 of 734
  generated paths. The VNDK subset has nine missing exact texts and all
  120 library paths are absent from the installed XML.
- Verified all five supplement members. Multiple deterministic packaging
  passes reproduced the same archive SHA-256. Rehashed the refreshed
  18-file private staging set. The five ROM images, Recovery plug-in
  and ROM ZIP had no changes. See the [notice receipt](../manifests/neutral-r2-apex-notices.json).
- The Android CI raw artifact URL for build 10951026, target `vndk`,
  returned 404 for the original manifest. The notice comparison and
  supplement do not establish the exact corresponding VNDK source revisions.

### Fresh neutral builder preflight — 2026-11-25

- Initialized a blank Repo workspace directly from the public Jarvis2 source
  commit and its pinned manifest. Repo v2.73 listed the exact 1,430 paths.
  Synced Music and Lineage's vendor project from their public remotes,
  compared both HEADs with the manifest, and verified the Music patch applies.
- Re-extracted all 13 selected images from the pinned OTA. Verified the
  eleven staged stock images, padded AVB templates and kernel. Compared
  content, modes and symlink targets for all 1,065 vendor and ODM entries
  against the earlier extraction. EROFS reported symlink timestamp warnings,
  so timestamps are outside this comparison.
- Ran the frozen launcher helper using the pinned SDK and JDK. Its six
  outputs include the authenticated launcher APK, three ARM libraries and
  two notice files. Removed the temporary zipalign bootstrap link.
  Generated the neutral animation directly from source. Both the APK and
  animation matched their r2 product copies byte for byte.
- The updated [neutral build guide](CURRENT_REPRODUCTION.md) describes the
  public manifest and staging process. The [preflight receipt](../manifests/neutral-r2-builder-preflight.json)
  pins the evidence. This run did not compile a full ROM or contact hardware.

### Neutral r2 static security defaults — 2026-11-25

- Verified eight canonical userspace properties from r2, including secure USB
  ADB, default TCP port `-1`, and privilege-allowlist enforcement. Checked
  the single project OTA certificate and the absence of persistent network
  and root ADB overrides in those property files.
- Inspected the exact Controls APK with the pinned SDK aapt2. Requested
  permissions and activity exports matched source. The accessibility service
  requires the binding permission, the button editor is private, backup is
  disabled, and the package does not request microphone access. Verified the
  three allowlist grants in the extracted system extension.
- The [static receipt](../manifests/neutral-r2-static-security.json) binds
  these checks to the earlier exact r2 image readback. Fresh-boot behavior,
  SELinux enforcement and user activation remain device tests.

### Neutral r2 image privacy readback — 2026-11-25

- Repeated the bounded scan on the exact three neutral r2 userspace
  filesystems. Verified each of the 31 APEX package hashes before scanning
  native payload bytes and symlinks. Scanned 6,119 regular files,
  49,278 ZIP entries and supported compressed resources with zero scan gaps.
- The 30 matches had the same categories, counts and paths as the earlier
  reviewed build. Independently rehashed all 14 enclosing files across
  both variants. Their bytes matched, including the contexts for the
  network examples and key-format strings. The
  [receipt](../manifests/neutral-r2-privacy-scan.json) carries no matched
  values. Final hosted asset review remains open.

### Neutral r2 patch and feature recheck — 2026-11-25

- Reverified all 18 staged files, the 200-file product archive and 69-file
  LCARS source archive. Matched the archived patch hashes to all eight tracked
  patches and the six replayed series. Independently checked the contents
  of the 22-entry vanilla and nine-entry private ZIPs, including all 21
  tracked feature files per variant and the LCARS binding.
- Read back the landscape capability and Controls 1.1 code, including
  Accessibility setup, input replay, AirPods wear state, audio routing,
  widgets and Smart Home. Compared the legacy Controls project with the ROM
  source. Its Java files are either identical or superseded by the release
  code for input replay and shortcut setup.
- Verified 126 vanilla APK package IDs across the three filesystems and 31
  APEX containers. The private composition added exactly its 27 pinned
  files and 15 parent directories. None of its 16 APK digests or IDs matched
  vanilla. Traced the two Google-prefixed IDs already in vanilla to code-free
  LineageOS compatibility overlays. [Inclusion recheck](../manifests/neutral-r2-inclusion-recheck.json)
- The ARM64 USB Linux menu, temporary suspend workaround and early UART
  diagnostics retain their development status. Bazzite stayed running.
  This recheck used existing artifacts and did not access Jarvis2.
- The source host suite passed 221 Python tests, eight Java suites and the
  repository privacy audit.

### Neutral r2 public signing companion — 2026-11-25

- Parsed each of 78 public keys and 47 X.509 certificates from the staged
  public signing export. Matched the certificate fingerprints, public keys
  and package roles to the independently pinned signing inventory. Re-encoded
  the 31 AVB blobs with the pinned tool and matched the r2 root fingerprint.
  The 157 ZIP members exactly matched the expected inventory, with no extra
  files. [Public export receipt](../manifests/neutral-r2-public-signing-export.json)

### Neutral r2 staged download review — 2026-11-25

- Rehashed all 18 assets against the independently pinned receipt and read
  234,153 inner archive entries. The owner path, domain, device ID and
  selected credential token patterns had no matches. Key-pattern matches
  appeared only in the pinned launcher, Cronet and native source companions.
  Rehashed the launcher and native carrier archives against their independent
  source inventories and matched the Cronet archive to its Git tree receipt.
- Recorded 52 bounded or unreadable upstream fixture entries with source
  identities. Independently decoded and scanned the gzip Flutter notice
  payload. [Companion review](../manifests/neutral-r2-companion-privacy.json)
  This was a local artifact review. Bazzite stayed running and Jarvis2
  was untouched. Review the hosted files after release staging.

### Neutral r2 build identity — 2026-11-25

- Traced mixed userspace identities to the original incremental target-files
  archive. The saved Ninja graph tracks the build-number file for system
  buildinfo. The product and system extension build-property rules read the
  same number and date but omit both file dependencies. Their generated files
  in r2 still identify `f38da52`. The target-files signing step and AVB
  descriptors preserve that identity.
- Added an expected-build check to the extracted-image inspector. The
  regression reproduced the false pass before the change. The real staged r2
  images now fail on six properties, and the archived coherent f38 control
  passes using its own expected build. This scopes the release hold to a
  replacement rebuilt with verified identities. [Identity receipt](../manifests/neutral-r2-build-identity.json)
- Verified the exact APK inventory lacks LineageOS Updater and the r2 ZIP
  lacks an OTA payload. Read the declared system and stock patch levels.
  No device contact or signing changes.

### Neutral r2 recipient preflight on Debian 12 — 2026-11-25

- Bootstrapped Debian 12 x86-64 from the signed Debian archive. In an
  isolated, offline environment, verified all 18 staged downloads and 33
  layout-reader companion checksums. Extracted 13 stock OTA inputs on that
  host and reproduced the two zero-padded AVB templates.
- The native layout reader initially failed to resolve `libbase.so` in the
  bare chroot. A controlled comparison reproduced the failure before mounting
  `/proc`. With only that mount added, the same binary and libraries reproduced
  the saved layout output exactly.
- Repeated the complete recipient preflight from fresh output directories.
  All seven candidate and restore checks and 13 AVB bindings passed. The
  incomplete saved slot B foundation was refused before staging. The Debian
  12 reports matched Debian 13 byte for byte. No device was accessed and
  Bazzite stayed running. [Debian 12 receipt](../manifests/neutral-r2-bookworm-preflight.json)

### Numbered-build dependency fix — 2026-11-25

- Ran the pinned Android Make rules with native Kati and Ninja. On the
  original rules, changing the build number refreshed system buildinfo and
  left the system extension and product identities stale.
- Added the number and date prerequisites for numbered builds. The replay
  now updates all three properties when the number changes and when the date
  alone changes. Fresh fixture output matched the original byte for byte.
  An unchanged numbered build had no work, and the existing unnumbered
  incremental policy was preserved.
- Replayed all nine patches against six pinned projects and compared 13
  affected files. Omitting the new patch raised the expected `core/sysprop.mk`
  mismatch. The existing clean ROM run retains its original eight-patch pin
  and has a separate output identity check. The new patch has native fixture
  evidence and awaits a full build. [Replay receipt](../manifests/release-build-property-replay.json)

### Reproducible build dates — 2026-11-25

- Replayed the real Android date-formatting rules at the same epoch with
  UTC and Hawaii time. The native outputs differed in exactly four
  human-readable date properties. The UTC epoch and build identities agreed.
- Pinned UTC and the C locale in the release recipe and native verifier.
  The full property files matched byte for byte across the two caller
  environments with those settings. The running clean build uses a Debian
  root configured for UTC and the default C locale. The historical f38
  recipe keeps its observed HST date format. This is property-level
  reproducibility evidence. [Environment receipt](../manifests/release-build-environment-replay.json)

### VNDK v34 source candidates — 2026-11-25

- Matched all 281 exported headers for `libexif`, `libnl` and `libxml2` from
  the original 10185551 import and the current r2 snapshot. Each matched
  Android 14 r1 source tree is identical to the public release and GSI
  branch trees for that project. Verified the extracted ELF digests
  against the exact signed r2 APEX inventory.
- Read `xmlParserVersion` directly through the ELF symbol and compared it
  with the source version macros. The later r67 `libxml2` headers differ.
  The later `libnl` build list adds an address module despite identical
  headers, and the r2 binary lacks its tested address symbol.
- Reproduced three source archives, checked all 4,739 Git entries and verified
  the private staging copy. The original CI inputs and exact binary rebuilds
  remain open. [Source candidate receipt](../manifests/neutral-r2-vndk-source-candidates.json)

### Successor patch and payload coverage — 2026-11-25

- Revalidated all 18 staged r2 files, the eight archived source patches and
  the 21 tracked feature files in both ZIPs. The vanilla filesystems match
  all three signed target-files filesystem digests, and the private GApps
  rehearsal retains the same feature files and Recovery binding.
- Ran the nine-patch verifier again against six pinned projects and 13
  modified source files. The report matched the recorded SHA-256, and
  native Kati and Ninja passed the numbered-build regression checks.
- Queued the full rebuild at the [nine-patch product pin](CURRENT_REPRODUCTION.md#build-sign-and-package)
  after the initial clean build and archive check. It preserves the baseline
  archive, verifies the ninth patch before the Android build, and reads back
  the new archive's 21 feature paths, three image members and three build
  identities. A 21-path fixture passed, and the same check rejected a stale
  product identity. Actual rebuilt and signed image checks remain open.

### Source attribution for the 11 default-rule VNDK modules — 2026-11-25

- Matched all 11 ARM ELF digests and sizes to the signed r2 APEX inventory.
  Their public module paths agree between the 10185551 import and r2. The
  AOSP Android 14 r1 source reproduces all ten frozen AIDL API hashes. It
  accounts for 119 generated C++ paths and 357 headers. Six binary stubs
  carry the expected interface hash. Four modules expose no such method.
- Compared the later pinned ROM source. Nine complete frozen API trees
  match the r1 candidates. Graphics common V4 changes the sign of
  `VENDOR_MASK` and appends a second API hash. Both snapshot exports
  contain the older value.
- Matched the bufferqueue helper's three exported headers to the r1 Git
  source. The binary defines BufferQueueProducer and GraphicBufferSource
  symbols. The vendor Blueprint declares a static GUI dependency.
- Verified the published-source Apache 2.0 license text in the staged VNDK
  XML and its attachment to every one of the 11 library paths. Exact CI
  inputs, binary rebuilds and complete dependency license scope remain
  open. [Module attribution receipt](../manifests/neutral-r2-vndk-default-license-sources.json)

### WebView icon filtering and relink handoff — 2026-11-25

- Verified that all five PNGs in the ARM build's icon resource ZIP match the
  pinned source inputs. Replayed the generated Ninja rule's filter through
  Chromium's actual resource predicates. It removes exactly the 640 dpi
  icon from that ZIP.
- Linked both icon sets with the pinned AAPT2 and the build's SDK 29/36
  parameters. The filtered link matches the exact r2 APK's four density
  configurations. The unfiltered control includes the fifth. Two independent
  runs reproduced both test APKs and the receipt byte for byte.
  [Icon filter evidence](../manifests/webview-r2-icon-filter.json)
- Queued the FFmpeg relink behind the exact WebView baseline invocation.
  The supervisor confirms a successful exit and verifies the saved artifact
  digests before comparing every APK entry to r2. On the pinned LineageOS
  control it reproduced the one Crashpad trampoline difference and matching
  native WebView payload. The live baseline and relink still await output.

### Launcher ARMv7 SQLite source rebuild — 2026-11-25

- Extracted the recipe and SQLite 3.50.3 amalgamation from the exact r2
  source companion. Verified the two input hashes, the Android NDK r27c
  archive and the compiler identity from the shipped ARMv7 ELF. The Maven,
  signed r2 launcher APK and extracted JNI library bytes match.
- Rebuilt with CMake and Ninja against NDK r27c and Android API 21.
  After stripping, all 1,408,528 bytes outside the GNU build-ID
  descriptor match the published library in all four builds.
- The two standard builds used fresh source and build paths and
  produced different IDs. Fixing the debug paths yielded identical
  stripped and unstripped ELF files across two more independent runs.
  Maven's original build ID differs. The ROM and source companion were
  used as read-only references. [SQLite replay receipt](../manifests/launcher-sqlite-rebuild.json)

### Readback from the generated images before signing — 2026-11-25

- Verified the exact original unsigned cb9334 target-files archive and the
  signed neutral r2 archive. In each archive all 21 feature files and the
  three canonical build property files match their extracted EROFS copies.
  Both artifacts have the same six stale identity fields in system_ext and
  product, so those values were present before signing.
- Created a test archive with three real EROFS images containing the
  tracked package files and coherent test properties. The independent
  readback passed all 24 file comparisons. A second archive changed the
  landscape declaration while retaining all three image bytes and was
  rejected on that file.
- Queued the readback on PVE behind the exact nine-patch build invocation.
  It verifies the patch receipt, the archive and all three generated image
  hashes, then compares the files extracted from the images. Actual
  successor output remains pending.
  [Readback controls](../manifests/successor-image-readback-controls.json)

### Flutter engine and launcher Dart AOT replay — 2026-11-25

- Fetched the two official engine-addressed artifacts. The ARMv7 runtime
  JAR and Linux `gen_snapshot` match the preserved controlled-build tools.
  The official runtime matches the packaged and extracted r2 `libflutter.so`.
- Replayed the exact Flutter 3.24.5 ARMv7 AOT flags twice on Beercan with
  the preserved kernel input. Both outputs match the complete `libapp.so`
  in the unsigned and signed APKs and r2's extracted JNI library.
- Compared the compiler depfile to the build stamp and the saved Flutter
  file cache. All 1,588 Dart cache hashes matched when recomputed with
  the pinned Flutter code. Standard MD5 disagreed on 207 files whose final
  block contained 56–63 bytes. The reproducer uses Flutter's routine.
- Matched 1,587 source files across 65 pinned archives in the r2 launcher
  companion. The remaining input is the generated plug-in registrant,
  whose hash matched the cache. Both saved kernel intermediates are
  identical. An independent Dart frontend run and a native engine rebuild
  remain open. [Flutter replay receipt](../manifests/launcher-flutter-aot-replay.json)

### Launcher source-to-kernel build — 2026-11-25

- Staged 140 checksum-pinned input archives, including all 137 application
  Pub archives, in a clean canonical workspace. Reused the pinned Flutter
  SDK and provisioned the 69 extra packages required by its tool cache.
  Pub resolved the app offline with the original lockfile unchanged.
- Rebuilt the plug-in registrant and Dart kernel using the Flutter
  `kernel_snapshot` target. Both match the preserved bytes, and the
  compiler read the same 1,588 source paths. The 143 original package
  records match. Flutter emitted one additional and unused synthetic
  localization entry in the regenerated configuration.
- Transferred the newly compiled kernel to Beercan and ran the pinned
  offline ARMv7 AOT compiler. The result matches the complete shipped
  `libapp.so` byte for byte. The native engine remains a pinned upstream
  artifact. [Frontend rebuild receipt](../manifests/launcher-flutter-frontend-rebuild.json)

### Launcher DataStore protobuf rebuild — 2026-11-25

- Verified the published Maven binaries against the exact raw protobuf input
  and the selected launcher runtime dependency. Replaying the AndroidX
  relocation on the raw binary matched the entire published 1.1.3 JAR.
- Compiled all 159 Java files from the pinned source companion with Temurin
  11.0.25+9. Shadow 8.1.1 under Gradle 8.7-rc-1 relocated the 523 compiled
  classes in an isolated offline workspace. All 529 archive entries and the
  complete JAR matched the launcher dependency byte for byte. The commands
  from the published recipe repeated the match in a second fresh directory.
  [Rebuild receipt](../manifests/launcher-protobuf-rebuild.json)

### Flutter ARMv7 native build preflight — 2026-11-25

- Verified the exact engine revision's `DEPS` and Linux ARMv7 release builder.
  Expanded the Linux/Android checkout with gclient and the nested Vulkan
  dependencies. All 43 staged native archives map to selected revisions.
  Rehashed every archive from the staged source companion.
- Resolved immutable package IDs for all 14 enabled CIPD downloads. Read the
  original r2 launcher's ELF header, NDK note and compiler/linker comments as
  a reference for the planned build comparison.
- Started the pinned dependency checkout. The graph generation and offline
  native build wait for checkout verification. The selected checkout includes
  test and tool inputs, so its coverage is distinct from the final link.
  [Preflight receipt](../manifests/launcher-flutter-native-preflight.json)

### VNDK libexif replay — 2026-11-25

- The retained Soong plan reproduced the modern system `libexif.so` as a
  control. It uses the same 12 C files as the staged Android 14 source
  archive. Two isolated Clang 17 builds from separate extractions reproduced
  the VNDK library outside its 16-byte GNU build ID, after restoring the
  historical link layout and shrink wrapping.
- Matched all 97,116 bytes outside the GNU note descriptor, including
  the 115 named exports and 64 named mini debug functions. Added the exact
  source archive to an independent 19-file private staging set and verified
  every download byte against its receipt.
  [Rebuild receipt](../manifests/neutral-r2-vndk-libexif-rebuild.json)

### VNDK libnl and libxml2 replay — 2026-11-25

- Reproduced both modern system ELF controls from the retained Soong plans.
  Rebuilt the historical VNDK variants with Clang 17 and the same 64 KiB
  layout and shrink-wrap settings used for libexif. The libnl replay needed
  the older Bionic headers and 36 historical inputs. The libxml2 replay
  needed the VNDK variant flag and 39 historical inputs.
- Compared the complete stripped libraries. Only the 16-byte GNU build ID
  per library differs. Repeated builds from fresh source extractions and
  matched both output files. Added the exact source archives to the
  independent private staging set and verified all 21 files.
  [Rebuild receipt](../manifests/neutral-r2-vndk-libnl-libxml2-rebuild.json)

- Added the exact Android 14 Bionic tree used by the `libnl` replay. Two
  independent Git exports produced the same gzip archive. Verified every
  tracked blob and mode, then recompiled the 36 files with includes from
  the extracted archive. The result matched both earlier `libnl` libraries
  outside the 16-byte GNU build ID. Reverified the new 22-file staging set
  and confirmed all 19 previous payloads still match their receipts. Host
  verification passed 222 Python tests with the pinned AVB fixture and all
  eight Java suites.

### Expanded source delivery privacy review — 2026-11-25

- Rehashed all 22 private staged files. All 16 payloads covered by the
  earlier recursive scan matched their previous hashes. Scanned the four
  added source archives and refreshed metadata. The scan read 8,273 files
  and 20 link targets and found no owner-specific values or decode gaps
  in the additions.
- Both new key findings came from the public AOSP Bionic tree. The runtime
  APEX development payload key matches its upstream AVB public key, and the
  container key matches its upstream certificate. Neither public key
  matched any of the 78 keys in the release signing export. The broader
  scan retains the 52 earlier upstream fixture limitations.
  [Companion review](../manifests/neutral-r2-companion-privacy.json)
- Host verification passed 222 Python tests with the pinned AVB fixture
  and all eight Java suites.

### Neutral r2 split SELinux policy replay — 2026-11-25

- Rehashed and re-extracted `system`, `system_ext`, `product` and the
  pinned stock `vendor` and `odm` images. All three policy identifiers
  differ from the stock precompiled image. Replayed the pinned init
  compiler command with vendor mapping 34.0 and verified three matching
  outputs. The host policy reader requires its pinned libc++ and MLS mode.
- The binary analysis found `su` and `backuptool` permissive in r2 and zero
  permissive domains in the stock policy. Expanded the original policy
  macro with both variant values. The two declarations are present in
  `userdebug` and absent in `user`. Separate strict compilation reported
  53 assertion failures. The exact candidate has yet to boot for runtime
  enforcement and the complete `user` variant is unbuilt.
  [SELinux receipt](../manifests/neutral-r2-selinux-replay.json)

- Replayed six Soong commands for `system`, `system_ext` and `product`
  policy under both variant values. The three `userdebug` outputs exactly
  match the r2 filesystems. Replacing those three files with the `user`
  outputs in the separate boot-policy replay produced identical binaries
  on two runs, both with zero permissive domains. The same strict mode
  that reported 53 assertions in r2 still reports 25. These are host
  policy checks. The full variant and hardware checks remain open.

- Verified and extracted all three stock platform images from the pinned
  OTA. Replayed the same compiler with seven stock CIL inputs. Stock
  passed with strict assertions enabled. With the same retained vendor
  inputs, the mixed `user` replay reports 25 assertions. All three stock
  identifiers match ODM, consistent with normal stock boot using its
  precompiled policy. The replay shares 45,550 decoded statement lines
  with that binary. The shipped binary contains one additional allow
  statement. [SELinux receipt](../manifests/neutral-r2-selinux-replay.json)

### Flutter ARMv7 link graph — 2026-11-25

- GN completed with the same local ARMv7 release arguments after staging
  pinned Debian pkgconf 1.8.1 for the host sysroot queries. The target uses
  NDK r26b, Android API 21 and LTO. Ninja is compiling the library.
- Mapped the 3,046 direct object inputs using GN's compile database and
  Ninja's additional assembly commands. Verified 2,994 unique source paths
  against their pinned Git trees across 16 staged source projects. The
  other 52 inputs are generated. Static archive and generated-source
  readback, discovered header coverage and the ELF comparison remain open.
  [Graph receipt](../manifests/launcher-flutter-native-preflight.json)

- Queried the six static libraries with pinned Ninja and verified the
  archive rule uses explicit inputs. All 78 planned archive members match
  compile database outputs. Verified 77 source paths in the exact Git
  trees of the five projects, all with staged archives. The remaining
  member uses a generated Dart version source. Archive bytes and the
  complete library are still building.

- Matched 53 generated inputs to their Ninja rules and verified all 987
  declared source paths in 12 staged Git projects. Dart's checkout reflog
  is the only declared input outside those trees and the build output.
  Two isolated reflogs at the pinned Dart revision and shallow boundary
  reproduce the build's exact 1,018-byte version source.
- Read back the first completed Expat and skcms archives. Their five
  member names, order and contents match the pinned Ninja graph and the
  compiled objects. The other archives, generated payloads and final
  library still need complete readback.

- Replayed the exact ICU assembly generation and assembled the output
  independently with the pinned command. The object data equals the
  778,864-byte pinned ICU blob and its little-endian size. Read back the
  blob from the staged source companion and from the reference ELF.
  Compiled archive readback expanded to four archives and 50 members,
  including libjpeg and libsimd. Final library and two archives remain open.

- Completed archive readback after FreeType and the precompiled Dart
  runtime finished. All 78 members across six libraries matched the
  names and order in the Ninja graph and the exact compiled object bytes.
  Recorded archive digests in the native preflight manifest. The final
  linked engine and compiler-discovered headers still need verification.

- Scoped actual Ninja compiler dependency records to 3,124 Android ARMv7
  link and archive objects. The first 2,649 compiled records cover 6,299
  tracked paths across 21 staged source archives and five generated paths.
  All scoped assembly, C and C++ rules declare GCC-style dependency files.
- Replayed the ARMv7 toolchain link without Flutter objects or project
  archives. The exact compiler, linker, NDK revision and two package
  instances were checked. The LLD replay archive contained eight NDK
  shared libraries, two startup files, one builtins archive and the pinned
  Flutter export script. All input digests matched and the scratch ELF
  reproduced byte for byte. Complete link and dependency audits are pending.
