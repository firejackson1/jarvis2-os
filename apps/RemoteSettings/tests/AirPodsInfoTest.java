package app.jarvis2.remote;
public class AirPodsInfoTest {
 static byte[] control(int id,int value){return new byte[]{4,0,4,0,9,0,(byte)id,(byte)value,0,0,0};}
 public static void main(String[] args){
  AirPodsInfo s=new AirPodsInfo();byte[] b={4,0,4,0,4,0,3,4,1,82,2,0,2,1,76,1,0,8,1,65,2,0};
  if(!s.read(b,b.length)||s.level(0)!=82||s.level(1)!=76||s.level(2)!=65)throw new AssertionError("Battery component mapping");
  if(!s.charging(1)||s.charging(0))throw new AssertionError("Charging status");
  b[9]=(byte)255;if(s.read(b,21)||s.level(0)!=82)throw new AssertionError("Reject truncated packet");
  b[10]=4;s.read(b,22);if(s.level(0)!=82||!s.stale(0))throw new AssertionError("Keep last known value, mark disconnected");
  s.read(control(13,4),11);if(s.mode()!=4)throw new AssertionError("Adaptive mode");
  s.read(control(13,99),11);if(s.mode()!=4)throw new AssertionError("Unknown mode must not overwrite confirmed state");
  s.read(control(40,1),11);if(s.conversation()!=1)throw new AssertionError("Conversation on");
  s.read(control(40,2),11);if(s.conversation()!=2)throw new AssertionError("Conversation off");
  byte[] command=AirPodsInfo.command(13,2);if(command.length!=11||command[4]!=9||command[6]!=13||command[7]!=2)throw new AssertionError("Command framing");
  byte[] voice={4,0,4,0,0x4b,0,2,0,0,1};
  if(AirPodsInfo.speaking(voice,10)!=1)throw new AssertionError("Speech start");
  voice[9]=8;if(AirPodsInfo.speaking(voice,10)!=0)throw new AssertionError("Speech end");
  voice[9]=99;if(AirPodsInfo.speaking(voice,10)!=-1||AirPodsInfo.speaking(voice,9)!=-1)throw new AssertionError("Unknown/truncated speech");
  System.out.println("AirPodsInfo: per-bud/case battery, charging, stale values, truncation, confirmed controls and commands passed");
 }
}
