# Jarvis2 public release checklist

Updated: 2026-11-25. Working checklist for continued development.

## Operating rules

- Keep slot B untouched. No partition flashing, slot switching, factory resets, or public release without the owner's authorization for that action.
- Keep Bazzite running under the current release goal. Use bounded build jobs and offload independent work; earlier temporary-shutdown permission does not override this current requirement.
- Prefer offline builds and reversible app/RAM tests. Explain any reboot or hardware interruption before testing.
- Keep private signing keys, accounts, ADB keys, server addresses, paired-device IDs and runtime preferences out of public artifacts.
- Preserve the owner's current development settings; secure defaults apply to release images, not silently to this device.
- Complete items only with recorded evidence. Distinguish host tests, live device tests and human verification.
- For each change record files, build identity, checks, limitations and rollback. Maintain this checklist and the shared private operations notes.

## Unofficial build policy — owner decision, 2026-11-23

We are maintaining an unofficial LineageOS-based Jarvis2 build. Official device
submission/certification is not a release goal at this stage. Do not present
LineageOS official-device acceptance requirements as mandatory for our unofficial
release; component licenses, accurate attribution and redistribution rights still
apply independently.

- [ ] Label release pages, filenames/release metadata and build identity clearly as unofficial and LineageOS-based; do not imply LineageOS endorsement or official support.
- [ ] Preserve applicable copyright, license and NOTICE files, credits and modification notices.
- [ ] Provide the exact corresponding source/build material required by each distributed copyleft component, including the kernel; do not assume publishing only our patches is sufficient.
- [x] Match the retained core kernel byte-for-byte to Google's GKI build 14657224 and pin its 20-project manifest; see KERNEL_SOURCE_PROVENANCE.md. Vendor-module correspondence and complete required source/build delivery remain open.
- [x] Verify and stage the 18 selected native source trees and the two WebView
  source inputs against r2. The rest of the ROM source and rights review stays
  open. [Userspace source review](USERSPACE_NOTICES.md#selected-native-source-materials-for-neutral-r2)
- [x] Match all 31 r2 APEX packages to their build license metadata and pin
  the resolved project list and VNDK v34 prebuilt library origins.
  [APEX source inventory](USERSPACE_NOTICES.md#apex-source-and-license-inventory-for-neutral-r2)
- [x] Match Cronet in the tethering APEX to its source-built ARM library and
  verify and stage the pinned Cronet source tree.
- [x] Regenerate, verify and stage the APEX and VNDK notice companion for
  the missing texts and paths in the r2 partition notice archives.
  [APEX notices](USERSPACE_NOTICES.md#apex-notice-companion)
- [ ] Verify the exact source revisions of the historic VNDK v34 builds and
  complete the APEX corresponding-source and redistribution review.
- [x] Trace all 120 r2 VNDK libraries to their byte-identical public snapshot
  imports, identify the module licensing rules and compare the local stock
  OTA's VNDK payload. [VNDK import history](USERSPACE_NOTICES.md#vndk-v34-import-history)
- [x] Match 281 VNDK headers to three pinned candidate source trees and
  verify their staged source archives. Exact CI source correspondence and
  rebuilt library byte equality remain open.
  [VNDK source candidates](USERSPACE_NOTICES.md#source-candidates-for-three-vndk-libraries)
- [x] Reproduce VNDK `libexif` from its staged sources outside the original
  GNU build ID. Repeat from a fresh extraction and stage the verified source
  alongside the ROM.
  [VNDK libexif evidence](USERSPACE_NOTICES.md#reproducing-the-vndk-libexif-library)
- [x] Reproduce VNDK `libnl` and `libxml2` from their staged sources
  outside their original GNU build IDs. Repeat both from fresh extractions
  and add their source archives and the pinned Bionic headers to the
  private delivery. Verify the `libnl` replay from the staged Bionic archive.
  [VNDK libnl and libxml2 evidence](USERSPACE_NOTICES.md#reproducing-the-vndk-libnl-and-libxml2-libraries)
- [x] Trace the 11 VNDK libraries that use the snapshot's default license
  rule back to their source declarations and check their delivered Apache
  notice attachments. [VNDK module attribution](USERSPACE_NOTICES.md#vndk-modules-using-the-snapshot-default)
- [x] Check out Chromium at the pinned r2 commit, replay every documented
  WebView patch against its exact inputs, and compare the prebuilt with the
  staged r2 APK. [WebView rebuild evidence](WEBVIEW_REBUILD.md)
- [x] Finish the Android source and tool sync, fetch the pinned optimization
  profiles, and validate the ARM32 WebView build graph.
- [x] Reconcile the WebView icon densities by replaying Chromium's real
  filter and linking the filtered and unfiltered icons with pinned AAPT2.
  [Icon filter receipt](../manifests/webview-r2-icon-filter.json)
- [ ] Finish the ARM32 WebView build, compare the complete APK with r2
  and verify an FFmpeg source relink.
- [ ] Review redistribution rights for proprietary firmware, vendor blobs, codecs, Google apps and bundled launchers before packaging them. Existing device installation is not evidence of redistribution permission.
- [x] Compare the exact neutral r2 ROM with the pinned stock bootloader,
  kernel, vendor/ODM/OEM files, module files and ramdisks. Trace the three
  whole-file matches to platform source and the newline placeholder.
  [Stock-file boundary](LICENSING.md#stock-file-boundary-in-neutral-r2)
- [ ] Keep Google applications out of public ROM bundles unless distribution is properly licensed; document separately installed optional components.
- [x] Verify that the exact vanilla r2 images exclude all 27 MindTheGapps
  additions, including the 16 APKs, by comparing extracted files and package
  IDs. [Package boundary](GOOGLE_APPS.md#neutral-r2-package-boundary)
- [ ] Use our own private signing keys and update channel; document known issues, tested hardware and our own support/bug-report destination.
- [ ] Keep official LineageOS branding/endorsement claims out of promotional material; review any upstream artwork/marks before release.

References: https://source.android.com/docs/setup/contribute/licenses ;
https://github.com/LineageOS/lineage_wiki/blob/main/pages/gapps.md .
These checks are pending audits, not a declaration that the current artifacts
already satisfy all distribution requirements. Nothing is authorized for public
publication by this policy decision alone.

## 1. Capture and reproduce the current working state — next

- [ ] Inventory installed APK versions/hashes, ROM fingerprints, active slot, RAM mounts, modules and live settings using read-only checks.
- [ ] Identify every feature supplied by app updates/RAM patches rather than the booted ROM.
- [ ] Map installed features to source, dependencies, licenses and reproducible build commands.
- [ ] Preserve a coherent baseline and rollback artifacts on the build host; verify backups by hash.
- [x] Choose the public source repository and exclude private/runtime/build artifacts before any publication. `firejackson1/jarvis2-os` is public after clean working tree, full-history privacy audit and passing CI at `1ac457e`. Binary publication remains pending hardware and recovery qualification.
- [ ] Complete reboot/default-switch/stability testing for optional launchers on Jarvis2 (ARM32 compatibility, cold launch, D-pad/Home, Settings integration, stability). Prefer an existing open-source base over extending the proprietary launcher; retain current home until a replacement passes testing.
  References: https://gitlab.com/flauncher/flauncher and https://github.com/leanbitlab-org/LtvLauncher . LTvLauncher advertises GPL-3.0, widgets and an OLED-friendly screensaver; this is research, not a hardware compatibility claim.

## 2. Integrate the complete candidate offline

- [ ] Consolidate device-tree/product configuration and persistent fixes in source.
- [x] Run [the full patch check](BUILD.md#verify-source-patches-without-modifying-the-android-tree) on the current release build checkout. Eight patches across six series and twelve files passed. Keep the report pin in the [candidate receipt](../manifests/current-cb9334-inclusion.json).
- [x] Match the [release inclusion ledger](PERSISTENT_FEATURES.md#release-candidate-inclusion) to the current signed archive and final images. Record the separately pinned Recovery build and AVB binding.
- [x] Recheck every shipped patch and the 21 tracked payload files from the
  staged neutral ZIP, add the matching LCARS source archive and correct the
  embedded release notes. See the [r2 coverage inventory](../manifests/neutral-r2-release-coverage.json).
- [x] Rehash every patch in the staged product source tarball and confirm all
  21 tracked payloads in both the vanilla r2 ZIP and the private GApps rehearsal.
  Check the landscape declaration and Controls 1.1 onboarding in the actual
  packaged files. [Inclusion recheck](../manifests/neutral-r2-inclusion-recheck.json)
- [x] Check the 1,430 upstream project pins, the twelve modified source files
  and the exact local build inputs. Record the
  [current reproduction procedure](CURRENT_REPRODUCTION.md).
- [x] Initialize the exact public manifest in a fresh Repo workspace and
  rehearse the neutral builder's stock OTA, launcher, and generated animation
  inputs. [Builder preflight](../manifests/neutral-r2-builder-preflight.json)
- [ ] Qualify experimental and hardware-dependent changes before listing them as release features.
- [x] Include Controls 1.1, the TV Settings overlay and the native Bluetooth Settings hook in the signed candidate.
- [x] Port the AirPods Bluetooth-page hook into Java source for normal ROM builds; source patch and rebuilt TvSettingsTwoPanel compile passed. Fresh-image behavior remains a separate test.
- [x] Include the four required audio policy libraries and the Bluetooth compatibility patch in the signed candidate.
- [ ] Resolve HAL, DTS and codec integration and redistribution requirements.
- [ ] Integrate verified USB/ADB defaults, remote keylayout, animation and TV UI changes; distinguish experiments from production fixes.
- [ ] Fix launcher/lock-screen/notification behavior in product configuration rather than relying on leftover device state.
- [ ] Rebuild the complete slot A candidate; compare all partition budgets, EROFS metadata, AVB descriptors, keys and rollback indexes offline.
- [ ] Verify the fresh build number, UTC build epoch and fingerprint component
  in all three generated and signed userspace filesystems. The existing r2
  artifact holds older generated identities in `system_ext` and `product`.
  [Identity receipt](../manifests/neutral-r2-build-identity.json)
- [x] Trace the missing dependencies and verify the incremental build-property
  fix with the pinned native Kati and Ninja. Fresh release image verification
  remains required. [Build-property patch](../patches/ReleaseTools/README.md)
- [ ] Rebuild from the nine-patch successor pin, verify all 21 tracked payloads
  and the three partition identities in the unsigned archive, and repeat the
  signed-image and ZIP readback before publication.
  [Successor build pin](CURRENT_REPRODUCTION.md#build-sign-and-package)
- [x] Verify the archive-to-EROFS readback on the older artifacts and
  exercise it with matching and mismatched test archives. The check is
  queued for the actual unsigned successor.
  [Readback controls](../manifests/successor-image-readback-controls.json)
- [x] Record the artifact hashes and [feature-to-image inventory](PERSISTENT_FEATURES.md#release-candidate-inclusion)
  for neutral r2. Compare the exact staged ZIP and private GApps rehearsal
  against all 21 tracked feature files. Recheck coverage after each rebuild.
- [x] Bind 15 selected frozen-f38 feature payloads to the pinned signed archive and final filesystem data, recording versions and later update gaps in `manifests/frozen-f38-feature-evidence.json`. This receipt covers the older vanilla baseline, not a newly integrated candidate or every release feature.
- [x] Verify all three complete f38 release filesystems against their signed
  target-files archive and reject the independently mixed image set.
  [Image inspection](BUILD.md#inspect-the-generated-images-themselves)

## 3. Release security and privacy

- [ ] Audit source and final extracted images for owner-specific values and unintended secrets.
- [x] Scan the exact neutral r2 userspace images and all 31 APEX payloads.
  Match each finding to an earlier reviewed, byte-identical file.
  [Privacy scan receipt](../manifests/neutral-r2-privacy-scan.json)
- [x] Read back the r2 userspace debugging and trust properties, the sole
  OTA public certificate, and the Controls manifest and privilege allowlist.
  [Static security receipt](../manifests/neutral-r2-static-security.json)
- [x] Verify the exact staged public signing export against the signed package
  audit. Parse every public key and certificate, re-encode every AVB blob,
  and reject unexpected ZIP members. [Public export receipt](../manifests/neutral-r2-public-signing-export.json)
- [x] Rehash and scan the 18 neutral r2 staged downloads. Match the key-pattern
  findings and undecoded upstream test fixtures to the pinned source inputs.
  Hosted asset review remains open. [Companion review](../manifests/neutral-r2-companion-privacy.json)
- [x] Verify the new 22-file set against the prior 16 payloads and scan all
  four added source archives plus the refreshed receipt and checksum list.
  Confirm the Bionic development keys match AOSP and differ from every
  key in the public release signing export.
  [Expanded staging review](../manifests/neutral-r2-companion-privacy.json)
- [ ] Use private release signing keys with a tested backup process; do not publish keys or ship development keys unknowingly.
- [x] Generate the private key set and verify an encrypted off-host backup, including archive identity and all 204 archived files. Keys have been used in private package/APEX and launcher signing rehearsals; final image signing and hardware acceptance remain open.
- [ ] Make root debugging and unauthenticated network ADB opt-in in public builds; retain normal USB authorization by default.
- [ ] Verify enforcing SELinux, app privilege allowlists, exported components and microphone permissions.
- [x] Replay the r2 split policy with stock vendor and ODM offline. Identify
  both permissive domains and record strict compiler results.
  [SELinux receipt](../manifests/neutral-r2-selinux-replay.json)
- [x] Regenerate the three `user` policy files from the retained build rules.
  Verify zero permissive domains after combining them with stock inputs
  and record the 25 remaining strict assertion failures.
- [x] Replay the strict compiler on the exact stock OTA policy as a control.
  Confirm zero stock assertion failures and compare the shipped precompiled
  policy with the stock replay.
- [ ] Evaluate the full `user` variant, repeat the policy check on its exact
  images and review the strict assertion failures before hardware validation.
- [ ] Ensure first-run setup uses each user's own accounts, Bluetooth devices and Smart Home provider.
- [ ] Add and test remote-shortcut service activation in first-run/Settings without ADB or an AI. The clean f38 trial included the app but left its accessibility service disabled; owner-verified side panels returned after enabling it. Never bake in an owner's service list.
- [x] Add exact-service status and Enable/Manage activation entry to controller-settings source; compile and verify the private signed 1.1 app. This does not complete the preceding installation and normal-user UI test.
- [ ] Check update/install compatibility and document which data is shared between slots.

## 4. Stability and hardware validation

- [ ] Diagnose and fix genuine suspend/wake and repeated speaker clicking; test repeated sleep/wake cycles and recovery after failure.
  Evidence and current limitations: [suspend/audio investigation](SUSPEND_AUDIO_INVESTIGATION.md).
- [x] Bind the current drivers and document the unwanted speaker-unmute path with two controlled, loss-free traces and a restored temporary mixer test. This does not complete the genuine suspend/wake or audible validation gate.
- [ ] Test Ethernet, Wi-Fi, Bluetooth reconnect and network transitions across reboot.
- [ ] Test direct USB and hub: storage, keyboard, mouse, controller and device/host role changes.
- [ ] Test fresh remote pairing, reconnect, Home/Back/Settings/Power, remapping and long/double presses.
- [ ] Test Xbox layout with real hardware; untested controller diagrams are not proof of support.
- [ ] Test HDMI resolution changes, 1080p/4K layouts, CEC, playback stability and audio switching.
- [ ] Run an extended idle/playback test with logs for crashes, ANRs, memory pressure, audio and thermal issues.

## 5. Audio and AirPods

- [ ] Re-test PCM, built-in speaker, HDMI and Bluetooth after integration; verify output selection and volume.
- [ ] Verify dual output, saved per-device delay, manual adjustment and automatic estimates after reconnect/reboot.
- [ ] Validate TrueHD/Atmos and DTS-HD/DTS:X with a compatible receiver and source files. Capability reporting and synthetic tests alone do not prove bit-perfect playback.
- [ ] Test ordinary AC3/EAC3/DTS and unsupported-format fallback.
- [ ] Verify AirPods pause/resume after a clean install, including manual-pause cancellation, seeking, disconnect and competing sessions.
- [ ] Resolve or clearly label unconfirmed Conversation Awareness/ducking and untested noise modes.
- [ ] Ensure the AirPods shortcut works with other users' devices; document the present name-based detection limitation.

## 6. Smart Home

- [ ] Test a compatible assistant provider on this ARM32 Android TV build with a new user's own account/server.
- [ ] Verify a complete command/reply flow and remote-button launch.
- [ ] Verify built-in and remote microphone paths independently; do not advertise remote capture until tested.
- [ ] Test microphone permissions, listening indication, cancellation and privacy behavior.
- [ ] Treat wake words, release-to-stop push-to-talk, voice-specific routing and playback ducking as separate features requiring implementation/verification.
- [ ] Document that the current Smart Home page is provider setup/shortcuts, not yet a verified voice satellite.

## 7. Installation and recovery — requires a separately authorized device test

- [x] Document the exact model, firmware base, bootloader prerequisites and
  supported partition layout. [Developer-preview test target](DEVICE.md#developer-preview-test-target)
- [x] Download the exact [stock OTA](STOCK_FOUNDATION.md), verify all thirteen
  extracted inputs against the pinned stock profile, and repeat the neutral
  LCARS preflight with those files.
- [x] Reconstruct the seven [stock rollback inputs](RESTORE_PLAN.md#stock-rollback-input-rehearsal)
  and verify the entire stock AVB chain and saved slot-A fit offline.
- [x] Exercise the exact neutral candidate's dry run, interrupted-write restore
  and complete install/restore in a
  [file-backed rehearsal](RESTORE_PLAN.md#exact-neutral-candidate-rollback-rehearsal).
  Recovery transport and physical rollback remain separate hardware checks.
- [x] Interrupt all seven r2 target writes individually and directly restore
  the saved file-backed state. Verify the protected ranges in every case.
  [r2 interruption matrix](RESTORE_PLAN.md#interrupted-writes-on-all-seven-r2-targets)
- [x] Generate the paired writer proofs from a
  [pinned transition review](CANDIDATE_INSTALLATION.md#stage-writer-inputs-from-a-pinned-review)
  and consume them in the exact candidate's file-backed dry run.
- [ ] Validate candidate against read-only live partition metadata and snapshot status before installation.
- [x] Verify the host Recovery inspector against saved native layout data and
  simulated read-only USB responses. The live session test remains pending.
  [Recovery inspection](CANDIDATE_INSTALLATION.md#inspect-an-existing-recovery-session)
- [x] Rehearse the seven-image Recovery backup and native fit using the
  file-backed layout. Fresh capture and physical rollback remain open.
  [Recovery backup](CANDIDATE_INSTALLATION.md#back-up-an-existing-qualified-recovery-session)
- [ ] Preserve and verify stock restore files, current recovery and necessary signing information.
- [ ] Test a RAM candidate where possible before requesting persistent installation.
- [x] Confirm the custom RAM menu on HDMI, physical-button navigation, Reboot
  system now back into Android, and Boot Linux from USB to the SanDisk desktop.
  Installed Recovery remains a separate gate. See the [layout and Fastbootd audit](PERSISTENT_FEATURES.md#installed-recovery-audit).
- [ ] Obtain authorization for the exact slot A installation plan; never infer permission to modify slot B.
- [ ] Test first boot/clean setup and upgrades using a suitable test device/data plan; do not wipe the owner's device automatically.
- [ ] Verify recovery entry, USB ADB/fastbootd, Android reboot and stock restoration paths.
- [x] Document the exact verified-boot failures between writes and what
  remains unverified before Recovery. [Intermediate states](RESTORE_PLAN.md#verified-boot-between-writes)
- [ ] Verify and document which recovery entry points remain reachable if a
  failure happens before Recovery starts.
- [ ] Test rollback and repeat installation from the published instructions.

## 8. Public developer preview

- [ ] Publish buildable source, patch provenance, license notices and any required corresponding source; review redistribution rights for proprietary blobs.
- [ ] Prepare installation/upgrade/rollback instructions, known issues and tested hardware matrix.
- [ ] Include versioned artifacts, checksums, signing details and accurate experimental labels.
- [x] Stage the current candidate's eight private payloads and two metadata
  files. Verify the exact local set against the independently pinned
  [receipt](CANDIDATE_PACKAGING.md#verify-the-complete-download-set).
- [x] Stage and verify the [neutral artwork variant](../manifests/current-neutral-artwork.json)
  with its original generator, a complete AVB audit and a saved slot-A fit.
  Hardware verification and hosted asset checks remain open.
- [x] Verify all 23 files in the consolidated private r2 delivery, including
  the GoogleTest supplement and all prior source and notice companions.
  [Release receipt](../manifests/current-neutral-artwork.json)
- [x] Rebuild the exact r2 ZIP, manifest and packaging receipt from the
  pinned source metadata and reviewed signed inputs.
  [Exact ZIP reproduction](CANDIDATE_PACKAGING.md#reproduce-the-staged-neutral-r2-zip)
- [x] Download and verify the complete older f38 draft, including its source
  supplement, public signing materials and two release metadata files. Repeat
  the [complete download check](CANDIDATE_PACKAGING.md#verify-the-complete-download-set)
  for the new release after staging.
- [x] Add bug-report instructions covering firmware/build identity and useful redacted logs. See `.github/ISSUE_TEMPLATE/bug_report.md`; final binary build identity remains a packaging gate.
- [ ] Review release contents for personal data and keys one last time.
- [ ] Publish the developer preview under the owner’s existing release authorization after the required installation/recovery, rights and final-artifact gates pass.
- [ ] Require repeatable installation/recovery and resolved critical stability issues before calling it stable.

## Evidence already available — re-test after integration

- [x] User verified remote navigation/select, Settings tap/hold, and widget double-press on the development device.
- [x] User verified AirPods removal pause and reinsertion resume after the duplicate-pause fix.
- [x] User verified custom boot animation visually; it must not delay boot.
- [x] Eight Java host suites passed for button gestures, AirPods parsing/state, sync math, HDMI caps, server URI validation and native replay flags; the current local suite has 194 Python cases (five signed AVB cases skipped without build tools); CI runs the signed fixtures separately.
- [x] Main Settings categories and the native Remotes & Accessories AirPods link were inspected live; link opens pause/resume and Back returns correctly.
- [x] Smart Home provider configuration/shortcut UI installed; no provider account or voice conversation verified yet.
- [x] Built-in microphone produced a one-second 16 kHz capture; samples discarded, not saved or transmitted.
- [x] Earlier offline image candidates passed size/metadata/AVB checks. This does not certify the newest app/Settings changes are in those images.

## Launcher options checkpoint — 2026-11-23

- [x] Install upstream-signed ARM32-compatible FLauncher 0.18.0, LTvLauncher 2026.11.23, and Bridge Console TV 0.61 preview as choices alongside Android TV Home.
- [x] Add Settings → Home screen with confirmation, preview and native Android Home-role switching; keep current default.
- [x] Launch all three alternatives successfully; reselect current Android TV Home and verify Android role callback accepted=true and default resolver unchanged.
- [ ] Test actual changes to each alternate default, remote Home behavior, reboot persistence and switching back.
- [ ] Review corresponding-source and redistribution requirements before bundling downloaded APKs in public ROM artifacts.

## Smart Home expansion — research, not release claims

- [ ] Assess Matter controller and Thread border-router feasibility as separate features; see SMART_HOME_ROADMAP.md.
- [x] Read-only evidence: vendor Thread HAL registered and configured for Spinel UART transport. No network commissioning/reset performed.
- [ ] Verify actual Thread operation before advertising support.
- [ ] Keep room-temperature features tied to a real external sensor, not the chip's thermal reading.

## Offline release checkpoint — 2026-11-24

- [x] Assemble and independently reproduce the controlled launcher's 445-file
  corresponding-source/notice bundle; see LAUNCHER_SOURCE_BUILD.md. This is
  component source delivery, not proof of complete ROM release readiness.
- [x] Rebuild the launcher's ARMv7 SQLite from the staged corresponding
  sources and match every byte outside the original GNU build ID. Fixed
  debug paths yield identical binaries from two fresh build directories.
  [SQLite recipe and evidence](LAUNCHER_SOURCE_BUILD.md#reproducing-the-armv7-sqlite-library)
- [x] Match the shipped Flutter engine to its official Maven artifact,
  read back the launcher's 1,588 recorded Dart inputs, and replay the ARMv7
  AOT compiler against the preserved kernel.
  [Flutter evidence](LAUNCHER_SOURCE_BUILD.md#armv7-flutter-engine-and-dart-aot)
- [x] Resolve the launcher's dependencies offline from the exact source
  companion, regenerate the plug-in registrant and Dart kernel, and
  reproduce the shipped ARMv7 AOT library from the new kernel.
  [Source-to-kernel receipt](../manifests/launcher-flutter-frontend-rebuild.json)
- [x] Compile and relocate DataStore's protobuf dependency from the staged
  Java sources and reproduce the complete JAR used to build the launcher.
  [Protobuf recipe and evidence](LAUNCHER_SOURCE_BUILD.md#reproducing-the-datastore-protobuf-jar)
- [x] Verify the launcher companion's 43 native source archives against the
  pinned Flutter checkout and resolve its 14 CIPD package instances.
  [Native build preflight](../manifests/launcher-flutter-native-preflight.json)
- [x] Map every planned direct ARMv7 link object to a tracked or generated
  input and confirm that all 16 tracked-source projects have staged archives.
- [x] Trace the 78 planned objects in the six directly linked static
  libraries to five staged source trees and one generated Dart version input.
- [x] Read back all six compiled Flutter static libraries and verify the
  names, order and bytes of all 78 members against the linked objects.
- [x] Trace all 53 generated source paths to their Ninja rules and verify
  the declared tracked inputs against the 12 pinned project trees.
- [x] Replay the generated Dart version file with two independent reflogs
  and match the exact build output.
- [x] Verify the staged ICU data against the reference engine ELF and
  reproduce its generated assembly and ARM object.
- [x] Reproduce all 51 linked Impeller shader sources byte for byte by
  replaying their compilation, archiving and embedding rules offline.
- [x] Verify the pinned Flutter ARMv7 linker/NDK inputs and reproduce the
  scratch link from its captured files. The complete engine link is separate.
- [x] Verify the actual ARMv7 link response and all 3,124 compiler
  dependency records. Stage and verify the pinned GoogleTest supplement
  alongside the existing launcher source companion.
- [x] Reproduce the complete Flutter ARMv7 library byte for byte against
  both the pinned release ELF and the signed launcher APK member.
- [x] Verify the private r2 download set with the recipient verifier and
  reject a copy with the GoogleTest source supplement omitted.
- [x] Verify production-key package/APEX signing in the private rehearsal with
  pinned public inventory; all 31 APEX filesystem metadata comparisons passed.
  Whole-image AVB, OTA trust and hardware acceptance remain separate gates.
- [x] Export and validate a Google-free composition profile and pinned 27-file
  recipe; verify existing metadata, including labels/capabilities, and exact
  expected additions against the tested private candidate.
- [x] Finish the deterministic local Google-app composer and coherent AVB rebuild
  against the exact `1ac457e` candidate: two actual runs produced identical five
  images, all ten independently rehashed. Public binary installation is pending.
- [x] Complete the bounded target-files build and integrate the neutral controlled
  launcher pin at source `1ac457e`; verify the exact signed launcher survives.
- [x] Re-run final base-image privacy, content, metadata, size and AVB checks on
  the exact signed `1ac457e` candidate; see DEVELOPMENT.md for scope and limits.
  GApps composition and final packaged ZIP checks remain separate.


## Corrected f38 candidate checkpoint — 2026-11-24

- [x] Complete the corrected candidate at frozen product source
  `f38da52af274a0e50c92a10cf279e62f44125358`, including the loadable remote
  permissions XML with all three requested grants. Historical `1ac457e` evidence
  above does not replace this candidate's checks.
- [x] Recheck production package/APEX signatures, OTA trust replacement, native
  metadata intent, image privacy/notices and stock-template AVB on this exact
  candidate. Independent audit SHA256:
  `774a819f5b13f6634bab41f603b610be72bc65e8a63b53262f08c4007de3f1a5`.
- [x] Verify the vanilla ZIP by complete member readback and independently repeat
  local Google composition with identical five-image outputs. Google-containing
  outputs remain private; no redistribution authorization is inferred.
- [x] Audit all 1,430 project revisions and reconstruct eleven modified/new files
  across five projects. Publish the missing SetupWizard source supplement at
  `225a2828d025ea9967d27ed2d0ee6455d555d395`; frozen product source requires that
  companion. See FROZEN_F38_REPRODUCTION.md for exact source/build identity.
- [x] Reproduce launcher/native-library/notices and animation staging in a sparse
  workspace using pinned SDK/JDK inputs. This does not prove a clean whole-ROM
  rebuild or reproducible private signatures.
- [x] Capture a fresh private sixteen-partition current-device restore baseline,
  matching live hashes before/after capture; verify its AVB consistency. Actual
  restoration and external hardware trust remain untested.
- [x] Complete the authorized read-only Android A → Recovery → fastbootd → Android A
  roundtrip over USB. This verifies the existing installed development recovery,
  not the candidate's stock bootstrap or production signing key acceptance.
- [x] Qualify the pinned recovery RAM helper and read-only metadata inspection
  on the existing development recovery: native execution passed; metadata
  remained byte-identical before/after mounting with replay disabled.
- [x] Complete the native Recovery raw-writer dry-run for the exact corrected
  candidate and seven-target transition: all targets classified old, no writes
  requested, protected physical/prefix hashes unchanged, Android A returned.
  This does not qualify persistent execution or replacement recovery.
- [x] Obtain approval for the exact seven-target slot A transition and shared
  data factory reset; install and fully read back the corrected f38 image set.
  Owner confirmed the reset reached Android setup; setup completion and input
  checks remain pending.
- [ ] Complete installation, clean setup, recovery and rollback tests of the exact
  production-key candidate before publishing binaries. Preserve slot B throughout.

- [x] Rehearse Controls 1.1 and the Music session cleanup in private vanilla
  images. Read back both APKs, verify filesystem content and metadata, rebuild
  AVB, reproduce all five image hashes, and apply-check all eight source patches.
  See `manifests/f38-app-integration-rehearsal.json`. Those changes now have a
  clean full-source build and final-image readback in the current candidate.
  Hardware verification remains required.


## Normal-user installation rehearsal — owner request, 2026-11-24

- [x] Verify the actual LCARS archive with the portable host preflight. Check
  all 13 AVB bindings, prepare the seven images and confirm fit and restore
  hashes against the saved slot-A trial. Fresh capture, signed release inputs
  and hardware verification remain open. [Local preflight](CANDIDATE_INSTALLATION.md#prepare-a-verified-lcars-zip-locally)
- [x] Repeat the layout and rollback-file check using the public preflight and
  pinned native `lpdump`, with a matching saved A result and a refused saved B.
  [Saved fit check](CANDIDATE_INSTALLATION.md#check-a-saved-layout-and-restore-files)
- [x] Verify the staged Linux x86-64 native layout-reader archive and reproduce
  the exact neutral r2 preflight from an extracted copy without the Android tree.
  [Host tool companion](CANDIDATE_INSTALLATION.md#native-layout-reader-for-linux-x86-64)
- [x] Reproduce the neutral r2 archive preflight from staged downloads, fresh
  stock extracts and a newly prepared tool kit. Both tested LZ4 versions
  produced the same seven image hashes and 13 verified AVB bindings.
  [Recipient preflight receipt](../manifests/neutral-r2-recipient-preflight.json)
- [x] Rehearse the same workflow on Debian 12 x86-64 with distro tools.
  Compare both reports with the Debian 13 run and repeat the saved-layout
  acceptance and refusal cases. [Debian 12 receipt](../manifests/neutral-r2-bookworm-preflight.json)
- [ ] Provide a supported installation route using published downloads and a
  standard computer, with exact prerequisites and clear supported-device/firmware
  limits. The current raw-image ZIP is not a sideload OTA.
- [ ] Make backup, target selection, verification and rollback reproducible from
  the published instructions without private server access, private scripts,
  manually authored trust booleans or an AI operator.
- [ ] Rehearse that exact public route and record device state, every write,
  protected slot/metadata checks, fresh setup and recovery results. The private
  developer trial is not a substitute for this acceptance test.


## Custom recovery required for the public build

- [x] Build and reproduce a stock-compatible ARM32 LCARS prototype offline.
  The archive preserves stock Fastbootd and boot-control services. The ARM
  emulator checks factory loading and menu dispatch. See the
  [prototype evidence](PERSISTENT_FEATURES.md#stock-compatible-arm32-lcars-prototype).
- [x] Publish the source-only prototype recipe and reproduce the exact image
  from that commit. The recipe verifies the stock firmware and header hashes.
  [Pinned recipe](https://github.com/firejackson1/jarvis2-os/blob/1409c21924d1040024c9521749248e05d7f78315/docs/STOCK_LCARS.md)
- [x] Rehearse the prototype's AVB binding offline with an ephemeral root key.
  Verify the whole chain and reject a stock image substituted for the prototype.
- [x] Reproduce the exact Recovery image using the portable tool kit and a
  separately supplied stock image. Verify two identical private LCARS ZIPs,
  local reconstruction from the archived plug-in and the resulting AVB chain.
  [Candidate packaging](CANDIDATE_PACKAGING.md#include-locally-assembled-lcars-recovery)
- [x] Bind the LCARS plug-in's exact compiler inputs to pinned revisions and
  reproduce its notice companion twice. Include it with the same plug-in in
  any final artifact review. [LCARS notice manifest](../manifests/lcars-notice-provenance.json)
- [x] Package the matching notices with the plug-in and independently
  verify the format 3 rehearsal ZIP through local `vendor_boot` reconstruction.
  [Candidate packaging](CANDIDATE_PACKAGING.md#include-locally-assembled-lcars-recovery)
- [x] Assemble the LCARS root binding directly from verified stock templates
  and a local Recovery image. Reproduce the five rehearsal ROM images and
  verify that the completed chain rejects stock Recovery substituted for LCARS.
  [LCARS AVB assembly](AVB_IMAGE_ASSEMBLY.md#bind-a-locally-reconstructed-lcars-recovery)
- [ ] Include the new compatible LCARS recovery and its source/build provenance
  in the final package and coherent AVB chain. Do not treat the stock-recovery
  engineering trial as the final product.
- [x] Recompose optional Google apps privately against the exact current LCARS
  candidate. Recheck both complete outputs, all 21 tracked unchanged members,
  and the `vendor_boot` binding with temporary keys. Repeat for neutral artwork.
  [Offline rehearsal](GAPPS_COMPOSITION.md#lcars-integration-rehearsal)
- [ ] Verify HDMI, box-button operation, USB keyboard and remote input in RAM
  before considering another recovery write.
- [ ] Implement and verify recovery-owned Bluetooth discovery/pairing/HID input
  for the onn remote; Android pairing and an input-only UI are insufficient.
- [ ] Recheck installer, recovery, Android return and rollback against the exact
  package containing that custom recovery.
