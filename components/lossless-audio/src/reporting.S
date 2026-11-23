.syntax unified
.thumb
.text
.global setup
setup:
 add.w r5,r0,#0xc0
 movs r1,#255
.global report
report:
 ldrb r0,[r5,#-0x4c]
 ldrb r1,[r5,#0x14]
 ldrb r2,[r5,#0x2d]
 orrs r1,r2
 lsls r1,r1,#1
 orrs r0,r1
 ldr r1,[pc,#284]
 add r1,pc
 lsls r0,r0,#4
 adds r1,r1,r0
 mov r0,r4
 movs r2,#255
 .word 0
 .hword 0
