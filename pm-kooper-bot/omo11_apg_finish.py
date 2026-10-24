"""From under the Super Block: jump into it right away, A through the text, then down, A on the partner menu,
A through the prompts, and stop 60 frames (2 s) after curPartner changes. usage: omo11_apg_finish.py START.st"""
import os, sys
from emu import *
from pm import *
POP = 0x8010D85C
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fin%d' % os.getpid())
e.load(sys.argv[1]); e.step(0, 0, 0, 2)
p0 = e.s8(PLAYER_DATA + 0x12)
for i in range(6): e.step(A, 0, 0, 2)
p = 0
for f in range(900):
    p = e.u32(POP)
    if 0x80000000 < p < 0x80800000 and e.s32(p + 0x318) == 4 and e.s32(p + 0x324) == 0: break
    e.step(A if f % 8 == 0 else 0, 0, 0, 2)
print('menu at %08x id %d enabled %08x' % (p, e.u32(p + 0x108), e.u32(p + 0x18C)), flush=True)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(2): e.step(0, 0, -80, 1)
for i in range(10): e.step(0, 0, 0, 2)
for i in range(2): e.step(A, 0, 0, 1)
for f in range(1200):
    if e.s8(PLAYER_DATA + 0x12) != p0: break
    e.step(A if (f > 20 and f % 30 == 0) else 0, 0, 0, 2)
print('curPartner', p0, '->', e.s8(PLAYER_DATA + 0x12), 'after', f, 'steps', flush=True)
for i in range(30): e.step(0, 0, 0, 2)          # 2 more seconds (60 frames)
print('end curPartner', e.s8(PLAYER_DATA + 0x12), flush=True)
