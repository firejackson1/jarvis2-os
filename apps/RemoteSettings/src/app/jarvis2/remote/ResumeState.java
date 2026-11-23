package app.jarvis2.remote;

/** A duplicate paused-state report is not a user command. */
final class ResumeState {
    private boolean armed,waiting;
    private long started,position;
    void arm(long now){armed=true;waiting=true;started=now;}
    void cancel(){armed=false;waiting=false;}
    void update(int state,long pos){
        if(!armed)return;
        if(waiting && state==2){waiting=false;position=pos;}
        else if(!waiting && (state!=2 || Math.abs(pos-position)>250))cancel();
        else if(waiting && state!=2 && state!=3 && state!=6)cancel();
    }
    boolean allows(long now,int state,long pos){
        return armed&&!waiting&&now>=started&&now-started<=120000&&state==2&&Math.abs(pos-position)<=250;
    }
}
