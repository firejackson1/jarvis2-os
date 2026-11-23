package app.jarvis2.remote;
import android.content.*;
import android.os.Bundle;
import android.preference.*;
import java.util.*;
public class RemotePreferences extends PreferenceActivity {
    @Override public void onCreate(Bundle state){
        super.onCreate(state);setTitle("Widgets");
        getPreferenceManager().setSharedPreferencesName("remote-preferences");
        PreferenceScreen screen=getPreferenceManager().createPreferenceScreen(this);setPreferenceScreen(screen);
        MultiSelectListPreference widgets=new MultiSelectListPreference(this);widgets.setKey("widgets");widgets.setTitle("Widgets on the left panel");
        widgets.setEntries(new String[]{"Now Playing","AirPods controls","Volume and sound output"});widgets.setEntryValues(new String[]{"media","airpods","audio"});
        widgets.setDefaultValue(new HashSet<>(Arrays.asList("media","airpods","audio")));widgets.setSummary("Choose which cards appear");screen.addPreference(widgets);
        link(screen,"Preview left widget panel","Use button controls to assign its shortcut",WidgetPanel.class);
    }
    private void link(PreferenceScreen screen,String title,String summary,Class<?> cls){Preference p=new Preference(this);p.setTitle(title);p.setSummary(summary);p.setOnPreferenceClickListener(v->{startActivity(new Intent(this,cls));return true;});screen.addPreference(p);}
    @Override public void onResume(){super.onResume();ButtonRouter.configuring(true);}
    @Override public void onPause(){ButtonRouter.configuring(false);super.onPause();}
}
