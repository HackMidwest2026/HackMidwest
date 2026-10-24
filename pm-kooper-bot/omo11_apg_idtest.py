"""DIAGNOSTIC ONLY (RAM write): with the APG menu open, write userIndex[0]=ID and enabled[0]=EN, press down, A,
then A through the prompts. Reports curPartner and whether the game keeps running. usage: omo11_apg_idtest.py ID [EN]"""
import os, sys
from emu import *
from pm import *
ID = int(sys.argv[1], 0); EN = int(sys.argv[2], 0) if len(sys.argv) > 2 else 1
e = Emu('pm-jp.z64', '/dev/shm/pmbot/id%d' % os.getpid())
e.load(os.environ.get('POPUP', '/tmp/claude-0/pm/pipe/base/popup.st')); e.step(0, 0, 0, 2)
p = e.u32(0x8010D85C)
e.w32(p + 0x108, ID & 0xFFFFFFFF); e.w32(p + 0x18C, EN)
for kv in filter(None, os.environ.get("EXTRA", "").split(",")):   # extra fields: off=value
    o, v = kv.split("="); e.w32(p + int(o, 16), int(v, 16))
for i in range(40): e.step(0, 0, 0, 2)
for i in range(2): e.step(0, 0, -80, 1)
for i in range(10): e.step(0, 0, 0, 2)
print('cursor moved', flush=True)
for i in range(2): e.step(A, 0, 0, 1)
print('pressed A', flush=True)
for f in range(600):
    e.step(A if (f > 100 and f % 30 == 0) else 0, 0, 0, 2)
    if f % 100 == 99: print('step', f + 1, 'curPartner', e.s8(PLAYER_DATA + 0x12), 'mode', e.s16(GAME_MODE), flush=True)
print('ALIVE curPartner', e.s8(PLAYER_DATA + 0x12), flush=True)
