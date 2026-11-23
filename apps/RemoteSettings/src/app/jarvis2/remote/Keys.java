package app.jarvis2.remote;
import android.accessibilityservice.AccessibilityService;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import android.os.Handler;
import android.content.Intent;
import android.provider.Settings;
public class Keys extends AccessibilityService {
 @Override protected void onServiceConnected(){AudioSync.get(this);EarDetection.get(this);}
 private ButtonRouter router;
 @Override protected boolean onKeyEvent(KeyEvent event){
  int code=event.getKeyCode();
  if(event.getAction()==KeyEvent.ACTION_DOWN && (code==KeyEvent.KEYCODE_MEDIA_PLAY
    ||code==KeyEvent.KEYCODE_MEDIA_PAUSE||code==KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE
    ||code==KeyEvent.KEYCODE_MEDIA_STOP||code==KeyEvent.KEYCODE_MEDIA_NEXT||code==KeyEvent.KEYCODE_MEDIA_PREVIOUS
    ||code==KeyEvent.KEYCODE_HOME||code==KeyEvent.KEYCODE_BACK))EarDetection.get(this).cancelResume();
  if(router==null)router=new ButtonRouter(this);
  return router.onKey(event);
 }
 @Override public void onAccessibilityEvent(AccessibilityEvent event){}
 @Override public void onInterrupt(){if(router!=null)router.clear();}
 @Override public void onDestroy(){if(router!=null)router.destroy();super.onDestroy();}
}
