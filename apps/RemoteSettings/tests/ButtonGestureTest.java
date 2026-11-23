package app.jarvis2.remote;
import java.util.*;
public class ButtonGestureTest {
 static List<String> out=new ArrayList<>();
 static void expect(String... events){if(!out.equals(Arrays.asList(events)))throw new AssertionError(out+" != "+Arrays.toString(events));out.clear();}
 static ButtonGesture g(String tap,String twice,String hold){return new ButtonGesture(tap,twice,hold,out::add);}
 public static void main(String[] args){
  ButtonGesture a=g("settings","widgets","bluetooth");a.down(0);a.up(60,false);a.tick(359);expect();a.tick(360);expect("settings");
  a=g("settings","widgets","bluetooth");a.down(0);a.up(60,false);a.down(180);a.up(220,false);a.tick(700);expect("widgets");
  a=g("settings","widgets","bluetooth");a.down(0);a.tick(599);expect();a.tick(600);a.down(620);a.up(900,false);a.tick(1300);expect("bluetooth");
  a=g("key:24","default","default");a.down(0);a.up(80,false);expect("key:24");
  a=g("default","widgets","default");a.down(0);a.tick(600);a.down(720);a.up(800,false);expect("default_down","default_repeat","default_up");
  a=g("settings","widgets","bluetooth");a.down(0);a.up(900,true);a.tick(1000);expect();
  a=g("settings","widgets","bluetooth");a.down(0);a.up(70,true);a.tick(1000);expect();
  a=g("settings","widgets","bluetooth");a.down(0);a.up(60,false);a.cancel();a.tick(1000);expect();
  a=g("settings","widgets","bluetooth");a.down(0);a.up(50,false);a.tick(351);a.down(400);a.up(450,false);a.tick(751);expect("settings","settings");
  a=g("none","none","key:24");a.down(0);a.tick(600);a.down(620);a.down(710);a.up(900,false);expect("key:24","key:24");
  ButtonGesture b=g("home","default","none");a=g("back","default","none");a.down(0);b.down(10);a.up(50,false);b.up(60,false);expect("back","home");
  System.out.println("ButtonGesture: tap/double/hold, deadline, repeat, default down/up, cancellation and simultaneous independent buttons passed");
 }
}
