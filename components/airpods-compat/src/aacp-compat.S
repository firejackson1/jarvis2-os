.syntax unified
.thumb
.text
.global compat
compat:
 ldr r0,[r4,#0x3c]
 ldrh r1,[r0,#4]
 movw r2,#0x1001
 cmp r1,r2
 ite eq
 moveq r5,#1
 movne r5,#0
 movs r1,#0
 strb.w r1,[r0,#0x40]
 .hword 0
