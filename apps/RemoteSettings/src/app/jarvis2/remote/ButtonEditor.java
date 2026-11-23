package app.jarvis2.remote;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.os.Bundle;
import android.preference.*;
import android.view.KeyEvent;
import java.util.*;

public class ButtonEditor extends PreferenceActivity {
    @Override public void onResume(){super.onResume();ButtonRouter.configuring(true);}
    @Override public void onPause(){ButtonRouter.configuring(false);super.onPause();}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        String descriptor=getIntent().getStringExtra("device");int code=getIntent().getIntExtra("code",0);
        if(descriptor==null||code<=0){finish();return;}
        ButtonBindings bindings=new ButtonBindings(this);
        setTitle(ButtonBindings.buttonName(code));
        PreferenceScreen screen=getPreferenceManager().createPreferenceScreen(this);setPreferenceScreen(screen);
        Preference heading=new Preference(this);heading.setTitle(getIntent().getStringExtra("name"));
        heading.setSummary(ButtonBindings.buttonName(code));heading.setSelectable(false);screen.addPreference(heading);
        List<String> actions=new ArrayList<>(Arrays.asList(ButtonBindings.ACTIONS));
        List<String> labels=new ArrayList<>(Arrays.asList(ButtonBindings.LABELS));
        Map<String,String> apps=new TreeMap<>();
        for(String category:new String[]{Intent.CATEGORY_LEANBACK_LAUNCHER,Intent.CATEGORY_LAUNCHER}){
            Intent launch=new Intent(Intent.ACTION_MAIN).addCategory(category);
            for(ResolveInfo app:getPackageManager().queryIntentActivities(launch,0))
                apps.put(app.activityInfo.packageName,app.loadLabel(getPackageManager()).toString());
        }
        for(Map.Entry<String,String> app:apps.entrySet()){actions.add("app:"+app.getKey());labels.add("Open "+app.getValue());}
        for(String gesture:new String[]{"tap","double","hold"}){
            ListPreference p=new ListPreference(this);p.setPersistent(false);
            p.setTitle(gesture.equals("tap")?"Press":gesture.equals("double")?"Double press":"Hold");
            p.setEntries(labels.toArray(new String[0]));p.setEntryValues(actions.toArray(new String[0]));
            p.setValue(bindings.get(descriptor,code,gesture));p.setSummary(p.getEntry());
            p.setOnPreferenceChangeListener((preference,value)->{
                bindings.set(descriptor,code,gesture,value.toString());
                p.setValue(bindings.get(descriptor,code,gesture));p.setSummary(p.getEntry());return false;
            });screen.addPreference(p);
        }
        Preference hint=new Preference(this);hint.setTitle("Gesture timing");
        hint.setSummary("Double press: 300 ms. Hold: 600 ms. Unmapped controls keep their normal behavior.");hint.setSelectable(false);screen.addPreference(hint);
        Preference reset=new Preference(this);reset.setTitle("Reset this button");reset.setOnPreferenceClickListener(p->{bindings.reset(descriptor,code);recreate();return true;});screen.addPreference(reset);
    }
}
