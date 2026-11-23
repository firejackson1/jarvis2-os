package app.jarvis2.remote;

public class SyncMathTest {
    private static void equal(int want, int got) {
        if (want != got) throw new AssertionError("Expected " + want + ", got " + got);
    }
    public static void main(String[] args) {
        equal(50, SyncMath.delay(50, 150, 150));
        equal(90, SyncMath.delay(50, 150, 190));
        equal(50, SyncMath.delay(50, 150, -1));
        equal(0, SyncMath.delay(50, 150, 20));
        equal(400, SyncMath.delay(50, 150, 1000));
        equal(50, SyncMath.delay(50, -1, 190));
        System.out.println("SyncMath: 6 checks passed");
    }
}
