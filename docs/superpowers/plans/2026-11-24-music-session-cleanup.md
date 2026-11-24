# Music service cleanup implementation plan

> Execute inline using superpowers:executing-plans. No device installation.

**Goal:** Release Music's owned media session when its service is destroyed.

**Architecture:** Apply a small patch to pinned packages/apps/Music. Exercise the
actual callback body with lifecycle counters, then compile its complete class
against existing SDK/app artifacts without changing the Android checkout.

**Spec:** ../specs/2026-11-24-music-session-cleanup-design.md

**Constraints:** No flash, slot switch, reboot, wake, APK install or VM action.
Keep generated classes/private captures outside Git. Preserve original source.

**Review focus:** Missing session, repeated cleanup, superclass lifecycle,
pinned source mismatch and mistaken attribution to suspend must be checked.

### Task 1: Patch and verify the lifecycle

Files: patches/Music/{series,README.md,0001-release-media-session-on-destroy.patch},
tests/test_music_session_cleanup.py, tests/fixtures/MediaPlaybackService.java,
docs/BUILD.md and docs/DEVELOPMENT.md.

- [x] Add a pinned-source fixture and a callback regression for normal, repeated
  and missing-session cleanup. Run it before the patch; expect a missing-patch
  failure. Also require the original callback to fail the lifecycle regression.
- [x] Add the smallest release/null/super callback patch and repeat the test;
  expect all lifecycle assertions to pass and the original to fail.
- [x] Compile the complete patched class in a fresh private output against SDK
  34 and the existing matching Music javac jar with javac memory capped at 256 MiB.
  Verify original source unchanged; record input/output hashes and statuses.
- [x] Document future-build integration and live-test limits. Run
  tools/test-host.sh and git diff --check; expect all executed tests to pass.
- [x] Commit the source patch and review the complete change. Publish source
  after review; leave live app and frozen images unchanged.
