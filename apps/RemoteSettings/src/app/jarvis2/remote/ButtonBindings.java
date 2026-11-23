package app.jarvis2.remote;
import android.content.*;
import android.view.*;
import java.util.*;

final class ButtonBindings {
    final SharedPreferences prefs;
    ButtonBindings(Context c){prefs=c.getSharedPreferences("button-bindings",Context.MODE_PRIVATE);}
    private String key(String descriptor,int code,String gesture){return descriptor+"|"+code+"|"+gesture;}
    static boolean settingsKey(int code){return code==KeyEvent.KEYCODE_F12||code==KeyEvent.KEYCODE_SETTINGS||code==KeyEvent.KEYCODE_NOTIFICATION;}
    String get(String descriptor,int code,String gesture){
        String fallback="default";
        boolean onn=false;
        for(InputDevice d:devices())if(d.getDescriptor().equals(descriptor)&&d.getVendorId()==0x0957)onn=true;
        if(onn && code==KeyEvent.KEYCODE_F11)fallback=gesture.equals("tap")?"key:26":gesture.equals("hold")?"power":"default";
        if(onn && code==KeyEvent.KEYCODE_F10)fallback=gesture.equals("double")?"default":"key:231";
        if(settingsKey(code))fallback=gesture.equals("tap")?"settings":gesture.equals("double")?"widgets":"bluetooth";
        return prefs.getString(key(descriptor,code,gesture),fallback);
    }
    void set(String descriptor,int code,String gesture,String action){
        SharedPreferences.Editor e=prefs.edit();if(action.equals("default"))e.remove(key(descriptor,code,gesture));else e.putString(key(descriptor,code,gesture),action);e.apply();
    }
    boolean intercept(String descriptor,int code){
        for(String g:new String[]{"tap","double","hold"})if(!get(descriptor,code,g).equals("default"))return true;
        return false;
    }
    void reset(String descriptor,int code){SharedPreferences.Editor e=prefs.edit();for(String g:new String[]{"tap","double","hold"})e.remove(key(descriptor,code,g));e.apply();}
    void resetAll(){prefs.edit().clear().apply();}
    static final String[] ACTIONS={"default","none","voice","voice_settings","settings","bluetooth","widgets","audio","configure","home","back","recents","power",
        "key:23","key:19","key:20","key:21","key:22","key:85","key:127","key:87","key:88","key:24","key:25","key:164","key:26","key:231","key:96","key:97","key:99","key:100","key:102","key:103","key:104","key:105","key:106","key:107","key:108","key:109","key:110"};
    static final String[] LABELS={"Default behavior","Do nothing","Configured voice assistant","Voice assistant settings","Android Settings","Bluetooth menu","Left widgets","Sound output","Button settings","Home","Back","Recent apps","Power menu",
        "Select","D-pad up","D-pad down","D-pad left","D-pad right","Play / pause","Pause","Next track","Previous track","Volume up","Volume down","Mute","Screen on / off","Voice assistant","Controller A","Controller B","Controller X","Controller Y","Controller LB","Controller RB","Controller LT","Controller RT","Left stick press","Right stick press","Controller Start","Controller Select","Controller Guide"};
    static String label(String action){for(int i=0;i<ACTIONS.length;i++)if(ACTIONS[i].equals(action))return LABELS[i];return action.startsWith("app:")?action.substring(4):action;}
    static String buttonName(int code){
        if(settingsKey(code))return "Settings / dashboard";
        if(code==KeyEvent.KEYCODE_F11)return "Power";
        if(code==KeyEvent.KEYCODE_F10)return "Microphone";
        switch(code){case 19:return "D-pad up";case 20:return "D-pad down";case 21:return "D-pad left";case 22:return "D-pad right";case 23:return "Select";case 96:return "A";case 97:return "B";case 99:return "X";case 100:return "Y";}
        return KeyEvent.keyCodeToString(code).replace("KEYCODE_","").replace('_',' ');
    }
    static List<InputDevice> devices(){
        List<InputDevice> result=new ArrayList<>();
        for(int id:InputDevice.getDeviceIds()){
            InputDevice d=InputDevice.getDevice(id);if(d==null||d.isVirtual())continue;
            String n=d.getName().toLowerCase(Locale.ROOT);
            if(n.contains("onn")||n.contains("remote")||d.supportsSource(InputDevice.SOURCE_GAMEPAD))result.add(d);
        }
        result.sort(Comparator.comparing(InputDevice::getName));return result;
    }
    static boolean xbox(InputDevice d){return d!=null&&(d.getVendorId()==0x045e||d.supportsSource(InputDevice.SOURCE_GAMEPAD));}
    static boolean available(InputDevice d,int code){return d!=null&&code>0&&d.hasKeys(code)[0];}
}
