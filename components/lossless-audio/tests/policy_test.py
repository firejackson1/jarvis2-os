import sys
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prepare_policy import patch

stock = Path(sys.argv[1]).read_bytes()
before, after = ET.fromstring(stock), ET.fromstring(patch(stock))
assert ET.tostring(after) == ET.tostring(ET.fromstring(patch(patch(stock))))
assert [n.attrib for n in before.findall(".//route")] == [n.attrib for n in after.findall(".//route")]
assert [n.attrib for n in before.iter() if n.tag.endswith("include")] == [n.attrib for n in after.iter() if n.tag.endswith("include")]
for mix in before.findall(".//mixPort"):
    target = after.find(".//mixPort[@name='%s']" % mix.get("name"))
    expected=dict(mix.attrib)
    if "AUDIO_OUTPUT_FLAG_HW_AV_SYNC" in expected.get("flags", ""):
        expected["flags"]=" ".join(f for f in expected["flags"].split() if f!="AUDIO_OUTPUT_FLAG_HW_AV_SYNC")
    assert target.attrib == expected
    for profile in mix.findall("profile"):
        assert profile.attrib in [n.attrib for n in target.findall("profile")]
hdmi = after.find(".//devicePort[@tagName='HDMI Out']")
assert any(not p.get("format") for p in hdmi.findall("profile")), "PCM dynamic profile lost"
for name in ("compress offload", "ms12 direct"):
    assert after.find(".//mixPort[@name='%s']/profile[@format='AUDIO_FORMAT_DTS_HD']" % name) is not None
assert after.find("./surroundSound/formats/format[@name='AUDIO_FORMAT_DOLBY_TRUEHD']") is not None
assert not any("AUDIO_OUTPUT_FLAG_HW_AV_SYNC" in m.get("flags", "").split() for m in after.findall(".//mixPort"))
print("Policy: existing routes/profiles/includes, PCM, added formats and idempotence passed")
