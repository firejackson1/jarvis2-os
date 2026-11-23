package app.jarvis2.remote;

import android.bluetooth.*;
import android.content.*;
import android.media.*;
import android.media.session.*;
import android.os.*;
import android.util.Log;
import android.view.KeyEvent;
import java.lang.reflect.Constructor;
import java.util.*;

/** Owns only an AACP notification socket to connected, bonded AirPods; never takes over audio. */
final class EarDetection {
    private static EarDetection instance;
    static synchronized EarDetection get(Context c){
        if(instance==null)instance=new EarDetection(c.getApplicationContext());
        return instance;
    }
    private final Context context;
    private final BluetoothAdapter adapter;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final SharedPreferences prefs;
    private volatile String currentAddress="";
    private BluetoothProfile a2dp;
    private volatile BluetoothSocket socket;
    private volatile Thread reader;
    private volatile boolean connected;
    private volatile String status="Waiting for AirPods";
    private volatile AirPodsInfo info=new AirPodsInfo();
    private volatile String controlStatus="";
    private AudioFocusRequest duck;
    private final Runnable endConversation=this::stopDucking;
    private void stopDucking(){
        main.removeCallbacks(endConversation);
        if(duck!=null){((AudioManager)context.getSystemService(Context.AUDIO_SERVICE)).abandonAudioFocusRequest(duck);duck=null;Log.i("JarvisAirPods","Conversation ended: released audio ducking");}
    }
    private void conversationEvent(boolean speaking){
        main.removeCallbacks(endConversation);
        if(!speaking||info.conversation()!=1||!connected){stopDucking();return;}
        AudioManager audio=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);
        try{
            if(!isRouted(audio,currentAddress))return;
            if(duck==null){
                AudioFocusRequest request=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                    .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                    .setOnAudioFocusChangeListener(change->{if(change<0)stopDucking();},main).build();
                if(audio.requestAudioFocus(request)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED){duck=request;Log.i("JarvisAirPods","Speaking: transient media ducking requested");}
            }
            main.postDelayed(endConversation,30000);
        }catch(Exception failure){Log.w("JarvisAirPods","Conversation ducking skipped",failure);}
    }
    private final java.util.concurrent.ExecutorService controls=java.util.concurrent.Executors.newSingleThreadExecutor(r->{Thread t=new Thread(r,"JarvisAirPodsControl");t.setDaemon(true);return t;});
    AirPodsInfo info(){return info;}
    boolean available(){return connected;}
    String controlStatus(){return controlStatus;}
    void setNoiseMode(int mode){
        if(mode==1 && info.offAllowed()!=1)sendControl(52,1);
        sendControl(13,mode);
    }
    void setConversation(boolean enabled){if(!enabled)stopDucking();sendControl(40,enabled?1:2);}
    private void sendControl(int id,int value){
        BluetoothSocket active=socket;
        if(!connected||active==null){controlStatus="Connect AirPods first";notifyStatus(status);return;}
        byte[] command=AirPodsInfo.command(id,value);
        controlStatus="Waiting for AirPods confirmation…";notifyStatus(status);
        controls.execute(()->{
            try{synchronized(active){active.getOutputStream().write(command);}}
            catch(Exception failure){controlStatus="Could not send AirPods command";notifyStatus(status);}
        });
        main.postDelayed(()->{
            int actual=id==13?info.mode():id==40?info.conversation():info.offAllowed();
            controlStatus=actual==value?"Confirmed by AirPods":"AirPods did not confirm this setting";
            notifyStatus(status);
        },2500);
    }
    private final Set<Runnable> listeners=new HashSet<>();
    private MediaController pausedByUs;
    private final ResumeState resumeState=new ResumeState();
    private String pausedMedia;
    private final MediaController.Callback playbackWatch=new MediaController.Callback(){
        @Override public void onPlaybackStateChanged(PlaybackState state){
            if(pausedByUs==null||state==null)return;
            resumeState.update(state.getState(),state.getPosition());
        }
        @Override public void onSessionDestroyed(){cancelResume();}
        @Override public void onMetadataChanged(MediaMetadata metadata){
            if(pausedByUs!=null&&!Objects.equals(pausedMedia,mediaIdentity(metadata)))cancelResume();
        }
    };
    private final Runnable poll=this::refresh;
    private final BluetoothProfile.ServiceListener profileListener=new BluetoothProfile.ServiceListener(){
        public void onServiceConnected(int profile,BluetoothProfile proxy){a2dp=proxy;refresh();}
        public void onServiceDisconnected(int profile){a2dp=null;closeSocket();notifyStatus("Waiting for Bluetooth");}
    };
    private EarDetection(Context c){
        context=c;prefs=c.getSharedPreferences("ear-detection",Context.MODE_PRIVATE);
        currentAddress=prefs.getString("last_device","");
        adapter=((BluetoothManager)c.getSystemService(Context.BLUETOOTH_SERVICE)).getAdapter();
        IntentFilter f=new IntentFilter(BluetoothA2dp.ACTION_CONNECTION_STATE_CHANGED);
        f.addAction(BluetoothAdapter.ACTION_STATE_CHANGED);
        c.registerReceiver(new BroadcastReceiver(){public void onReceive(Context c,Intent i){refresh();}},f);
        if(adapter!=null)adapter.getProfileProxy(c,profileListener,BluetoothProfile.A2DP);
        refresh();
    }
    private String prefKey(String name){return currentAddress.isEmpty()?name:name+"."+currentAddress;}
    boolean enabled(){return prefs.getBoolean(prefKey("enabled"),prefs.getBoolean("enabled",true));}
    boolean autoResume(){return prefs.getBoolean(prefKey("resume"),prefs.getBoolean("resume",true));}
    void setAutoResume(boolean value){prefs.edit().putBoolean(prefKey("resume"),value).apply();if(!value)cancelResume();}
    void cancelResume(){
        if(pausedByUs!=null)pausedByUs.unregisterCallback(playbackWatch);
        pausedByUs=null;resumeState.cancel();
    }
    String status(){return enabled()?status:"Automatic pause is off";}
    void setEnabled(boolean value){prefs.edit().putBoolean(prefKey("enabled"),value).apply();if(!value)cancelResume();refresh();}
    void listen(Runnable listener){listeners.add(listener);listener.run();}
    void unlisten(Runnable listener){listeners.remove(listener);}
    private void notifyStatus(String value){
        status=value;
        main.post(()->{for(Runnable r:new ArrayList<>(listeners))r.run();});
    }
    private void closeSocket(){
        main.post(this::cancelResume);main.post(this::stopDucking);
        BluetoothSocket old=socket;socket=null;connected=false;info.disconnected();
        if(old!=null)try{old.close();}catch(Exception ignored){}
    }
    private void refresh(){
        main.removeCallbacks(poll);
        BluetoothDevice target=null;
        if(adapter!=null&&adapter.isEnabled()&&a2dp!=null){
            for(BluetoothDevice d:a2dp.getConnectedDevices())
                if(d.getBondState()==BluetoothDevice.BOND_BONDED && d.getName()!=null
                        && d.getName().toLowerCase(Locale.ROOT).contains("airpods")){
                    // Fail closed if multiple AirPods are connected rather than guessing the active pair.
                    if(target!=null){target=null;break;}target=d;
                }
        }
        if(target==null){closeSocket();notifyStatus(enabled()?"Waiting for connected AirPods":"Automatic pause is off");}
        else if(reader==null){
            BluetoothDevice chosen=target;
            reader=new Thread(()->read(chosen),"JarvisAirPodsWear");reader.setDaemon(true);reader.start();
        }
        if(adapter!=null&&adapter.isEnabled())main.postDelayed(poll,15000);
    }
    private void read(BluetoothDevice device){
        BluetoothSocket candidate=null;
        try{
            Constructor<BluetoothSocket> ctor=BluetoothSocket.class.getDeclaredConstructor(int.class,
                boolean.class,boolean.class,BluetoothDevice.class,int.class,ParcelUuid.class);
            ctor.setAccessible(true);
            candidate=ctor.newInstance(3,true,true,device,4097,
                ParcelUuid.fromString("74ec2172-0bad-4d01-8f77-997b2be0722a"));
            BluetoothSocket active=candidate;socket=active;
            notifyStatus("Connecting to AirPods wear detection…");
            main.postDelayed(()->{if(socket==active&&!connected)try{active.close();}catch(Exception ignored){}},7000);
            active.connect();connected=true;info=new AirPodsInfo();controlStatus="";
            currentAddress=device.getAddress();prefs.edit().putString("last_device",currentAddress).apply();
            active.getOutputStream().write(new byte[]{0,0,4,0,1,0,2,0,0,0,0,0,0,0,0,0});
            active.getOutputStream().write(new byte[]{4,0,4,0,0x4d,0,(byte)0xd7,0,0,0,0,0,0,0});
            active.getOutputStream().write(new byte[]{4,0,4,0,0x0f,0,-1,-1,-1,-1});
            notifyStatus("Connected · waiting for ear state");
            WearState wear=new WearState();byte[] frame=new byte[1024];int count;
            while(socket==active && (count=active.getInputStream().read(frame))>0){
                if(info.read(frame,count)){
                    Log.i("JarvisAirPods","Info battery="+info.level(0)+","+info.level(1)+","+info.level(2)+" mode="+info.mode()+" conversation="+info.conversation());
                    notifyStatus(status);
                }
                int speaking=AirPodsInfo.speaking(frame,count);
                if(speaking>=0)main.post(()->conversationEvent(speaking==1));
                int mask=WearState.mask(frame,count);
                if(mask<0)continue;
                int before=wear.current();
                boolean removed=wear.update(frame,count);
                boolean inserted=before>=0 && (mask&~before)!=0;
                notifyStatus(mask==3?"Both AirPods in ears":mask==0?"AirPods removed":"One AirPod in ear");
                Log.i("JarvisAirPods","Wear mask="+mask+" removed="+removed);
                if(removed && enabled())main.post(()->pauseIfRouted(device.getAddress()));
                else if(inserted && enabled())main.post(()->resumeIfOwned(device.getAddress()));
            }
        }catch(Exception failure){
            if(enabled())notifyStatus("Wear detection unavailable · retrying");
            Log.w("JarvisAirPods","Wear channel: "+failure.getClass().getSimpleName()+": "+failure.getMessage());
        }finally{
            if(socket==candidate)closeSocket();
            else if(candidate!=null)try{candidate.close();}catch(Exception ignored){}
            reader=null;
        }
    }
    private void pauseIfRouted(String address){
        if(!enabled() || !connected)return;
        AudioManager audio=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);
        try{
            if(!isRouted(audio,address)){Log.i("JarvisAirPods","Removal ignored: media uses another output");return;}
            MediaSessionManager sessions=(MediaSessionManager)context.getSystemService(Context.MEDIA_SESSION_SERVICE);
            cancelResume();
            boolean paused=false;
            for(MediaController controller:sessions.getActiveSessions(null)){
                PlaybackState state=controller.getPlaybackState();
                if(state!=null&&(state.getState()==PlaybackState.STATE_PLAYING||state.getState()==PlaybackState.STATE_BUFFERING)){
                    if(autoResume()){
                        pausedByUs=controller;resumeState.arm(SystemClock.elapsedRealtime());
                        pausedMedia=mediaIdentity(controller.getMetadata());
                        controller.registerCallback(playbackWatch,main);
                    }
                    controller.getTransportControls().pause();paused=true;break;
                }
            }
            if(!paused && audio.isMusicActive()){
                audio.dispatchMediaKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_MEDIA_PAUSE));
                audio.dispatchMediaKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,KeyEvent.KEYCODE_MEDIA_PAUSE));
            }
            Log.i("JarvisAirPods","Removal: sent Pause; owned resume="+(pausedByUs!=null));
        }catch(Exception failure){Log.w("JarvisAirPods","Could not safely target playing media",failure);}
    }

    private boolean isRouted(AudioManager audio,String address)throws Exception {
        AudioAttributes attrs=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).build();
        List<?> devices=(List<?>)AudioManager.class.getMethod("getDevicesForAttributes",AudioAttributes.class).invoke(audio,attrs);
        for(Object d:devices){
            int type=(Integer)d.getClass().getMethod("getType").invoke(d);
            String mac=(String)d.getClass().getMethod("getAddress").invoke(d);
            if(type==AudioDeviceInfo.TYPE_BLUETOOTH_A2DP && address.equalsIgnoreCase(mac))return true;
        }
        return false;
    }
    private String mediaIdentity(MediaMetadata metadata){
        if(metadata==null)return "";
        return metadata.getString(MediaMetadata.METADATA_KEY_MEDIA_ID)+"|"
            +metadata.getString(MediaMetadata.METADATA_KEY_TITLE)+"|"+metadata.getLong(MediaMetadata.METADATA_KEY_DURATION);
    }
    private void resumeIfOwned(String address){
        MediaController owner=pausedByUs;
        if(owner==null)return;
        try{
            PlaybackState state=owner.getPlaybackState();
            AudioManager audio=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);
            if(!enabled()||!autoResume()||!connected||state==null
                    ||!resumeState.allows(SystemClock.elapsedRealtime(),state.getState(),state.getPosition())
                    ||!Objects.equals(pausedMedia,mediaIdentity(owner.getMetadata()))||!isRouted(audio,address))return;
            MediaSessionManager sessions=(MediaSessionManager)context.getSystemService(Context.MEDIA_SESSION_SERVICE);
            boolean stillActive=false;
            for(MediaController c:sessions.getActiveSessions(null)){
                if(c.getSessionToken().equals(owner.getSessionToken()))stillActive=true;
                else if(c.getPlaybackState()!=null && c.getPlaybackState().getState()==PlaybackState.STATE_PLAYING)return;
            }
            if(stillActive){owner.getTransportControls().play();Log.i("JarvisAirPods","Insertion: resumed the session paused by ear detection");}
        }catch(Exception failure){Log.w("JarvisAirPods","Resume skipped",failure);}
        finally{cancelResume();}
    }
}
