# Jarvis2 OS development

- This is an unofficial LineageOS-based developer preview project.
- Preserve slot B. Do not flash, switch slots, wipe userdata, reboot the box,
  or interrupt the owner's desktop VM without authorization for that action.
- Existing device trust/settings are not a release baseline. Never copy ADB keys,
  private signing keys, credentials, firmware, vendor binaries or owner state here.
- Keep earlier experiments outside this repository intact. Build offline first.
- Run tools/test-host.sh and record actual evidence in docs/DEVELOPMENT.md.
- Generated APKs/images belong outside the tracked tree, never in Git history.
- Do not include experimental lossless-derived code/binaries without a verified
  redistribution license. Credit alone does not grant distribution permission.
- Maintain exact source/build provenance and a tested rollback path. Do not call
  a public image ready until installation, fresh boot and recovery are verified.
- The owner has authorized progress toward public release; no official LineageOS
  acceptance is required. Do not claim official status or upstream support.
