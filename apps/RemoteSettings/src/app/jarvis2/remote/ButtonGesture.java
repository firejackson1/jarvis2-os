package app.jarvis2.remote;
import java.util.function.Consumer;

/** Per physical button. Caller supplies a monotonic clock and schedules deadline(). */
final class ButtonGesture {
    private final String tap,twice,hold;
    private final Consumer<String> fire;
    private boolean down,held,second,pending;
    private long pressed,singleAt,lastRepeat;
    ButtonGesture(String tap,String twice,String hold,Consumer<String> fire){
        this.tap=tap;this.twice=twice;this.hold=hold;this.fire=fire;
    }
    private void emit(String action){if(!"none".equals(action))fire.accept(action);}
    void down(long now){
        boolean alreadyHeld=held;
        tick(now);
        if(down){
            if(alreadyHeld && "default".equals(hold))emit("default_repeat");
            else if(alreadyHeld && repeats(hold) && now-lastRepeat>=100){lastRepeat=now;emit(hold);}
            return;
        }
        second=pending&&now<=singleAt;pending=false;
        down=true;held=false;pressed=now;
    }
    void up(long now,boolean cancelled){
        if(!down)return;
        if(cancelled){cancel();return;}
        tick(now);down=false;
        if(held){if("default".equals(hold))emit("default_up");}
        else if(!cancelled){
            if(second)emit(twice);
            else if("default".equals(twice))emit(tap);
            else{pending=true;singleAt=now+300;}
        }
        if(cancelled)pending=false;
        held=false;second=false;
    }
    void tick(long now){
        if(down&&!held&&now-pressed>=600){
            held=true;pending=false;lastRepeat=now;
            emit("default".equals(hold)?"default_down":hold);
        }
        if(pending&&!down&&now>=singleAt){pending=false;emit(tap);}
    }
    long deadline(){return down&&!held?pressed+600:pending?singleAt:-1;}
    boolean idle(){return !down&&!pending;}
    void cancel(){if(down&&held&&"default".equals(hold))emit("default_up");down=false;pending=false;held=false;second=false;}
    private boolean repeats(String action){
        return action.equals("key:19")||action.equals("key:20")||action.equals("key:21")
            ||action.equals("key:22")||action.equals("key:24")||action.equals("key:25");
    }
}
