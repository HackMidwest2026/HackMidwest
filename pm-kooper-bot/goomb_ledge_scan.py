"""Goombario walks off the mac_01 west out-of-bounds edge (B held, C-down tattles every 100 frames; he side-steps
off the edge). Saves a state on the frame he leaves the ground, then for K = 0..40 releases B and presses C-down K
game frames into his fall (Mario idle). Logs whether a tattle opened, the partner/input/freeze state, where Goombario
ends up and whether he comes back, plus anything odd 300 frames later. usage: goomb_ledge_scan.py"""
import math, os
from emu import *
from pm import *
from nav import stick_world
EX = -470; ez = EX + 884; OUT = -2
e = Emu('pm-jp.z64', '/dev/shm/pmbot/gls')
e.load(os.environ.get('GSTATE', 'states/mac01_e0_goomb.st')); e.step(0, 0, 0, 2)
mx, mz = EX - OUT / math.sqrt(2), ez + OUT / math.sqrt(2)
e.wf32(PLAYER + PS_POS, mx); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, mz)
gk = [n for n in npcs(e) if n['id'] == -4][0]['addr']
e.wf32(gk + 0x38, mx + 25); e.wf32(gk + 0x3C, 20.0); e.wf32(gk + 0x40, mz - 25)
e.step(0, 0, 0, 200)
s = stick_world(e, 45, 30); e.step(0, s[0], s[1], 2); e.step(0, 0, 0, 60)
def g(): return [n for n in npcs(e) if n['id'] == -4][0]
for f in range(300):
    e.step(B | (D_CBUTTON if f == 20 else 0), 0, 0, 2)
    if not e.u32(g()['addr']) & 0x1000: break
print('Goombario left the ground at', f, g()['y'])
st = '/dev/shm/pmbot/gls_fall.st'; e.save(st)
def state(): q = g(); return dict(gy=round(q['y'], 1), gx=round(q['x'], 1), gz=round(q['z'], 1), grounded=int(bool(e.u32(q['addr']) & 0x1000)),
                                 pstate=e.s8(0x8010ED70), acting=e.s8(0x8010ED73), inDis=e.s8(PLAYER + 0x15), freeze=e.s32(0x8009A5B8), act=player(e)['action'])
for K in [None] + list(range(0, 41, 2)):
    e.load(st); tat = 0
    for f in range(60):
        e.step(D_CBUTTON if f == K else 0, 0, 0, 2)
        if e.s8(0x8010ED70) == 1: tat += 1
    s1 = state()
    e.step(0, 0, 0, 600); s2 = state()
    print('K', K, 'tattle frames', tat, 'after 60', s1, 'after 360', s2, flush=True)
