"""Greedy Laki push in isk_11 (no position edits): from the history-full state (Laki idle, follow target frozen near
the start just left of the leftmost pedestal), each cycle tries a set of short stick taps (world direction, tilt,
frames held, frames waited) and keeps the one that moves Laki furthest from the frozen target (weighted toward +x,
the right side of the room) while the follow state stays 5 and the target is unchanged. Saves the end state.
usage: isk11_greedy_push.py RING.st OUT.st [CYCLES]   env GOAL=x,z (push Laki toward that point instead of
maximising x)"""
import math, sys
from emu import *
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
ring, outp = sys.argv[1], sys.argv[2]; CYC = int(sys.argv[3]) if len(sys.argv) > 3 else 200
e = Emu('pm-jp.z64', '/dev/shm/pmbot/igp')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load(ring); e.step(0, 0, 0, 2)
ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
def intact(): return e.u32(PTR) == ptr0 and (e.u32(STATE) >> 16) == 5 and e.f32(HIST + 16 * ptr0 + 4) == tx and e.f32(HIST + 16 * ptr0 + 12) == tz
import os
GOAL = tuple(float(v) for v in os.environ['GOAL'].split(',')) if os.environ.get('GOAL') else None
def score(l):
    if GOAL: return -math.hypot(l['x'] - GOAL[0], l['z'] - GOAL[1]) + 0.05 * math.hypot(l['x'] - tx, l['z'] - tz)
    return (l['x'] - tx) + 0.1 * math.hypot(l['x'] - tx, l['z'] - tz)
ACTS = [(d, t, h, w) for d in (0, 30, -30, 60, -60, 90, -90, 150, 180, -150) for t in (20, 45, 80) for h in (1, 2) for w in (2, 8)]
cur = '/dev/shm/pmbot/igp_cur.st'; e.save(cur); best_s = score(laki()); stall = 0
for c in range(CYC):
    cand = None
    for (d, t, h, w) in ACTS:
        e.load(cur)
        for i in range(h): e.step(0, *stick_for(d % 360, t), 2)
        for i in range(w): e.step(0, 0, 0, 2)
        if not intact(): continue
        s = score(laki())
        if cand is None or s > cand[0]: cand = (s, (d, t, h, w))
    if cand is None: print('no intact action at cycle', c); break
    d, t, h, w = cand[1]
    e.load(cur)
    for i in range(h): e.step(0, *stick_for(d % 360, t), 2)
    for i in range(w): e.step(0, 0, 0, 2)
    e.save(cur)
    p, l = player(e), laki()
    stall = stall + 1 if cand[0] <= best_s + 0.05 else 0
    best_s = max(best_s, cand[0])
    if c % 10 == 0: print(c, 'act', cand[1], 'M (%.1f %.1f %.1f) L (%.1f %.1f %.1f) d %.1f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], math.hypot(l['x'] - tx, l['z'] - tz)), flush=True)
    if stall > 25: print('stalled at cycle', c); break
p, l = player(e), laki()
print('end: M (%.1f %.1f %.1f) L (%.1f %.1f %.1f) d %.1f target (%.1f %.1f)' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], math.hypot(l['x'] - tx, l['z'] - tz), tx, tz))
e.step(0, 0, 0, 2); e.save(outp)
