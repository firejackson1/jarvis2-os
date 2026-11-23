package app.jarvis2.remote;
public class VoiceServerTest {
 public static void main(String[] args) {
  eq("https://ha.example.org",VoiceServer.normalize(" https://ha.example.org/ "));
  eq("http://192.0.2.10:8123",VoiceServer.normalize("http://192.0.2.10:8123"));
  for(String bad:new String[]{"", "javascript:alert(1)","https://user:password@example.org", "https://example.org/?token=secret", "https://example.org/#token", "https://example.org/path", "file:///tmp/x", "https://example.org:99999"}) {
   try { VoiceServer.normalize(bad); throw new AssertionError("Accepted invalid server"); } catch(IllegalArgumentException expected){}
  }
  System.out.println("Voice server validation passed");
 }
 static void eq(String a,String b){if(!a.equals(b))throw new AssertionError(b);}
}
