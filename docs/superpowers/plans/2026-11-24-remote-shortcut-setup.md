# Remote Shortcut Setup Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, without subagents.

**Goal:** Enable ordinary users to discover and activate remote shortcuts after reset.

**Architecture:** Add status and an Android Accessibility intent to the existing
ControllerSettings activity. Android owns consent and the service setting.

**Tech Stack:** Existing Java Android TV app; platform accessibility APIs.

**Spec:** ../specs/2026-11-24-remote-shortcut-setup.md

## Global Constraints

Preserve user data and other accessibility services. No automatic enable,
partition flashes, slot changes, reboot or Bazzite interruption.

## Review Focus

- A different enabled service must not produce an enabled status for Keys.
- Disabled service must show setup and receive initial focus.
- No paired controller must not hide setup.
- Returning from Android Settings must refresh status.
- Missing settings handler must show a useful message rather than crash.

## Task 1 — Discoverable activation

Files: ControllerSettings.java; docs/PERSISTENT_FEATURES.md and DEVELOPMENT.md.
Consumes Android's per-user enabled accessibility-service list. Produces a
visible state and explicit Android Settings launch; writes no secure settings.

- [ ] Capture existing controller-screen UI and assert setup is present; record
  the expected failure before changing code.
- [x] Add exact-component state detection and a setup button before the controller
  chooser, including the no-controller branch. Use ACCESSIBILITY_SETTINGS.
- [x] Compile the app against the actual public SDK and run tools/test-host.sh.
- [ ] Verify candidate signer against the installed app before any data-preserving
  app update. Exercise the UI route and inspect binding/crash state; no reboot.
- [ ] Record checks, untested cases and rollback. Update release documentation.

The UI is low-impact wiring; use actual device hierarchy/intent checks rather
than source-text or framework mock tests. Keep private captures out of Git.

## Execution notes

- Baseline and updated host suite: 193 tests, five unavailable local AVB-tool
  skips; all executed tests and eight Java suites passed. These do not test the
  new Android UI.
- Public SDK compilation and APK signature verification passed. Initial archive
  build stopped at its final provenance step because the exported source had
  no Git metadata. Repeat from an actual clone of the committed source; retain
  the failed receipt rather than treating that build as successful.
- Device hierarchy capture produced no XML, and the subsequent screenshot was
  black. Read-only power state showed deliberate Power-button sleep. No RED UI
  assertion or successful visual test is claimed; leave the screen off and
  defer live UI/signature matching/installation checks until it is awake.
- Self-review only; no independent reviewer. Disabled state, another enabled
  service, no controller and unavailable Settings handler remain runtime checks.
- Final versioned candidate is 1.1/code2 from clean source 46c1c1b. App and RRO
  signing, manifest/version inspection and bounded build completed successfully.
  APKs remain private and uninstalled; the f38 ROM has not been rebuilt.
