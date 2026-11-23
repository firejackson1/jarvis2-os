package app.jarvis2.remote;

// AACP wear notification: header 04 00 04 00, opcode 06 00, two wear bytes.
// Protocol reference: librepods-org/librepods, data/Packets.kt (ear notification).
final class WearState {
    private int previous=-1;
    int current(){return previous;}
    void reset(){previous=-1;}
    static int mask(byte[] frame,int length){
        if(length!=8 || frame.length<8 || frame[0]!=4 || frame[1]!=0 || frame[2]!=4
                || frame[3]!=0 || frame[4]!=6 || frame[5]!=0)return -1;
        int left=frame[6]&255,right=frame[7]&255;
        if(left>3 || right>3)return -1;
        return (left==0?1:0)|(right==0?2:0);
    }
    boolean update(byte[] frame,int length){
        int current=mask(frame,length);
        if(current<0)return false;
        boolean removed=previous>=0 && (previous&~current)!=0;
        previous=current;
        return removed;
    }
}
