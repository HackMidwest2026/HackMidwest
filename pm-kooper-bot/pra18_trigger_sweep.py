"""pra_18: how close can Mario get, from the NORTH side, to Clubba 3's talk/battle trigger (IsPlayerWithin(717,70,80))?
DIAGNOSTIC SETUP: Mario placed on foot at START with Lakilester; everything after is real input. For each method and
stick angle, tracks Mario's dist2D to (717,70) every frame (the trigger script checks every frame)."""
import os, sys, json, math
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ts%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dist = lambda p: math.hypot(p['x'] - 717, p['z'] - 70)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 720.0); e.wf32(PLAYER + PS_POS + 8, -35.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 700.0); e.wf32(L['addr'] + 0x40, -35.0)           # DIAGNOSTIC
for i in range(40): e.step(0, 0, 0, 2)
foot = '/dev/shm/pmbot/ts%d_foot.st' % os.getpid(); e.save(foot)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
ride = '/dev/shm/pmbot/ts%d_ride.st' % os.getpid(); e.save(ride)
best = {}
def track(tag, seq, st):
    e.load(st); m = (1e9, None)
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2); p = player(e); d = dist(p)
        if d < m[0]: m = (d, (round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), p['action'], k))
    if tag not in best or m[0] < best[tag][0]: best[tag] = (m[0], m[1], seq[:m[1][4] + 1] if m[1] else None)
    return m
stick = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
for deg in range(0, 91, 5):
    for mag in (30, 55, 80):
        sx, sy = stick(deg, mag)
        track('walk/run hold', [(0, sx, sy)] * 80, foot)
        track('ride hold', [(0, sx, sy)] * 80, ride)
        for k in (10, 20, 30, 40, 60):
            track('ride hold then C-down (dismount) still holding', [(0, sx, sy)] * k + [(D_CBUTTON, sx, sy)] + [(0, sx, sy)] * 40, ride)
            track('ride hold then dismount + remount', [(0, sx, sy)] * k + [(D_CBUTTON, sx, sy)] + [(0, sx, sy)] * 25 + [(D_CBUTTON, 0, 0)] + [(0, 0, 0)] * 40, ride)
            track('hold then jump (A)', [(0, sx, sy)] * k + [(A, sx, sy)] * 12 + [(0, sx, sy)] * 30, foot)
            track('hold then spin (Z)', [(0, sx, sy)] * k + [(Z, sx, sy)] + [(0, sx, sy)] * 40, foot)
            track('hold on foot then C-down mount', [(0, sx, sy)] * k + [(D_CBUTTON, 0, 0)] + [(0, 0, 0)] * 40, foot)
    print(deg, {k: round(v[0], 2) for k, v in best.items()}, flush=True)
json.dump({k: [v[0], v[1], v[2]] for k, v in best.items()}, open('/tmp/claude-0/pm/p18/trigger_sweep.json', 'w'))
for k, v in sorted(best.items(), key=lambda kv: kv[1][0]): print('%-50s %.2f at %s' % (k, v[0], v[1]))
