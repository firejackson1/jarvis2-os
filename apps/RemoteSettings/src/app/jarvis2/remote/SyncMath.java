package app.jarvis2.remote;

final class SyncMath {
    static int clamp(int ms) { return Math.max(0, Math.min(400, ms)); }
    static int delay(int calibration, int baseline, int reported) {
        return clamp(calibration + (baseline > 0 && reported > 0 ? reported - baseline : 0));
    }
}
