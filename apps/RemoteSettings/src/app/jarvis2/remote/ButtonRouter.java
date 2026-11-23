package app.jarvis2.remote;
import android.accessibilityservice.AccessibilityService;
import android.content.*;
import android.os.*;
import android.util.Log;
import android.view.*;
import java.util.*;

final class ButtonRouter {
    private static final int FALLBACK=0x400;
    private static ButtonRouter active;
    private static boolean configuring;
    static void configuring(boolean value){configuring=value;if(value&&active!=null)active.clear();}
    private final Keys owner;private final ButtonBindings bindings;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final Map<String,Press> presses=new HashMap<>();
    private final Map<String,Integer> directKeys=new HashMap<>();
    private final Map<String,KeyEvent> directDowns=new HashMap<>();
    private final class Press {
        KeyEvent down,up,last;ButtonGesture gesture;
        final Runnable timer=()->{
            gesture.tick(SystemClock.uptimeMillis());schedule(this);
        };
    }
    ButtonRouter(Keys owner){this.owner=owner;bindings=new ButtonBindings(owner);active=this;}
    boolean onKey(KeyEvent event){
        if(configuring || (event.getFlags()&FALLBACK)!=0 || event.getDeviceId()<0)return false;
        InputDevice device=event.getDevice();if(device==null||device.isVirtual())return false;
        String descriptor=device.getDescriptor();int code=event.getKeyCode();
        String id=descriptor+"|"+code;
        String tap=bindings.get(descriptor,code,"tap");
        if(directKeys.containsKey(id)||(tap.startsWith("key:")&&bindings.get(descriptor,code,"double").equals("default")&&bindings.get(descriptor,code,"hold").equals("default"))){
            int target=directKeys.containsKey(id)?directKeys.get(id):Integer.parseInt(tap.substring(4));
            if(event.getAction()==KeyEvent.ACTION_DOWN){directKeys.put(id,target);directDowns.putIfAbsent(id,new KeyEvent(event));}
            inject(remap(event,target));
            if(event.getAction()==KeyEvent.ACTION_UP){directKeys.remove(id);directDowns.remove(id);}
            Log.d("JarvisButtons","Direct key "+code+" -> "+target+" action="+event.getAction());return true;
        }
        Press p=presses.get(id);long now=SystemClock.uptimeMillis();
        if(p==null&&!bindings.intercept(descriptor,code))return false;
        if(p==null){
            if(event.getAction()!=KeyEvent.ACTION_DOWN)return false;
            p=new Press();Press capture=p;
            p.gesture=new ButtonGesture(bindings.get(descriptor,code,"tap"),bindings.get(descriptor,code,"double"),
                bindings.get(descriptor,code,"hold"),action->dispatch(action,capture));presses.put(id,p);
        }
        p.gesture.tick(now);p.last=new KeyEvent(event);
        if(event.getAction()==KeyEvent.ACTION_DOWN){
            if(event.getRepeatCount()==0)p.down=new KeyEvent(event);
            p.gesture.down(now);
        }else if(event.getAction()==KeyEvent.ACTION_UP){p.up=new KeyEvent(event);p.gesture.up(now,event.isCanceled());}
        schedule(p);return true;
    }
    private void schedule(Press p){
        main.removeCallbacks(p.timer);
        long deadline=p.gesture.deadline();
        if(deadline>=0)main.postAtTime(p.timer,deadline);
        if(p.gesture.idle())presses.values().remove(p);
    }
    private KeyEvent remap(KeyEvent e,int code){return new KeyEvent(e.getDownTime(),e.getEventTime(),e.getAction(),code,e.getRepeatCount(),e.getMetaState(),e.getDeviceId(),0,e.getFlags()|FALLBACK,e.getSource());}
    void clear(){
        for(Map.Entry<String,Integer> e:directKeys.entrySet())inject(remap(KeyEvent.changeAction(directDowns.get(e.getKey()),KeyEvent.ACTION_UP),e.getValue()));
        directKeys.clear();directDowns.clear();
        for(Press p:new ArrayList<>(presses.values())){main.removeCallbacks(p.timer);p.gesture.cancel();}presses.clear();}
    void destroy(){clear();if(active==this)active=null;}
    private void inject(KeyEvent event){
        if(event==null)return;
        try{
            Class<?> manager=Class.forName("android.hardware.input.InputManager");
            Object input=manager.getMethod("getInstance").invoke(null);
            KeyEvent replay=KeyEvent.changeFlags(event,event.getFlags()|FALLBACK);
            boolean ok=(Boolean)manager.getMethod("injectInputEvent",InputEvent.class,int.class).invoke(input,replay,0);
            if(!ok)Log.w("JarvisButtons","Input injection rejected");
        }catch(Exception e){Log.e("JarvisButtons","Cannot replay input",e);}
    }
    private void pair(int code,Press p){
        long now=SystemClock.uptimeMillis();KeyEvent origin=p.down;
        int device=origin==null?-1:origin.getDeviceId(),source=origin==null?InputDevice.SOURCE_KEYBOARD:origin.getSource();
        inject(new KeyEvent(now,now,KeyEvent.ACTION_DOWN,code,0,0,device,0,FALLBACK,source));
        inject(new KeyEvent(now,now,KeyEvent.ACTION_UP,code,0,0,device,0,FALLBACK,source));
    }
    private void dispatch(String action,Press p){
        try{
            switch(action){
                case "none":return;
                case "voice":VoiceSettings.launch(owner);return;
                case "voice_settings":owner.startActivity(new Intent(owner,VoiceSettings.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));return;
                case "default":inject(p.down);inject(p.up);return;
                case "default_down":inject(p.down);return;
                case "default_repeat":inject(p.last);return;
                case "default_up":inject(p.up!=null?p.up:KeyEvent.changeAction(p.down,KeyEvent.ACTION_UP));return;
                case "home":EarDetection.get(owner).cancelResume();owner.performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME);return;
                case "back":owner.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK);return;
                case "recents":owner.performGlobalAction(AccessibilityService.GLOBAL_ACTION_RECENTS);return;
                case "power":owner.performGlobalAction(AccessibilityService.GLOBAL_ACTION_POWER_DIALOG);return;
            }
            if(action.startsWith("key:")){
                int code=Integer.parseInt(action.substring(4));
                if(code==85||code==127||code==87||code==88)EarDetection.get(owner).cancelResume();
                pair(code,p);return;
            }
            Intent intent;
            if(action.equals("settings"))intent=new Intent(android.provider.Settings.ACTION_SETTINGS);
            else if(action.equals("widgets"))intent=new Intent(owner,WidgetPanel.class);
            else if(action.equals("configure"))intent=new Intent(owner,ControllerSettings.class);
            else if(action.startsWith("app:")){
                String app=action.substring(4);intent=owner.getPackageManager().getLeanbackLaunchIntentForPackage(app);
                if(intent==null)intent=owner.getPackageManager().getLaunchIntentForPackage(app);
                if(intent==null)return;
            }else intent=new Intent(owner,Panel.class).putExtra("page",action.equals("audio")?"audio":"bluetooth");
            owner.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            Log.i("JarvisButtons","Action="+action);
        }catch(Exception e){Log.e("JarvisButtons","Button action failed",e);}
    }
}
