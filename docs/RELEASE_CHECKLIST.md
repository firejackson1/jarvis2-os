# Jarvis2 public release checklist

Updated: 2026-11-24. Working checklist for continued development, not a claim of release readiness.

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
- [ ] Review redistribution rights for proprietary firmware, vendor blobs, codecs, Google apps and bundled launchers before packaging them. Existing device installation is not evidence of redistribution permission.
- [ ] Keep Google applications out of public ROM bundles unless distribution is properly licensed; document separately installed optional components.
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
- [ ] Include current TV controls app, Settings overlay and native Bluetooth Settings hook.
- [x] Port the AirPods Bluetooth-page hook into Java source for normal ROM builds; source patch and rebuilt TvSettingsTwoPanel compile passed. Fresh-image behavior remains a separate test.
- [ ] Include the required audio policy libraries, checked HAL/DTS/codec changes and Bluetooth compatibility patch.
- [ ] Integrate verified USB/ADB defaults, remote keylayout, animation and TV UI changes; distinguish experiments from production fixes.
- [ ] Fix launcher/lock-screen/notification behavior in product configuration rather than relying on leftover device state.
- [ ] Rebuild the complete slot A candidate; compare all partition budgets, EROFS metadata, AVB descriptors, keys and rollback indexes offline.
- [ ] Produce artifact hashes and a feature-to-image manifest. Older offline image sets do not contain every current app update.

## 3. Release security and privacy

- [ ] Audit source and final extracted images for owner-specific values and unintended secrets.
- [ ] Use private release signing keys with a tested backup process; do not publish keys or ship development keys unknowingly.
- [x] Generate the private key set and verify an encrypted off-host backup, including archive identity and all 204 archived files. Keys have been used in private package/APEX and launcher signing rehearsals; final image signing and hardware acceptance remain open.
- [ ] Make root debugging and unauthenticated network ADB opt-in in public builds; retain normal USB authorization by default.
- [ ] Verify enforcing SELinux, app privilege allowlists, exported components and microphone permissions.
- [ ] Ensure first-run setup uses each user's own accounts, Bluetooth devices and Smart Home provider.
- [ ] Check update/install compatibility and document which data is shared between slots.

## 4. Stability and hardware validation

- [ ] Diagnose and fix genuine suspend/wake and repeated speaker clicking; test repeated sleep/wake cycles and recovery after failure.
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

- [ ] Document exact model, firmware base, bootloader requirements and supported partition layout.
- [ ] Validate candidate against read-only live partition metadata and snapshot status before installation.
- [ ] Preserve and verify stock restore files, current recovery and necessary signing information.
- [ ] Test a RAM candidate where possible before requesting persistent installation.
- [ ] Obtain authorization for the exact slot A installation plan; never infer permission to modify slot B.
- [ ] Test first boot/clean setup and upgrades using a suitable test device/data plan; do not wipe the owner's device automatically.
- [ ] Verify recovery entry, USB ADB/fastbootd, Android reboot and stock restoration paths.
- [ ] Document what remains recoverable if failure occurs before recovery; do not promise an unproven unbrick path.
- [ ] Test rollback and repeat installation from the published instructions.

## 8. Public developer preview

- [ ] Publish buildable source, patch provenance, license notices and any required corresponding source; review redistribution rights for proprietary blobs.
- [ ] Prepare installation/upgrade/rollback instructions, known issues and tested hardware matrix.
- [ ] Include versioned artifacts, checksums, signing details and accurate experimental labels.
- [x] Add bug-report instructions covering firmware/build identity and useful redacted logs. See `.github/ISSUE_TEMPLATE/bug_report.md`; final binary build identity remains a packaging gate.
- [ ] Review release contents for personal data and keys one last time.
- [ ] Publish the developer preview under the owner’s existing release authorization after the required installation/recovery, rights and final-artifact gates pass.
- [ ] Require repeatable installation/recovery and resolved critical stability issues before calling it stable.

## Evidence already available — re-test after integration

- [x] User verified remote navigation/select, Settings tap/hold, and widget double-press on the development device.
- [x] User verified AirPods removal pause and reinsertion resume after the duplicate-pause fix.
- [x] User verified custom boot animation visually; it must not delay boot.
- [x] Eight Java host suites passed for button gestures, AirPods parsing/state, sync math, HDMI caps, server URI validation and native replay flags; the current local suite has 193 Python cases (five signed AVB cases skipped without build tools); CI runs the signed fixtures separately.
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
- [ ] Qualify the raw-writer dry-run against actual hardware. File-backed tests
  alone do not qualify it; the previous helper test did not execute the writer.
- [ ] Obtain approval for the exact candidate transition, including its stock
  init_boot/vendor_boot foundation and shared-data signing-key migration plan.
- [ ] Complete installation, clean setup, recovery and rollback tests of the exact
  production-key candidate before publishing binaries. Preserve slot B throughout.
