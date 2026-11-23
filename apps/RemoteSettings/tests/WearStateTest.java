package app.jarvis2.remote;
public class WearStateTest {
 static byte[] event(int left,int right){return new byte[]{4,0,4,0,6,0,(byte)left,(byte)right};}
 public static void main(String[] args){
  WearState w=new WearState();
  if(w.update(event(0,0),8))throw new AssertionError("Initial report must not pause");
  if(!w.update(event(1,0),8))throw new AssertionError("Removing either bud pauses");
  if(w.update(event(1,0),8))throw new AssertionError("Duplicate must not pause");
  if(w.update(event(0,0),8))throw new AssertionError("Insertion must not pause or resume");
  if(w.update(new byte[]{4,0,4,0,6,0,1},7))throw new AssertionError("Truncated frame");
  if(w.update(event(99,0),8))throw new AssertionError("Unknown status");
  if(!w.update(event(0,1),8))throw new AssertionError("Malformed frames must not replace baseline");
  if(!w.update(event(1,1),8))throw new AssertionError("Removing last worn bud pauses");
  w.reset();
  if(w.update(event(1,1),8)||w.update(event(0,1),8))throw new AssertionError("No initial pause or autoplay");
  byte[] unrelated=event(1,1);unrelated[4]=4;
  if(w.update(unrelated,8))throw new AssertionError("Battery packet must not act as wear event");
  if(!w.update(event(1,1),8))throw new AssertionError("Single-bud use removal");
  System.out.println("WearState: baseline, either/last bud removal, duplicates, insertion, malformed/unknown/unrelated frames passed");
 }
}
