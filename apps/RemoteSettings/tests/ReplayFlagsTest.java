package app.jarvis2.remote;
public final class ReplayFlagsTest {
 public static void main(String[] args){
  int system=0x8,canceled=0x20,longPress=0x80;
  for(int code:new int[]{26,231}){
   int flags=ReplayFlags.forKey(code,system|longPress|ReplayFlags.FALLBACK);
   if((flags&ReplayFlags.FALLBACK)!=0)throw new AssertionError("Native policy must see ordinary gestures");
   if((flags&(system|longPress))!=(system|longPress))throw new AssertionError("Native flags lost");
   if(ReplayFlags.forKey(code,canceled)!=canceled)throw new AssertionError("Canceled native UP changed");
  }
  for(int code:new int[]{19,23,24,85,131,132}){
   int flags=ReplayFlags.forKey(code,system);
   if((flags&ReplayFlags.FALLBACK)==0)throw new AssertionError("Ordinary replay may re-enter remapping");
   if((flags&system)==0)throw new AssertionError("Original replay flags lost");
  }
  System.out.println("Replay flags: native Power/Voice gestures, cancellation and other-key recursion guard passed");
 }
}
