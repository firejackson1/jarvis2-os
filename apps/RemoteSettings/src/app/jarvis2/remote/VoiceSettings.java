package app.jarvis2.remote;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.net.Uri;
import android.os.Bundle;
import android.preference.*;
import android.widget.Toast;
import java.util.*;

/** Provider-owned authentication and capture; Jarvis2 never receives account tokens or audio. */
public class VoiceSettings extends PreferenceActivity {
 static SharedPreferences prefs(Context c){return c.getSharedPreferences("voice-assistant",Context.MODE_PRIVATE);}
 @Override public void onCreate(Bundle state){
  super.onCreate(state);setTitle("Smart Home");
  getPreferenceManager().setSharedPreferencesName("voice-assistant");
  PreferenceScreen screen=getPreferenceManager().createPreferenceScreen(this);setPreferenceScreen(screen);
  ListPreference provider=new ListPreference(this);provider.setKey("provider");provider.setTitle("Assistant provider");
  List<String> values=new ArrayList<>(Arrays.asList("off","system"));
  List<String> labels=new ArrayList<>(Arrays.asList("Not configured","Android default assistant"));
  Map<String,String> apps=new TreeMap<>();
  for(ResolveInfo r:getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_ASSIST),0))
   if(!r.activityInfo.packageName.equals(getPackageName()))apps.put(r.activityInfo.packageName,r.loadLabel(getPackageManager()).toString());
  for(String pkg:new String[]{"io.homeassistant.companion.android","io.homeassistant.companion.android.minimal"})try{
   ApplicationInfo a=getPackageManager().getApplicationInfo(pkg,0);apps.put(pkg,getPackageManager().getApplicationLabel(a).toString());
  }catch(PackageManager.NameNotFoundException ignored){}
  for(Map.Entry<String,String> app:apps.entrySet()){values.add(app.getKey());labels.add(app.getValue());}
  String selected=prefs(this).getString("provider","off");
  if(!values.contains(selected)){values.add(selected);labels.add("Unavailable app · "+selected);}
  provider.setEntries(labels.toArray(new String[0]));provider.setEntryValues(values.toArray(new String[0]));provider.setDefaultValue("off");
  provider.setSummary(labels.get(values.indexOf(selected)));provider.setOnPreferenceChangeListener((p,v)->{provider.setSummary(labels.get(values.indexOf(v.toString())));return true;});screen.addPreference(provider);
  Preference info=new Preference(this);info.setTitle("Use your own account");info.setSummary("Install your preferred assistant app, then sign in there. Home Assistant users choose their own server and Assist pipeline in the Companion app. No account is bundled with this release.");info.setSelectable(false);screen.addPreference(info);
  action(screen,"Open assistant setup","Sign in and configure microphone, reply audio and wake-word options in your assistant app",()->openSetup(this));
  action(screen,"Test configured assistant","Opens the provider’s Assist screen if available; otherwise opens its app",()->launch(this));
  action(screen,"Assign a remote or controller button","Choose Configured voice assistant for press, double press or hold",()->startActivity(new Intent(this,ControllerSettings.class)));
  EditTextPreference server=new EditTextPreference(this);server.setKey("server");server.setTitle("Home Assistant server shortcut (optional)");server.setDialogTitle("Your Home Assistant server");server.setSummary(prefs(this).getString("server", "No server saved · configure your account in the Companion app"));
  server.setOnPreferenceChangeListener((p,v)->{
   try {String address=v.toString().trim().isEmpty()?"":VoiceServer.normalize(v.toString());prefs(this).edit().putString("server",address).apply();server.setText(address);server.setSummary(address.isEmpty()?"No server saved":address);return false;}
   catch(IllegalArgumentException e){Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();return false;}
  });screen.addPreference(server);
  action(screen,"Open server sign-in","Opens your server in an installed browser; this shortcut does not configure the Companion app",()->{
   String address=prefs(this).getString("server","");
   if(address.isEmpty()){Toast.makeText(this,"Enter your server address first",Toast.LENGTH_LONG).show();return;}
   try {startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(VoiceServer.normalize(address))));}catch(Exception e){Toast.makeText(this,"Install a browser or sign in through the Companion app",Toast.LENGTH_LONG).show();}
  });
  action(screen,"Sound output","Choose the TV or connected headphones using Jarvis2 audio controls. Assistant apps control their own audio focus.",()->startActivity(new Intent(this,Panel.class).putExtra("page","audio")));
  Preference limits=new Preference(this);limits.setTitle("Microphone and wake-word support");limits.setSummary("Jarvis2 does not listen in the background. Capture and wake-word support depend on the chosen app. The built-in microphone passed a capture test; the onn remote microphone and speech playback through the remote are not verified. Button gestures launch the app; they are not release-to-stop push-to-talk.");limits.setSelectable(false);screen.addPreference(limits);
  action(screen,"Home Assistant setup guide","Official installation, account, Assist and wake-word instructions",()->{
   try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://www.home-assistant.io/voice_control/android/")));}catch(ActivityNotFoundException e){Toast.makeText(this,"No browser installed",Toast.LENGTH_LONG).show();}
  });
  action(screen,"Forget voice configuration","Clears Jarvis2’s provider and server shortcut. To sign out, also use the assistant app’s account settings.",()->new AlertDialog.Builder(this).setMessage("Clear Jarvis2 voice preferences? Your assistant app account and remote mappings will stay unchanged.").setNegativeButton("Cancel",null).setPositiveButton("Forget",(d,w)->{prefs(this).edit().clear().apply();recreate();}).show());
 }
 private void action(PreferenceScreen screen,String title,String summary,Runnable run){Preference p=new Preference(this);p.setTitle(title);p.setSummary(summary);p.setOnPreferenceClickListener(v->{run.run();return true;});screen.addPreference(p);}
 static void openSetup(Context c){
  String pkg=prefs(c).getString("provider","off");Intent i;
  if(pkg.equals("off")){Toast.makeText(c,"Install and select an assistant provider first",Toast.LENGTH_LONG).show();return;}
  if(pkg.equals("system"))i=new Intent(android.provider.Settings.ACTION_VOICE_INPUT_SETTINGS);
  else {i=c.getPackageManager().getLeanbackLaunchIntentForPackage(pkg);if(i==null)i=c.getPackageManager().getLaunchIntentForPackage(pkg);}
  start(c,i,"The assistant app is unavailable; choose another provider");
 }
 static void launch(Context c){
  String pkg=prefs(c).getString("provider","off");
  if(pkg.equals("off")){start(c,new Intent(c,VoiceSettings.class),"Voice settings unavailable");return;}
  Intent assist=new Intent(Intent.ACTION_ASSIST);if(!pkg.equals("system"))assist.setPackage(pkg);
  if(assist.resolveActivity(c.getPackageManager())!=null){start(c,assist,"Assistant could not open");return;}
  if(pkg.equals("system")){Toast.makeText(c,"Choose an Android default assistant first",Toast.LENGTH_LONG).show();return;}
  openSetup(c);
 }
 private static void start(Context c,Intent i,String error){
  try{if(i==null)throw new ActivityNotFoundException();c.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));}
  catch(ActivityNotFoundException|SecurityException e){Toast.makeText(c,error,Toast.LENGTH_LONG).show();}
 }
 @Override public void onResume(){super.onResume();ButtonRouter.configuring(true);}
 @Override public void onPause(){ButtonRouter.configuring(false);super.onPause();}
}
