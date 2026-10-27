"""pra_18: user's technique ON LAKILESTER: ride into the mirror near x 723, then alternate stick right-slightly-down
and left-slightly-down. Riding speed is 3 (stick < 55) or 6 (> 55). Sweep approach, tilt, magnitude, frames per side,
neutral gap; 240 frames each; also try a C-down dismount at the best frame. Track Mario's (and Laki's) max z.
DIAGNOSTIC SETUP: Mario placed on foot at (723,-30) with Laki; mount + all later frames are real input.
usage: pra18_alt_ride.py PART NPARTS"""
import os, sys, math, json, itertools
from emu import *
from pm import *
part, nparts = int(sys.argv[1]), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ar%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dist = lambda p: math.hypot(p['x'] - 717, p['z'] - 70)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 723.0); e.wf32(PLAYER + PS_POS + 8, -30.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 703.0); e.wf32(L['addr'] + 0x40, -30.0)           # DIAGNOSTIC
for i in range(40): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
assert player(e)['action'] == 33
b0 = '/dev/shm/pmbot/ar%d_0.st' % os.getpid(); e.save(b0)
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
appr = {}
for a in (90, 70, 110):                    # approach: hold toward the mirror at this angle 25 frames
    e.load(b0)
    for i in range(25): e.step(0, *st(a, 80), 2)
    fn = '/dev/shm/pmbot/ar%d_a%d.st' % (os.getpid(), a); e.save(fn); appr[a] = fn
    print('approach', a, 'mario z %.3f laki z %.3f' % (player(e)['z'], e.f32(laki()['addr'] + 0x40)), flush=True)
combos = list(itertools.product(appr, (1, 3, 6, 10, 15, 20, 30, 45), (20, 80), (1, 2, 3, 4, 6, 10), (0, 1)))[part::nparts]
best = (-99,); res = []
for a, d, mag, n, gap in combos:
    e.load(appr[a]); m = (-99,); bestf = None
    for f in range(240):
        phase = (f // (n + gap)) % 2; inphase = f % (n + gap) < n
        s = st(d if phase == 0 else 180 - d, mag) if inphase else (0, 0)
        e.step(0, s[0], s[1], 2); p = player(e)
        if -99 < p['z'] < 0 and p['z'] > m[0]:
            m = (p['z'], p['x'], dist(p), f, e.f32(laki()['addr'] + 0x40))
    r = (round(m[0], 4), round(m[1], 2), round(m[2], 3), m[3], round(m[4], 3), a, d, mag, n, gap); res.append(r)
    if m[0] > best[0]: best = r; print('best', r, flush=True)
    if m[2] < 80: print('HIT', r, flush=True)
json.dump(res, open('/tmp/claude-0/pm/p18/alt_ride_%d.json' % part, 'w')); print('final', best)
