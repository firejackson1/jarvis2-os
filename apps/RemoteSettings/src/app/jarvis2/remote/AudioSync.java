package app.jarvis2.remote;

import android.content.*;
import android.media.*;
import android.os.*;
import android.util.Log;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Lives with the remote key service so closing the panel keeps audio working. */
final class AudioSync {
    private static AudioSync instance;
    static synchronized AudioSync get(Context context) {
        if (instance == null) instance = new AudioSync(context.getApplicationContext());
        return instance;
    }
    private final AudioManager audio;
    private final SharedPreferences prefs;
    private final LosslessAudio lossless;
    private boolean passRouted;
    private volatile String losslessStatus = "Decoded audio";
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Set<Runnable> listeners = new HashSet<>();
    private boolean busy, again, owned;
    private volatile boolean delayKnown, routeDirty = true;
    private Object media;
    private Class<?> strategyClass;
    private List<?> previous;
    private String routeAddress;
    private volatile String address = "", name = "No Bluetooth audio connected";
    private volatile String status = "TV + Bluetooth is off";
    private volatile int reported = -1, applied = 0;
    private final Runnable poll = this::refresh;

    private AudioSync(Context context) {
        lossless = new LosslessAudio(context);
        audio = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
        prefs = context.getSharedPreferences("audio-sync", Context.MODE_PRIVATE);
        audio.registerAudioDeviceCallback(new AudioDeviceCallback() {
            public void onAudioDevicesAdded(AudioDeviceInfo[] devices) { routeDirty = true; delayKnown = false; lossless.invalidate(); refresh(); }
            public void onAudioDevicesRemoved(AudioDeviceInfo[] devices) { routeDirty = true; delayKnown = false; lossless.invalidate(); refresh(); }
        }, main);
        refresh();
    }
    boolean enabled() { return prefs.getBoolean("enabled", false); }
    boolean automatic() { return prefs.getBoolean("auto", true); }
    boolean passthrough() { return prefs.getBoolean("passthrough", false); }
    boolean canBitstream() { return lossless.canBitstream(); }
    String receiverFormats() { return lossless.receiver(); }
    String losslessSupport() { return lossless.support(); }
    String losslessStatus() { return losslessStatus; }
    int calibration() { return prefs.getInt("delay." + address, 0); }
    String status() { return status; }
    String name() { return name; }
    String detail() {
        return reported > 0 ? "Reported output latency " + reported + " ms" : "Latency unavailable · using saved delay";
    }
    int applied() { return applied; }
    boolean hasDevice() { return !address.isEmpty(); }
    void listen(Runnable listener) { listeners.add(listener); }
    void unlisten(Runnable listener) { listeners.remove(listener); }
    void setEnabled(boolean enabled) {
        SharedPreferences.Editor edit = prefs.edit().putBoolean("enabled", enabled);
        if (enabled) edit.putBoolean("passthrough", false);
        edit.apply(); refresh();
    }
    void setPassthrough(boolean enabled) {
        SharedPreferences.Editor edit = prefs.edit().putBoolean("passthrough", enabled);
        if (enabled) edit.putBoolean("enabled", false);
        edit.apply(); refresh();
    }
    void setAutomatic(boolean automatic) { prefs.edit().putBoolean("auto", automatic).apply(); refresh(); }
    void calibrate(int ms) {
        if (address.isEmpty()) return;
        SharedPreferences.Editor edit = prefs.edit().putInt("delay." + address, SyncMath.clamp(ms));
        if (reported > 0) edit.putInt("baseline." + address, reported);
        edit.apply();
        refresh();
    }
    void refresh() {
        main.removeCallbacks(poll);
        if (busy) { again = true; return; }
        busy = true;
        worker.execute(() -> {
            try { update(); }
            catch (Exception failure) {
                Log.e("JarvisAudioSync", "Could not apply sync", failure);
                status = "Could not apply audio sync";
                losslessStatus = "Could not apply audio mode";
                prefs.edit().putBoolean("passthrough", false).apply();
                try { lossless.apply(audio, false); } catch (Exception modeFailure) {
                    Log.e("JarvisAudioSync", "Could not restore decoded mode", modeFailure);
                }
                try { restore(); } catch (Exception restoreFailure) {
                    Log.e("JarvisAudioSync", "Could not restore routing", restoreFailure);
                }
            }
            main.post(() -> {
                busy = false;
                for (Runnable listener : new ArrayList<>(listeners)) listener.run();
                if (again) { again = false; refresh(); }
                else if (enabled() || passthrough()) main.postDelayed(poll, 15000);
            });
        });
    }
    private void update() throws Exception {
        lossless.refreshCaps(audio);
        AudioDeviceInfo hdmi = null, bluetooth = null;
        for (AudioDeviceInfo device : audio.getDevices(AudioManager.GET_DEVICES_OUTPUTS)) {
            if (device.getType() == AudioDeviceInfo.TYPE_HDMI) hdmi = device;
            if (device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP) bluetooth = device;
        }
        String next = bluetooth == null ? "" : bluetooth.getAddress();
        if (!next.equals(address)) reported = -1;
        address = next;
        name = bluetooth == null ? "No Bluetooth audio connected" : bluetooth.getProductName().toString();
        if (passthrough()) {
            if (owned || prefs.getBoolean("owned", false)) restore();
            if (hdmi == null || !lossless.canBitstream()) {
                lossless.apply(audio, false);
                losslessStatus = hdmi == null ? "Waiting for HDMI audio" : lossless.support();
                passRouted = false;
            } else {
                if (!passRouted || routeDirty) {
                    preferOne(hdmi);
                    passRouted = true;
                    routeDirty = false;
                }
                lossless.apply(audio, true);
                losslessStatus = "HDMI bitstream mode · headphones off";
            }
            status = "TV + Bluetooth is off";
            return;
        }
        passRouted = false;
        if (lossless.ready() || enabled()) lossless.apply(audio, false);
        losslessStatus = "Decoded PCM · headphones supported";
        if (!enabled()) {
            if (owned || prefs.getBoolean("owned", false)) restore();
            status = "TV + Bluetooth is off";
            return;
        }
        if (hdmi == null || bluetooth == null) {
            if (owned || prefs.getBoolean("owned", false)) restore();
            status = hdmi == null ? "Waiting for HDMI audio" : "Waiting for Bluetooth audio";
            return;
        }
        if (!owned || !address.equals(routeAddress) || routeDirty) {
            routeDirty = false;
            if (owned) restore();
            findStrategy();
            Method get = AudioManager.class.getMethod("getPreferredDevicesForStrategy", strategyClass);
            // After a process restart, the prior combined preference belongs to this app.
            if (prefs.getBoolean("owned", false)) removePreference();
            previous = new ArrayList<>((List<?>) get.invoke(audio, media));
            Class<?> attributes = Class.forName("android.media.AudioDeviceAttributes");
            Constructor<?> make = attributes.getConstructor(AudioDeviceInfo.class);
            List<Object> outputs = Arrays.asList(make.newInstance(hdmi), make.newInstance(bluetooth));
            boolean accepted = (Boolean) AudioManager.class.getMethod("setPreferredDevicesForStrategy",
                    strategyClass, List.class).invoke(audio, media, outputs);
            if (!accepted) throw new IllegalStateException("Combined routing rejected");
            owned = true;
            routeAddress = address;
            prefs.edit().putBoolean("owned", true).apply();
        }
        int fresh = readLatency();
        // Do not reuse another device's latency, or an old reading after a read failure.
        reported = fresh;
        int saved = calibration();
        int baseline = prefs.getInt("baseline." + address, -1);
        if (baseline < 0 && fresh > 0) {
            // First estimate for an uncalibrated device. The slider can refine it by ear.
            if (!prefs.contains("delay." + address)) saved = SyncMath.clamp(fresh);
            prefs.edit().putInt("delay." + address, saved).putInt("baseline." + address, fresh).apply();
            baseline = fresh;
        }
        int delay = automatic() ? SyncMath.delay(saved, baseline, fresh) : saved;
        setDelay(delay);
        status = (automatic() ? "Auto estimate" : "Manual") + " · TV delay " + delay + " ms";
    }
    private void findStrategy() throws Exception {
        if (media != null) return;
        strategyClass = Class.forName("android.media.audiopolicy.AudioProductStrategy");
        for (Object strategy : (List<?>) strategyClass.getMethod("getAudioProductStrategies").invoke(null)) {
            if (strategyClass.getMethod("getAudioAttributesForLegacyStreamType", int.class)
                    .invoke(strategy, AudioManager.STREAM_MUSIC) != null) {
                media = strategy;
                return;
            }
        }
        throw new IllegalStateException("Audio policy unavailable");
    }
    private void removePreference() throws Exception {
        AudioManager.class.getMethod("removePreferredDeviceForStrategy", strategyClass).invoke(audio, media);
    }
    private void restore() throws Exception {
        findStrategy();
        setDelay(0);
        boolean restored = previous != null && !previous.isEmpty() && (Boolean) AudioManager.class
                .getMethod("setPreferredDevicesForStrategy", strategyClass, List.class).invoke(audio, media, previous);
        if (!restored) removePreference();
        owned = false;
        previous = null;
        routeAddress = null;
        prefs.edit().putBoolean("owned", false).apply();
    }
    private void setDelay(int ms) throws Exception {
        ms = SyncMath.clamp(ms);
        if (delayKnown && applied == ms) return;
        AudioManager.class.getMethod("setParameters", String.class)
                .invoke(audio, "hal_param_out_dev_delay_time_ms=" + ((2 << 16) | ms));
        applied = ms;
        delayKnown = true;
        Log.i("JarvisAudioSync", "TV delay " + applied + " ms");
    }
    private int readLatency() {
        try {
            return LiveLatency.read();
        } catch (Exception failure) {
            Log.w("JarvisAudioSync", "Output latency unavailable", failure);
            return -1;
        }
    }
    void selectOutput(AudioDeviceInfo device, Runnable complete) {
        prefs.edit().putBoolean("enabled", false).putBoolean("passthrough", false).apply();
        main.removeCallbacks(poll);
        worker.execute(() -> {
            try {
                if (owned || prefs.getBoolean("owned", false)) restore();
                if (lossless.ready()) lossless.apply(audio, false);
                passRouted = false;
                preferOne(device);
                status = "TV + Bluetooth is off";
                Log.i("JarvisAudioSync", "Selected output type " + device.getType());
            } catch (Exception failure) {
                status = "Could not select output";
                Log.e("JarvisAudioSync", status, failure);
            }
            main.post(complete);
        });
    }
    private void preferOne(AudioDeviceInfo device) throws Exception {
        findStrategy();
        Object attributes = Class.forName("android.media.AudioDeviceAttributes")
                .getConstructor(AudioDeviceInfo.class).newInstance(device);
        boolean accepted = (Boolean) AudioManager.class
                .getMethod("setPreferredDevicesForStrategy", strategyClass, List.class)
                .invoke(audio, media, Collections.singletonList(attributes));
        if (!accepted) throw new IllegalStateException("Output selection rejected");
    }
}
