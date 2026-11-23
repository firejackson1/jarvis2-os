package app.jarvis2.remote;
import android.app.AlertDialog;
import android.app.role.RoleManager;
import android.content.*;
import android.content.pm.*;
import android.os.Bundle;
import android.preference.*;
import android.widget.Toast;
import java.util.*;
import java.util.function.Consumer;

/** Uses Android's HOME role; never disables/uninstalls any launcher. */
public class LauncherSettings extends PreferenceActivity {
 private RoleManager roles;
 @Override public void onCreate(Bundle state){super.onCreate(state);roles=getSystemService(RoleManager.class);setTitle("Home screen");}
 @Override public void onResume(){super.onResume();ButtonRouter.configuring(true);render();}
 @Override public void onPause(){ButtonRouter.configuring(false);super.onPause();}
 private void render(){
  PreferenceScreen screen=getPreferenceManager().createPreferenceScreen(this);setPreferenceScreen(screen);
  List<String> holders=new ArrayList<>();
  ResolveInfo current=getPackageManager().resolveActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME),PackageManager.MATCH_DEFAULT_ONLY);
  if(current!=null)holders.add(current.activityInfo.packageName);
  Preference info=new Preference(this);info.setTitle("Choose your Home screen");info.setSummary("Select a launcher to make it the default. All other launchers stay installed so you can switch back here.");info.setSelectable(false);screen.addPreference(info);
  Map<String,ResolveInfo> homes=new TreeMap<>();
  for(ResolveInfo r:getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME),PackageManager.MATCH_DEFAULT_ONLY)){
   if(r.activityInfo.packageName.equals("com.android.tv.settings"))continue;
   homes.put(r.activityInfo.packageName,r);
  }
  for(ResolveInfo r:homes.values()){
   String pkg=r.activityInfo.packageName,label=r.loadLabel(getPackageManager()).toString();
   Preference p=new Preference(this);p.setTitle(label);p.setIcon(r.loadIcon(getPackageManager()));
   p.setSummary(holders.contains(pkg)?"Current default":"Select as default Home screen");
   p.setOnPreferenceClickListener(v->{new AlertDialog.Builder(this).setTitle(label).setMessage("Use this launcher when you press Home? You can switch back in Settings → Home screen.").setNegativeButton("Cancel",null).setNeutralButton("Preview",(d,w)->startActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).setComponent(new ComponentName(pkg,r.activityInfo.name)))).setPositiveButton("Use launcher",(d,w)->choose(pkg)).show();return true;});screen.addPreference(p);
  }
 }
 private void choose(String pkg){
  try{
   Consumer<Boolean> done=ok->{android.util.Log.i("JarvisHome","Home role update accepted="+ok+" package="+pkg);Toast.makeText(this,ok?"Default Home updated":"Android rejected the launcher change",Toast.LENGTH_LONG).show();render();};
   RoleManager.class.getMethod("addRoleHolderAsUser",String.class,String.class,int.class,android.os.UserHandle.class,java.util.concurrent.Executor.class,Consumer.class)
    .invoke(roles,RoleManager.ROLE_HOME,pkg,0,android.os.Process.myUserHandle(),getMainExecutor(),done);
  }catch(Exception failure){Toast.makeText(this,"Could not change Home. Your previous launcher remains selected.",Toast.LENGTH_LONG).show();android.util.Log.e("JarvisHome","Home role change failed",failure);}
 }
}
