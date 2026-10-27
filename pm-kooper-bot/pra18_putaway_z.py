"""pra_18 north side: ride Lakilester into the mirror, then swap partner (C-right menu -> other partner) so Laki's
PutAway hop places Mario. How close to z = 0 does Mario's centre get? DIAGNOSTIC SETUP as pra18_laki_z.py."""
import os, sys, json, math
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pz%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dist = lambda p: math.hypot(p['x'] - 717, p['z'] - 70)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 723.0); e.wf32(PLAYER + PS_POS + 8, -25.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 703.0); e.wf32(L['addr'] + 0x40, -25.0)           # DIAGNOSTIC
for i in range(40): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/pz%d_0.st' % os.getpid(); e.save(b0)
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
best = ((-99,),)
for a1 in [int(v) for v in os.environ.get('A1', '60,75,90,105,120').split(',')]:
    for n1 in (15, 30, 45):
        for a2 in (None, 0, 45, 90, 135, 180):
            for n2 in (1, 4, 10):
                for down in (0, 1, 2, 3):
                    e.load(b0)
                    for i in range(n1): e.step(0, *st(a1, 80), 2)
                    s2 = (0, 0) if a2 is None else st(a2, 80)
                    for i in range(n2): e.step(0, *s2, 2)
                    p = player(e); L = laki(); pre = (round(p['z'], 2), round(e.f32(L['addr'] + 0x40), 2))
                    e.step(R_CBUTTON, 0, 0, 2)
                    for i in range(20): e.step(0, 0, 0, 2)
                    for j in range(down):
                        e.step(0, 0, -80, 2)
                        for i in range(5): e.step(0, 0, 0, 2)
                    if down == 0:
                        e.step(0, 0, 80, 2)
                        for i in range(5): e.step(0, 0, 0, 2)
                    e.step(A, 0, 0, 2); zz = (-99,)
                    for i in range(80):
                        e.step(0, 0, 0, 2); p = player(e)
                        if -99 < p['z'] < 0 and p['z'] > zz[0]: zz = (round(p['z'], 3), round(p['x'], 2), round(dist(p), 3), i, p['action'])
                    pid = e.s8(PLAYER_DATA + 0x12)
                    r = (zz, pre, pid, (a1, n1, a2, n2, down))
                    if zz[0] > best[0][0]: best = r; print('new best', r, flush=True)
                    if len(zz) > 2 and zz[2] < 80: print('HIT', r, flush=True)
print('final', best)
