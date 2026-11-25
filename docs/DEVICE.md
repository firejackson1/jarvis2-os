# Jarvis2 device configuration

Unofficial LineageOS 21 / Android 14 bring-up for the US 2026 onn 4K Pro
(jarvis2), using stock build 15640252 as the hardware interface baseline.
ARM32 userspace, ARM64 Linux kernel, Virtual A/B dynamic partitions.

## Developer-preview test target

| Item | Required for the r2 trial |
| --- | --- |
| Hardware | US 2026 onn 4K Pro with product `jarvis2`. The prepared baseline is firmware `URO3.260203.035.A1`, build `15640252`. |
| Boot chain | An already-unlocked test unit. Live acceptance of the r2 AVB key and a reachable recovery transport need their own tests. |
| Slot and layout | Slot A with all eight foundation partitions allocated, one `super` backing device with 512-byte sectors, and matching native LP views. The three rebuilt logical images must fit the exact existing extents. |
| Snapshot state | A settled layout with verified clean snapshot metadata in Recovery. |
| Rollback | A fresh, hash-verified seven-image backup and an independently reachable restore transport. Previous metadata shows an unallocated B foundation. Both slots share userdata and LP metadata. |

The slot-A fit is based on a saved capture. Confirm the exact current layout
and the hardware gates before any separately authorized trial.
[Stock foundation](STOCK_FOUNDATION.md) ·
[Slot layout requirements](SLOT_INSTALLATION.md#read-only-preflight-tool) ·
[Restore evidence](RESTORE_PLAN.md)

## Development status

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
