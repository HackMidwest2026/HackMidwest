"""Goombario tattle timed against a loading zone (nok_13 west exit). Mario walks west from the entry; C-down on game
frame C. Logs when the map change starts, the partner / input / freeze state after arriving in the next map, and
whether Mario can move there (walk 30 frames east, distance moved). usage: goomb_lz_tattle.py C0 C1"""
import sys, math
from emu import *
from pm import *
from nav import stick_world
ENC, PSTAT, FREEZE = 0x8009A5E0, 0x8010ED70, 0x8009A5B8
e = Emu('pm-jp.z64', '/dev/shm/pmbot/glz')
e.load('states/nok13_e0_goomb.st'); e.step(0, 0, 0, 20)
s0 = stick_world(e, 90); e.step(0, s0[0], s0[1], 40); e.step(0, 0, 0, 80)   # walk 20 game frames east first
base = '/dev/shm/pmbot/glz.st'; e.save(base)
def run(C):
    e.load(base); ch = None
    for f in range(400):
        st = stick_world(e, 270) if (C is None or f < C) else (0, 0)
        if ch is not None: st = (0, 0)
        e.step(D_CBUTTON if f == C else 0, st[0], st[1], 2)
        if ch is None and (e.s16(GAME_MODE) != 4 or e.u32(PLAYER + 4) & 0x00002000 == 0 and False): pass
        if ch is None and e.s16(GAME_MODE) == 5: ch = f
        if ch is not None and e.s16(GAME_MODE) == 4 and f > ch + 30: break
    e.step(0, 0, 0, 120)
    w = where(e); p0 = player(e); pst = (e.s8(PSTAT), e.s8(PLAYER + 0x15), e.s32(FREEZE))
    s = stick_world(e, 90); e.step(0, s[0], s[1], 60); p1 = player(e)
    return ch, w, pst, round(math.hypot(p1['x'] - p0['x'], p1['z'] - p0['z']), 1)
print('baseline', run(None))
for C in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    print('C', C, run(C), flush=True)
