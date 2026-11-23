package app.jarvis2.remote;

import android.os.*;
import java.util.ArrayList;

/** Reads the HAL through AudioFlinger, bypassing AudioSystem's stale latency cache. */
final class LiveLatency {
    static int read() throws Exception {
        // This transaction is verified against our LineageOS 21 generated AIDL header.
        if (Build.VERSION.SDK_INT != 34) return -1;
        IBinder flinger = (IBinder) Class.forName("android.os.ServiceManager")
                .getMethod("getService", String.class).invoke(null, "media.audio_flinger");
        if (flinger == null || !"android.media.IAudioFlingerService".equals(flinger.getInterfaceDescriptor())) return -1;
        ArrayList<Object> patches = new ArrayList<>();
        // AudioManager resolves the generic native port handles into typed device/mix ports.
        int result = (Integer) android.media.AudioManager.class
                .getMethod("listAudioPatches", ArrayList.class).invoke(null, patches);
        if (result != 0) return -1;
        int latency = -1;
        for (Object patch : patches) {
            boolean bluetooth = false;
            for (Object config : (Object[]) patch.getClass().getMethod("sinks").invoke(patch)) {
                Object port = config.getClass().getMethod("port").invoke(config);
                if (!port.getClass().getName().equals("android.media.AudioDevicePort")) continue;
                int type = (Integer) port.getClass().getMethod("type").invoke(port);
                if (type == 0x80 || type == 0x100 || type == 0x200) bluetooth = true;
            }
            if (!bluetooth) continue;
            for (Object config : (Object[]) patch.getClass().getMethod("sources").invoke(patch)) {
                Object port = config.getClass().getMethod("port").invoke(config);
                if (!port.getClass().getName().equals("android.media.AudioMixPort")) continue;
                int handle = (Integer) port.getClass().getMethod("ioHandle").invoke(port);
                Parcel request = Parcel.obtain(), reply = Parcel.obtain();
                try {
                    request.writeInterfaceToken("android.media.IAudioFlingerService");
                    request.writeInt(handle);
                    if (!flinger.transact(IBinder.FIRST_CALL_TRANSACTION + 5, request, reply, 0)) continue;
                    reply.readException();
                    int ms = reply.readInt();
                    if (ms > 0 && ms <= 2000) latency = Math.max(latency, ms);
                } finally { request.recycle(); reply.recycle(); }
            }
        }
        return latency;
    }
}
