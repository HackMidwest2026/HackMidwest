"""pra_18: reproduce the -12.707 riding spot (approach 110, alternate tilt 6 deg, mag 80, 6 frames/side, 1 neutral) and
try leaving Laki from there: C-down dismount (holding various directions) and partner swap (PutAway) via C-right.
Tracks Mario's min distance to Clubba 3's trigger point every frame. DIAGNOSTIC SETUP as pra18_alt_ride.py."""
import os, sys, math
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/f127')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dist = lambda p: math.hypot(p['x'] - 717, p['z'] - 70)
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 723.0); e.wf32(PLAYER + PS_POS + 8, -30.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 703.0); e.wf32(L['addr'] + 0x40, -30.0)           # DIAGNOSTIC
for i in range(40): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(25): e.step(0, *st(110, 80), 2)
d, mag, n, gap = 6, 80, 6, 1
spots = []
for f in range(60):
    phase = (f // (n + gap)) % 2; inphase = f % (n + gap) < n
    s = st(d if phase == 0 else 180 - d, mag) if inphase else (0, 0)
    e.step(0, s[0], s[1], 2); p = player(e)
    if p['z'] > -12.75:
        fn = '/dev/shm/pmbot/f127_%d.st' % f; e.save(fn); spots.append((fn, round(p['x'], 2), round(p['z'], 3)))
print('spots at -12.7:', [(s[1], s[2]) for s in spots[:8]], len(spots))
best = ((1e9,),)
for fn, sx_, sz_ in spots[:12]:
    for hold in (None, 90, 0, 180, 45, 135, 270):
        h = (0, 0) if hold is None else st(hold, 80)
        for how in ('dismount', 'swapup', 'swapdown'):
            e.load(fn); m = (1e9,)
            if how == 'dismount':
                e.step(D_CBUTTON, *h, 2); seq = [(D_CBUTTON, h)] + [(0, h)] * 50
                for i in range(50):
                    e.step(0, *h, 2); p = player(e)
                    if p['z'] < 0 and dist(p) < m[0]: m = (dist(p), round(p['x'], 2), round(p['z'], 3), i, p['action'])
            else:
                e.step(R_CBUTTON, *h, 2)
                for i in range(20): e.step(0, 0, 0, 2)
                e.step(0, 0, 80 if how == 'swapup' else -80, 2)
                for i in range(6): e.step(0, 0, 0, 2)
                e.step(A, 0, 0, 2)
                for i in range(80):
                    e.step(0, *h, 2); p = player(e)
                    if p['z'] < 0 and dist(p) < m[0]: m = (dist(p), round(p['x'], 2), round(p['z'], 3), i, p['action'])
            r = (m, sx_, sz_, hold, how)
            if m[0] < best[0][0]: best = r; print('best', r, flush=True)
            if m[0] < 80: print('HIT', r, flush=True)
print('final', best)
