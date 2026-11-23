package app.jarvis2.remote;
import java.net.URI;
import java.util.Locale;
/** Accept a server origin, never credentials or a token-bearing link. */
final class VoiceServer {
 static String normalize(String value){
  try {
   URI u=new URI(value.trim());String scheme=u.getScheme();
   if(scheme==null||!(scheme.equalsIgnoreCase("https")||scheme.equalsIgnoreCase("http"))||u.getHost()==null||u.getUserInfo()!=null||u.getRawQuery()!=null||u.getRawFragment()!=null||u.getPort()>65535||u.getPort()==0||(!u.getRawPath().isEmpty()&&!u.getRawPath().equals("/")))throw new IllegalArgumentException();
   return new URI(scheme.toLowerCase(Locale.ROOT),null,u.getHost(),u.getPort(),null,null,null).toASCIIString();
  }catch(Exception e){throw new IllegalArgumentException("Use a server address such as https://ha.example.org, without a password, path or token.");}
 }
}
