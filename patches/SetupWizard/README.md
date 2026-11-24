# SetupWizard Bluetooth permission

Apply `series` to `packages/apps/SetupWizard` at pinned upstream revision
`e58f07efee4ba3d69d6b4922d5bbf4707da6e033`, then build `LineageSetupWizard`.
The patch adds the manifest declaration for `android.permission.BLUETOOTH_CONNECT`.
It does not grant a runtime permission or establish successful device setup.

This exact source change was already present in the workspace that built the
frozen `f38da52` candidate. Publishing its source representation does not require
rebuilding those images or change their original device-source identity. For
that candidate, obtain this patch as an external source supplement while keeping
the device checkout at its original commit; see
[frozen reproduction](../../docs/FROZEN_F38_REPRODUCTION.md).
