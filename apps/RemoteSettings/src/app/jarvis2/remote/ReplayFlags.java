package app.jarvis2.remote;
/** Native Power/Voice policy consumes these keys before accessibility filtering. */
final class ReplayFlags {
 static final int FALLBACK=0x400;
 static int forKey(int code,int flags){
  // FLAG_FALLBACK skips the framework's normal single-key gesture detector.
  return code==26||code==231?flags&~FALLBACK:flags|FALLBACK;
 }
}
