package app.jarvis2.remote;
import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.media.*;
import android.media.session.*;
import android.media.session.MediaController;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.util.*;

public class WidgetPanel extends Activity {
    private final Handler main=new Handler(Looper.getMainLooper());
    private final Runnable refresh=this::update;
    private LinearLayout body;private TextView title,battery,noise,control;
    private Button play;private Switch conversation;
    private SeekBar volume;
    private final List<Button> mediaButtons=new ArrayList<>(),buttons=new ArrayList<>();
    private Set<String> renderedWidgets;
    private MediaController media;private boolean closed;
    private EarDetection ears;private Runnable earListener;
    private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);ears=EarDetection.get(this);
        ScrollView scroll=new ScrollView(this);scroll.setFocusable(false);scroll.setFillViewport(false);scroll.setVerticalScrollBarEnabled(false);
        body=new LinearLayout(this);body.setOrientation(1);body.setPadding(dp(16),dp(16),dp(16),dp(16));
        GradientDrawable glass=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{0xb3444444,0xc0181818});
        glass.setCornerRadius(dp(22));glass.setStroke(dp(1),0x66ffffff);body.setBackground(glass);
        scroll.addView(body);setContentView(scroll);
        Window w=getWindow();w.setBackgroundDrawableResource(android.R.color.transparent);w.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
        w.setDimAmount(.12f);w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);w.setWindowAnimations(0);
        if(android.os.Build.VERSION.SDK_INT>=31)w.setBackgroundBlurRadius(dp(28));
        WindowManager.LayoutParams p=w.getAttributes();p.width=dp(320);p.height=Math.min(dp(490),getResources().getDisplayMetrics().heightPixels-dp(28));p.x=dp(16);w.setAttributes(p);
        label(body,"Widgets",23);
        Set<String> selected=getSharedPreferences("remote-preferences",MODE_PRIVATE).getStringSet("widgets",new HashSet<>(Arrays.asList("media","airpods","audio")));
        renderedWidgets=new HashSet<>(selected);
        if(selected.contains("media")){
            LinearLayout card=card("Now Playing");title=label(card,"Nothing playing",16);title.setMaxLines(2);title.setEllipsize(android.text.TextUtils.TruncateAt.END);
            LinearLayout row=new LinearLayout(this);card.addView(row);
            mediaButtons.add(action(row,"Previous",()->mediaAction("previous")));play=action(row,"Play / pause",()->mediaAction("toggle"));mediaButtons.add(play);mediaButtons.add(action(row,"Next",()->mediaAction("next")));
        }
        if(selected.contains("airpods")){
            LinearLayout card=card("AirPods");battery=label(card,"Waiting for battery report",14);noise=label(card,"Noise control",14);
            LinearLayout modes=new LinearLayout(this);card.addView(modes);
            action(modes,"ANC",()->ears.setNoiseMode(2));action(modes,"Transparency",()->ears.setNoiseMode(3));
            LinearLayout second=new LinearLayout(this);card.addView(second);
            action(second,"Adaptive",()->ears.setNoiseMode(4));action(second,"Off",()->ears.setNoiseMode(1));
            conversation=new Switch(this);conversation.setText("Conversation Awareness");conversation.setTextColor(Color.WHITE);conversation.setTextSize(13);
            conversation.setThumbTintList(android.content.res.ColorStateList.valueOf(Color.WHITE));conversation.setTrackTintList(android.content.res.ColorStateList.valueOf(0xff888888));card.addView(conversation);
            conversation.setOnClickListener(v->ears.setConversation(conversation.isChecked()));
            control=label(card,"",12);
        }
        if(selected.contains("audio")){
            LinearLayout card=card("Sound output");AudioManager a=(AudioManager)getSystemService(AUDIO_SERVICE);
            volume=new SeekBar(this);volume.setContentDescription("Media volume");volume.setMax(a.getStreamMaxVolume(AudioManager.STREAM_MUSIC));volume.setProgress(a.getStreamVolume(AudioManager.STREAM_MUSIC));volume.setFocusableInTouchMode(true);
            card.addView(volume,new LinearLayout.LayoutParams(-1,dp(38)));
            volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int value,boolean user){if(user)a.setStreamVolume(AudioManager.STREAM_MUSIC,value,0);}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){}});
            action(card,"Choose output / sync",()->startActivity(new Intent(this,Panel.class).putExtra("page","audio")));
        }
        LinearLayout footer=new LinearLayout(this);body.addView(footer);action(footer,"Customize",()->startActivity(new Intent(this,RemotePreferences.class)));action(footer,"Close",this::finish);
        earListener=this::updateAirPods;ears.listen(earListener);update();
        body.post(()->{for(Button b:buttons)if(b.isEnabled()){b.requestFocus();break;}});
        body.setAlpha(0);body.setTranslationX(-dp(14));if(android.animation.ValueAnimator.areAnimatorsEnabled())body.animate().alpha(1).translationX(0).setDuration(180).start();else{body.setAlpha(1);body.setTranslationX(0);}
    }
    private LinearLayout card(String name){LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(10),dp(8),dp(10),dp(10));GradientDrawable b=new GradientDrawable();b.setColor(0x55444444);b.setCornerRadius(dp(14));card.setBackground(b);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(9);body.addView(card,p);label(card,name,17);return card;}
    private TextView label(LinearLayout parent,String text,int size){TextView v=new TextView(this);v.setText(text);v.setTextColor(Color.WHITE);v.setTextSize(size);v.setPadding(0,dp(4),0,dp(5));parent.addView(v);return v;}
    private Button action(LinearLayout parent,String text,Runnable click){Button b=new Button(this);b.setFocusableInTouchMode(true);buttons.add(b);b.setText(text);b.setTextSize(12);b.setTextColor(Color.WHITE);b.setAllCaps(false);b.setPadding(dp(4),0,dp(4),0);b.setMinimumWidth(0);b.setMinWidth(0);GradientDrawable bg=new GradientDrawable();bg.setColor(0x55333333);bg.setCornerRadius(dp(10));bg.setStroke(dp(1),0x66888888);b.setBackground(bg);b.setOnFocusChangeListener((v,f)->bg.setStroke(dp(f?2:1),f?Color.WHITE:0x66888888));b.setOnClickListener(v->click.run());LinearLayout.LayoutParams p=parent.getOrientation()==LinearLayout.HORIZONTAL?new LinearLayout.LayoutParams(0,dp(38),1):new LinearLayout.LayoutParams(-1,dp(38));p.setMargins(dp(2),dp(3),dp(2),dp(3));parent.addView(b,p);return b;}
    private void update(){
        if(closed)return;
        if(title!=null){
            media=null;MediaSessionManager manager=(MediaSessionManager)getSystemService(MEDIA_SESSION_SERVICE);
            for(MediaController c:manager.getActiveSessions(null)){
                PlaybackState state=c.getPlaybackState();if(state!=null&&(state.getState()==PlaybackState.STATE_PLAYING||state.getState()==PlaybackState.STATE_PAUSED)){media=c;break;}
            }
            if(media==null){title.setText("Nothing playing");play.setText("Play / pause");}
            else{MediaMetadata m=media.getMetadata();title.setText(m==null?media.getPackageName():m.getDescription().getTitle());play.setText(media.getPlaybackState().getState()==PlaybackState.STATE_PLAYING?"Pause":"Play");}
        }
        for(Button b:mediaButtons)b.setEnabled(media!=null);
        if(volume!=null&&!volume.isPressed())volume.setProgress(((AudioManager)getSystemService(AUDIO_SERVICE)).getStreamVolume(AudioManager.STREAM_MUSIC));
        updateAirPods();main.removeCallbacks(refresh);main.postDelayed(refresh,1000);
    }
    private void mediaAction(String what){
        if(media==null)return;ears.cancelResume();MediaController.TransportControls c=media.getTransportControls();
        if(what.equals("next"))c.skipToNext();else if(what.equals("previous"))c.skipToPrevious();else if(media.getPlaybackState().getState()==PlaybackState.STATE_PLAYING)c.pause();else c.play();
        main.postDelayed(refresh,150);
    }
    private String percent(AirPodsInfo i,int n){int value=i.level(n);return value<0?"—":value+"%"+(i.charging(n)?" ⚡":i.stale(n)?" (last)":"");}
    private void updateAirPods(){
        if(closed||battery==null)return;AirPodsInfo i=ears.info();
        battery.setText("L "+percent(i,0)+"   R "+percent(i,1)+"\nCase "+percent(i,2));
        String[] modes={"Not reported","Off","ANC","Transparency","Adaptive"};noise.setText("Noise control · "+modes[Math.max(0,i.mode())]);
        conversation.setEnabled(ears.available()&&i.conversation()>0);conversation.setChecked(i.conversation()==1);
        control.setText(ears.available()?ears.controlStatus():"Connect AirPods to use these controls");
    }
    @Override public void onResume(){
        super.onResume();
        Set<String> selected=getSharedPreferences("remote-preferences",MODE_PRIVATE).getStringSet("widgets",new HashSet<>(Arrays.asList("media","airpods","audio")));
        if(renderedWidgets!=null&&!renderedWidgets.equals(selected))recreate();
    }
    @Override public void onDestroy(){closed=true;main.removeCallbacksAndMessages(null);if(earListener!=null)ears.unlisten(earListener);super.onDestroy();}
}
