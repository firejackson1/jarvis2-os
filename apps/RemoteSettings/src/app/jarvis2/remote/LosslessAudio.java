package app.jarvis2.remote;

import android.media.AudioManager;
import android.content.Context;
import android.util.Log;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;

final class LosslessAudio {
    private volatile String appliedMode="";
    private volatile int caps;
    private volatile boolean readable;
    private final boolean preparedROM;
    LosslessAudio(Context context) {
        preparedROM=context.getPackageManager().hasSystemFeature("app.jarvis2.audio.lossless");
    }
    boolean ready() {
        if(preparedROM)return true;
        try {
            Class<?> props=Class.forName("android.os.SystemProperties");
            if("1".equals(props.getMethod("get",String.class).invoke(null,"debug.jarvis2.lossless_ready")))return true;
        } catch(Exception ignored) { }
        return false;
    }
    void refreshCaps(AudioManager audio) {
        try {
            caps=HdmiCaps.parse(new String(Files.readAllBytes(Paths.get("/sys/class/amhdmitx/amhdmitx0/aud_cap")),StandardCharsets.UTF_8));
            readable=true;
        } catch(Exception failure) {
            // Platform apps cannot read this vendor sysfs node under the stock SELinux policy.
            // The patched HAL answers from its EDID capability flags, without relaxing that policy.
            try {
                String reply=(String)AudioManager.class.getMethod("getParameters",String.class)
                        .invoke(audio,"hdmi_encodings");
                readable=reply!=null && reply.contains("hdmi_encodings=");
                caps=readable?HdmiCaps.parseHal(reply):0;
            } catch(Exception queryFailure) { caps=0; readable=false; }
        }
    }
    int caps() { return caps; }
    String receiver() { return readable ? HdmiCaps.describe(caps) : "HDMI capabilities unavailable"; }
    boolean canBitstream() { return ready() && readable && caps!=0; }
    String support() {
        if(!ready())return "Audio support needs preparation after reboot";
        if(!readable)return "Cannot read receiver capabilities";
        return (caps&HdmiCaps.LOSSLESS)!=0 ? "Lossless formats reported by receiver" : "This display does not report lossless audio";
    }
    void invalidate() { appliedMode=""; }
    void apply(AudioManager audio, boolean passthrough) throws Exception {
        if(passthrough&&!canBitstream())throw new IllegalStateException("No compatible HDMI receiver");
        String key=passthrough?"pass:"+caps:"decoded";
        if(key.equals(appliedMode))return;
        if(passthrough) {
            int[] formats={5,6,7,8,14,18};
            for(int i=0;i<formats.length;i++) {
                boolean accepted=(Boolean)AudioManager.class.getMethod("setSurroundFormatEnabled",int.class,boolean.class)
                        .invoke(audio,formats[i],(caps&(1<<i))!=0);
                if(!accepted)throw new IllegalStateException("Could not set format "+formats[i]);
            }
        }
        // Public hidden API enum values are AUTO=0, NEVER=1, MANUAL=3 on API34.
        boolean accepted=(Boolean)AudioManager.class.getMethod("setEncodedSurroundMode",int.class)
                .invoke(audio,passthrough?3:1);
        if(!accepted)throw new IllegalStateException("Could not set surround mode");
        AudioManager.class.getMethod("setParameters",String.class)
                .invoke(audio,"hdmi_format="+(passthrough?6:0));
        appliedMode=key;
        Log.i("JarvisLossless",passthrough?"HDMI bypass with EDID format mask "+caps:"Decoded PCM mode");
    }
}
