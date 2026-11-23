package app.jarvis2.remote;

/** Bounded AACP protocol decoding; unknown/disconnected values never become fake percentages. */
final class AirPodsInfo {
    private final int[] levels={-1,-1,-1},statuses={4,4,4};
    private int mode=-1,conversation=-1,off=-1;
    synchronized int level(int i){return levels[i];}
    synchronized boolean charging(int i){return statuses[i]==1||statuses[i]==5;}
    synchronized boolean stale(int i){return statuses[i]==4;}
    synchronized int mode(){return mode;}
    synchronized int conversation(){return conversation;}
    synchronized int offAllowed(){return off;}
    synchronized void disconnected(){for(int i=0;i<3;i++)statuses[i]=4;}
    synchronized boolean read(byte[] b,int n){
        if(n<6||n>b.length||b[0]!=4||b[1]!=0||b[2]!=4||b[3]!=0||b[5]!=0)return false;
        if(b[4]==4&&n==22&&(b[6]&255)==3){
            boolean[] seen=new boolean[3];
            for(int o:new int[]{7,12,17}){
                int i=component(b[o]&255),level=b[o+2]&255,status=b[o+3]&255;
                if(i<0||seen[i]||(status!=1&&status!=2&&status!=4&&status!=5)||(level>100&&status!=4))return false;
                seen[i]=true;
            }
            for(int o:new int[]{7,12,17}){int i=component(b[o]&255);statuses[i]=b[o+3]&255;if(statuses[i]!=4)levels[i]=b[o+2]&255;}
            return true;
        }
        if(b[4]==9&&n==11){
            int id=b[6]&255,value=b[7]&255;
            if(b[8]!=0||b[9]!=0||b[10]!=0)return false;
            if(id==13&&value>=1&&value<=4)mode=value;
            else if(id==40&&(value==1||value==2))conversation=value;
            else if(id==52&&(value==1||value==2))off=value;
            else return false;
            return true;
        }
        return false;
    }
    private int component(int code){return code==4?0:code==2?1:code==8?2:-1;}
    static int speaking(byte[] b,int n){
        if(n!=10||b.length<n||b[0]!=4||b[1]!=0||b[2]!=4||b[3]!=0||b[4]!=0x4b||b[5]!=0||b[6]!=2||b[7]!=0)return -1;
        int state=b[9]&255;return state==1||state==2?1:state==6||state==8||state==9?0:-1;
    }
    static byte[] command(int id,int value){
        if((id!=13&&id!=40&&id!=52)||value<1||value>(id==13?4:2))throw new IllegalArgumentException("Unsupported control");
        return new byte[]{4,0,4,0,9,0,(byte)id,(byte)value,0,0,0};
    }
}
