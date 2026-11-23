package app.jarvis2.remote;
public class ResumeStateTest {
 public static void main(String[] args){
  ResumeState r=new ResumeState();r.arm(1000);
  if(r.allows(1100,2,20000))throw new AssertionError("Must confirm pause first");
  r.update(2,20000);r.update(2,20000);r.update(2,20001);
  if(!r.allows(3000,2,20001))throw new AssertionError("Duplicate player updates must permit resume");
  if(r.allows(121001,2,20001))throw new AssertionError("Expired ownership");
  r.cancel();if(r.allows(3000,2,20001))throw new AssertionError("Manual control cancelled ownership");
  r.arm(4000);r.update(2,20000);r.update(3,20000);r.update(2,20000);
  if(r.allows(6000,2,20000))throw new AssertionError("User play/pause must not revive ownership");
  r.arm(7000);r.update(2,20000);r.update(2,21000);
  if(r.allows(9000,2,21000))throw new AssertionError("Seeking cancels ownership");
  System.out.println("ResumeState: duplicate paused reports, confirmation, timeout, manual cancellation, user play/pause and seek passed");
 }
}
