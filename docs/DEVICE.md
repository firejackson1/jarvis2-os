# Jarvis2 device configuration

Unofficial LineageOS 21 / Android 14 bring-up for the US 2026 onn 4K Pro
(jarvis2), using stock build 15640252 as the hardware interface baseline.
ARM32 userspace, ARM64 Linux kernel, Virtual A/B dynamic partitions.

This source has built and booted a development device. That device also uses
RAM overlays and separately installed apps; it is not proof this repository
produces a complete or ready-to-install ROM. See docs/RELEASE_CHECKLIST.md.

Stock firmware, kernel, vendor images, OEM configuration and signing keys are
not distributed. stage-stock.py validates locally supplied stock images against
stock-inputs.sha256 and stages them in a caller-owned Android checkout.

No personal ADB identity is authorized by this device configuration. USB ADB
requires normal user authorization. No network ADB listener is configured here.
The developer-options network switch is temporary and resets on reboot; see
[connecting developer tools](DEBUGGING.md) for the normal user route.

Public system-image integration, private release signing, exact partition
budgets, clean installation and rollback remain release gates. Do not flash
outputs from this repository until the release documentation explicitly names
them as tested and provides a verified installation/restore procedure.
