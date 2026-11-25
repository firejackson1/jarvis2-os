# Optional local boot artwork

The development box uses the owner's custom 1920×1080/60 fps animation with
interruptible `p` parts. The original supplied archive used completion-required
`c` parts, which could delay exit after Android was ready. Do not package that
original version.

```sh
python3 tools/prepare-boot-animation.py /outside/repo/bootanimation-no-delay.zip
```

The helper verifies the exact development animation hash, stored ZIP entries,
PNG frame signatures and interruptible parts before staging it under ignored
prebuilts/. The product fragment then uses this local input for the existing
Lineage bootanimation module. With no local artwork, the upstream default remains.
The source repository does not contain the artwork or grant redistribution rights
for embedded marks/artwork. Review those rights before publishing a ROM with it.

The private `cb9334ee26cc` candidate's signed product image includes the exact
pinned `media/bootanimation.zip`. See the
[candidate receipt](../manifests/current-cb9334-inclusion.json). Public
redistribution review and a boot timing test on this candidate remain open.
