package app.jarvis2.remote;

import java.util.Locale;

final class HdmiCaps {
    static final int AC3=1, EAC3=2, DTS=4, DTSHD=8, TRUEHD=16, JOC=32, LOSSLESS=DTSHD|TRUEHD;
    static int parse(String text) {
        int result=0;
        for(String line:text.toUpperCase(Locale.ROOT).split("\n")) {
            line=line.trim();
            if(line.startsWith("AC-3,")) result|=AC3;
            if(line.startsWith("DOLBY_DIGITAL+,")) {
                result|=EAC3;
                if(line.matches(".*DEPVALUE\\s+0X[0-9A-F]*[13579BDF]\\s*")) result|=JOC;
            }
            if(line.startsWith("DTS,")) result|=DTS;
            if(line.startsWith("DTS-HD,")||line.startsWith("DTS_HD,")) result|=DTSHD;
            if(line.startsWith("MAT,")||line.startsWith("MLP,")||line.startsWith("TRUEHD,")
                    ||line.startsWith("DOLBY_TRUEHD,")) result|=TRUEHD;
        }
        return result;
    }
    static String describe(int caps) {
        StringBuilder result=new StringBuilder();
        String[] names={"Dolby Digital", "Dolby Digital Plus", "DTS", "DTS-HD / DTS:X", "TrueHD / Atmos", "DD+ Atmos"};
        for(int i=0;i<names.length;i++) if((caps&(1<<i))!=0) {
            if(result.length()>0)result.append("\n");
            result.append(names[i]);
        }
        return result.length()==0?"No encoded surround formats reported":result.toString();
    }
    static int parseHal(String reply) {
        int result=0;
        for(String segment:reply.toLowerCase(Locale.ROOT).split(";")) {
            String[] pair=segment.trim().split("=",2);
            if(pair.length>1 && !pair[1].isEmpty() && !pair[1].equals("1") && !pair[1].equals("true"))continue;
            switch(pair[0]) {
                case "ac3": result|=AC3; break;
                case "eac3": result|=EAC3; break;
                case "dts": result|=DTS; break;
                case "dtshd": case "dts_hd": result|=DTSHD; break;
                case "truehd": case "mat": result|=TRUEHD; break;
                case "eac3-joc": case "eac3_joc": result|=JOC; break;
            }
        }
        return result;
    }
}
