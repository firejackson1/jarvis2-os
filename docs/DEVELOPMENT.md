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
