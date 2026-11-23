#include <stdint.h>
extern int printf(const char *, ...);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern const char *dlerror(void);
extern int dlclose(void *);
static uint8_t carrier[8192], raw[65536];
int main(int argc, char **argv) {
    void *lib=dlopen(argc>1?argv[1]:"/dev/jarvis-lossless/libHwAudio_dtshd.so",2);
    if(!lib){printf("dlopen failed: %s\n",dlerror());return 1;}
    int (*process)(const uint8_t *,int,int *,uint8_t *,int *,int *,uint8_t *,int *)=dlsym(lib,"dca_decoder_process");
    int (*init)(int,int)=dlsym(lib,"dca_decoder_init");
    int (*done)(void)=dlsym(lib,"dca_decoder_deinit");
    if(!process||!init||!done||init(0,0)!=0)return 2;
    uint8_t packet[16]={0x7f,0xfe,0x80,0x01,1,2,3,4,5,6,7,8,9,10,11,12};
    int consumed=0,pcm=0,bytes=0,fmt[2]={0};
    if(process(packet,16,&consumed,carrier,&pcm,fmt,raw,&bytes)!=16)return 3;
    if(consumed!=16||pcm!=8192||bytes!=32768||fmt[0]!=192000||fmt[1]!=2)return 4;
    for(int i=0;i<16;i++)if(raw[(20+i)^1]!=packet[i])return 5;
    done();dlclose(lib);
    printf("Android ARM32: library load, stock ABI, HBR frame and exact payload preservation passed\n");
    return 0;
}
