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

A sample of the exact pinned frames shows stylized onn lettering and the
LineageOS emblem. The custom asset is part of the private candidate. Review
those marks and the artwork's provenance before promoting a ZIP that contains
it. Omitting the optional local input selects the upstream animation and
changes the product image, which requires a fresh hash and AVB audit.

## Original neutral animation

The optional neutral animation shows four pulsing dots on black. It uses the
same Android bootanimation path and exits through an interruptible `p` part.
It is generated with Python's standard library and has no external artwork
inputs. For a fresh build, run from the Android root with the checkout that
contains the generator:

```sh
mkdir -p device/onn/jarvis2/prebuilts
python3 /path/to/current-jarvis2-tools/tools/prepare-boot-animation.py \
  --neutral device/onn/jarvis2/prebuilts/bootanimation.zip
```

The output must be a new file. Its SHA-256 is
`ea74502097a5e61134f25e92ac313f2154f80aea4972bae5cec1d4252bb2b375`.
Test HDMI and boot timing on the actual image before release.
