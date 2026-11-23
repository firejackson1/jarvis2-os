#!/usr/bin/env python3
"""Extend our saved policy without dropping PCM, existing profiles, routes or includes."""
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

def patch(source):
    root = ET.fromstring(source, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    primary = root.find("./modules/module[@name='primary']")
    if primary is None:
        raise ValueError("Missing primary audio module")
    # This vendor HAL lacks pause/resume on its HW_AV_SYNC streams under Lineage.
    # Advertising that flag aborts AudioFlinger while it probes direct outputs.
    for port in primary.findall("./mixPorts/mixPort"):
        flags=port.get("flags", "").split()
        if "AUDIO_OUTPUT_FLAG_HW_AV_SYNC" in flags:
            port.set("flags", " ".join(f for f in flags if f!="AUDIO_OUTPUT_FLAG_HW_AV_SYNC"))
    rates = "44100 48000 88200 96000 192000"
    masks = "AUDIO_CHANNEL_OUT_MONO AUDIO_CHANNEL_OUT_STEREO AUDIO_CHANNEL_OUT_5POINT1 AUDIO_CHANNEL_OUT_7POINT1"
    for name in ("compress offload", "ms12 direct"):
        port = primary.find("./mixPorts/mixPort[@name='%s']" % name)
        if port is None:
            raise ValueError("Missing " + name)
        if port.find("./profile[@format='AUDIO_FORMAT_DTS_HD']") is None:
            ET.SubElement(port, "profile", name="dtshd raw", format="AUDIO_FORMAT_DTS_HD",
                          samplingRates=rates, channelMasks=masks)
    hdmi = primary.find("./devicePorts/devicePort[@tagName='HDMI Out']")
    if hdmi is None:
        raise ValueError("Missing HDMI sink")
    if len(hdmi) == 0:
        ET.SubElement(hdmi, "profile", name="")  # Keep the original dynamic PCM/EDID profiles.
    for fmt in ("AUDIO_FORMAT_DTS", "AUDIO_FORMAT_DTS_HD"):
        if hdmi.find("./profile[@format='%s']" % fmt) is None:
            ET.SubElement(hdmi, "profile", name="", format=fmt, samplingRates=rates,
                          channelMasks=masks)
    formats = root.find("./surroundSound/formats")
    if formats is None:
        raise ValueError("Missing surround format list")
    for fmt in ("AUDIO_FORMAT_DOLBY_TRUEHD", "AUDIO_FORMAT_DTS_HD"):
        if formats.find("./format[@name='%s']" % fmt) is None:
            ET.SubElement(formats, "format", name=fmt)
    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    stock, output = map(Path, sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=True)
    (output / "audio_policy_configuration.xml").write_bytes(patch((stock / "audio_policy_configuration.xml").read_bytes()))
    config = json.loads((stock / "aml_audio_config.json").read_text())
    config.update(Passthrough_Audio_Config=1, Dolby_DRC_Audio_Config=1, Dts_DRC_Audio_Config=1)
    (output / "aml_audio_config.json").write_text(json.dumps(config, indent=4) + "\n")
