package app.jarvis2.remote;
public class HdmiCapsTest {
    public static void main(String[] args) {
        String tv="PCM, 2 ch, 32/44.1/48 kHz\nAC-3, 6 ch\nDTS, 6 ch\nDolby_Digital+, 8 ch, DepValue 0x0\n";
        int caps=HdmiCaps.parse(tv);
        if(caps!=(HdmiCaps.AC3|HdmiCaps.EAC3|HdmiCaps.DTS))throw new AssertionError("TV must not gain lossless formats");
        int avr=HdmiCaps.parse(tv+"DTS-HD, 8 ch\nMAT, 8 ch\n");
        if((avr&HdmiCaps.LOSSLESS)!=HdmiCaps.LOSSLESS)throw new AssertionError("Lossless receiver not recognized");
        if(HdmiCaps.parse("")!=0||HdmiCaps.parse("Permission denied")!=0)throw new AssertionError("Unavailable caps must fail closed");
        if((HdmiCaps.parse("DTS-HD, 8 ch\n")&HdmiCaps.DTS)!=0)throw new AssertionError("DTS-HD must not imply a reported DTS core profile");
        if((HdmiCaps.parse("Dolby_Digital+, 8 ch, DepValue 0x1\n")&HdmiCaps.JOC)==0)throw new AssertionError("JOC flag missing");
        if(HdmiCaps.parse("PCM, 2 ch\n")!=0)throw new AssertionError("PCM-only TV cannot bitstream surround");
        if(HdmiCaps.parseHal("ac3=;eac3=;hdmi_encodings=pcm")!=(HdmiCaps.AC3|HdmiCaps.EAC3))throw new AssertionError("Vendor HAL reply not recognized");
        if(HdmiCaps.parseHal("dtshd=;truehd=;hdmi_encodings=pcm")!=HdmiCaps.LOSSLESS)throw new AssertionError("HAL lossless flags missing");
        System.out.println("HDMI capabilities: TV, receiver, missing caps, format boundaries and JOC passed");
    }
}
