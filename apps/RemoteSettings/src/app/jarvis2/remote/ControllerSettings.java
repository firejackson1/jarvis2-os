package app.jarvis2.remote;
import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.hardware.input.InputManager;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.util.*;

public class ControllerSettings extends Activity implements InputManager.InputDeviceListener {
    private LinearLayout body,diagram,side;private String selected;private InputDevice device;
    private final Set<Integer> placed=new HashSet<>();private InputManager manager;
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    @Override public void onCreate(Bundle s){super.onCreate(s);manager=(InputManager)getSystemService(INPUT_SERVICE);manager.registerInputDeviceListener(this,new Handler());render();}
    @Override public void onResume(){super.onResume();ButtonRouter.configuring(true);if(body!=null)render();}
    @Override public void onPause(){ButtonRouter.configuring(false);super.onPause();}
    private void render(){
        List<InputDevice> devices=ButtonBindings.devices();device=null;
        for(InputDevice d:devices)if(d.getDescriptor().equals(selected))device=d;
        if(device==null&&!devices.isEmpty()){device=devices.get(0);selected=device.getDescriptor();}
        ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);body.setGravity(Gravity.CENTER_HORIZONTAL);body.setPadding(dp(24),dp(16),dp(24),dp(24));scroll.addView(body);setContentView(scroll);
        text("Remote & controller buttons",22);text("Select a button to change its press, double-press and hold actions",13);
        LinearLayout chooser=new LinearLayout(this);chooser.setGravity(Gravity.CENTER);body.addView(chooser);
        for(InputDevice d:devices){Button b=new Button(this);b.setText(d.getName());b.setOnClickListener(v->{selected=d.getDescriptor();render();});chooser.addView(b);}
        if(device==null){text("Connect an onn remote or Xbox controller to configure its buttons.",18);return;}
        LinearLayout content=new LinearLayout(this);content.setGravity(Gravity.TOP|Gravity.CENTER_HORIZONTAL);body.addView(content);
        diagram=new LinearLayout(this);diagram.setOrientation(1);diagram.setPadding(dp(10),dp(10),dp(10),dp(10));
        GradientDrawable shell=new GradientDrawable();shell.setColor(0xff17191d);shell.setCornerRadius(dp(ButtonBindings.xbox(device)?28:44));shell.setStroke(dp(1),0xff505358);diagram.setBackground(shell);
        content.addView(diagram,new LinearLayout.LayoutParams(-2,-2));
        side=new LinearLayout(this);side.setOrientation(1);LinearLayout.LayoutParams sideSize=new LinearLayout.LayoutParams(dp(250),-2);sideSize.leftMargin=dp(24);content.addView(side,sideSize);
        textIn(side,device.getName(),19);textIn(side,ButtonBindings.xbox(device)?"Xbox / gamepad layout":"onn remote layout",14);
        textIn(side,"Bright buttons are reported by this device. Select one to edit its actions. Mappings are paused while this settings screen is open.",14);
        placed.clear();
        if(ButtonBindings.xbox(device)){
            row(102,"LB",104,"LT",109,"Select",108,"Start",105,"RT",103,"RB");
            row(0,"",110,"Xbox / guide",0,"");
            row(19,"↑",0,"",100,"Y");
            row(21,"←",23,"D-pad",22,"→",99,"X",97,"B");
            row(20,"↓",106,"L-stick",107,"R-stick",96,"A");
        }else{
            row(ButtonBindings.available(device,141)?141:26,"Power",ButtonBindings.available(device,140)?140:231,"Mic",code("PROFILE_SWITCH"),"Profile");
            row(0,"",19,"↑",0,"");row(21,"←",23,"Select",22,"→");row(0,"",20,"↓",0,"");
            row(4,"Back",3,"Home",142,"Settings");row(25,"Vol −",164,"Mute",24,"Vol +");
            row(178,"TV input",code("MACRO_1"),"Free TV",code("FEATURED_APP_1"),"Live TV");
            row(190,"YouTube",191,"Netflix",196,"Disney+",197,"Paramount+");
        }
        List<Integer> extra=new ArrayList<>();for(int c=1;c<=KeyEvent.getMaxKeyCode();c++)if(!placed.contains(c)&&ButtonBindings.available(device,c))extra.add(c);
        if(!extra.isEmpty()){
            Button other=new Button(this);other.setText("Other reported buttons ("+extra.size()+")");
            String[] names=extra.stream().map(ButtonBindings::buttonName).toArray(String[]::new);
            other.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Other reported buttons").setItems(names,(d,n)->edit(extra.get(n))).show());side.addView(other);
        }
        textIn(side,"Dim buttons are unavailable to Android on this device; TV/IR controls stay with the TV.",12);
        Button settings=new Button(this);settings.setText("Widget and shortcut settings");settings.setOnClickListener(v->startActivity(new Intent(this,RemotePreferences.class)));side.addView(settings);
        Button reset=new Button(this);reset.setText("Reset all button actions");reset.setOnClickListener(v->new AlertDialog.Builder(this).setMessage("Restore normal button behavior and the standard Settings shortcuts?").setNegativeButton("Cancel",null).setPositiveButton("Reset",(d,w)->{new ButtonBindings(this).resetAll();render();}).show());side.addView(reset);
    }
    private void edit(int code){startActivity(new Intent(this,ButtonEditor.class).putExtra("device",device.getDescriptor()).putExtra("code",code).putExtra("name",device.getName()));}
    private void textIn(LinearLayout parent,String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setPadding(0,dp(5),0,dp(9));parent.addView(t);}
    private int code(String name){return KeyEvent.keyCodeFromString("KEYCODE_"+name);}
    private void text(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setGravity(Gravity.CENTER);t.setPadding(0,dp(5),0,dp(5));body.addView(t);}
    private void row(Object... items){
        LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER);
        for(int i=0;i<items.length;i+=2){int c=(Integer)items[i];String name=(String)items[i+1];
            if(c<=0){row.addView(new View(this),new LinearLayout.LayoutParams(dp(76),dp(34)));continue;}
            placed.add(c);Button b=new Button(this);b.setText(name);b.setTextSize(12);b.setAllCaps(false);b.setTextColor(Color.WHITE);b.setPadding(dp(3),0,dp(3),0);
            boolean available=ButtonBindings.available(device,c);b.setEnabled(available);b.setAlpha(available?1f:0.22f);
            GradientDrawable background=new GradientDrawable();background.setColor(0xff292c30);background.setCornerRadius(dp(16));background.setStroke(dp(1),0xff66696d);b.setBackground(background);
            b.setOnFocusChangeListener((v,focus)->{background.setStroke(dp(focus?3:1),focus?Color.WHITE:0xff66696d);b.setScaleX(focus?1.05f:1);b.setScaleY(focus?1.05f:1);});
            b.setContentDescription(name+(available?" · configure button":" · not reported"));
            b.setOnClickListener(v->edit(c));b.setFocusableInTouchMode(true);if(c==23&&available)b.post(b::requestFocus);
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(76),dp(34));p.setMargins(dp(4),dp(3),dp(4),dp(3));row.addView(b,p);
        }diagram.addView(row);
    }
    public void onInputDeviceAdded(int id){render();}public void onInputDeviceRemoved(int id){render();}public void onInputDeviceChanged(int id){render();}
    @Override public void onDestroy(){manager.unregisterInputDeviceListener(this);super.onDestroy();}
}
