"""kpa_62 cardinal-only RTA search. Fixed points: from each START, hold one cardinal (right/down/left/up) for 60 frames
and keep spots that don't move between 60 and 90 frames (corners). From each fixed point, try every 1- and 2-move
program, each move one of: walk DIR k frames (k 1..12), spin (Z) holding DIR for k frames (k 1, 6, 12, 20), jump (A)
holding DIR for k frames (k 0..14). Each move is followed by 20 neutral frames. Spots on the line (x -440.80..-440.58,
z -60..-40, y 60) are then checked with the full clip (settle, mount, ride, B, hold down, C-down on frame 34).
usage: kpa62_card_search.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
A, Z = 0x0080, 0x0020
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcs%d' % os.getpid())
tmp = '/dev/shm/pmbot/kcs%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
STARTS = [(-450, -80), (-440, -60), (-470, -100), (-460, -50), (-430, -120), (-480, -70)]
MOVES = [('walk', d, k) for d in CARD for k in range(1, 13)] + [('spin', d, k) for d in CARD for k in (1, 6, 12, 20)] + \
        [('jump', d, k) for d in CARD for k in range(0, 15)]
def do(m):
    kind, d, k = m
    if kind == 'walk':
        for i in range(k): e.step(0, *CARD[d], 2)
    elif kind == 'spin':
        e.step(Z, *CARD[d], 2)
        for i in range(k - 1): e.step(0, *CARD[d], 2)
    else:
        e.step(A, *CARD[d], 2)
        for i in range(k): e.step(A, *CARD[d], 2)
        for i in range(30 - k): e.step(0, 0, 0, 2)
    for i in range(20): e.step(0, 0, 0, 2)
def on_line(p): return -440.80 <= p['x'] <= -440.58 and -60 <= p['z'] <= -40 and abs(p['y'] - 60) < .5
def clip():
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = CARD['down']
    for fr in range(1, 34): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2)
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): return True
    return False
# fixed points
fixed = {}
for (sx, sz) in STARTS:
    for d in CARD:
        e.load(tmp + '.st0'); place(e, float(sx), float(sz))
        for i in range(60): e.step(0, *CARD[d], 2)
        a = player(e)
        for i in range(30): e.step(0, *CARD[d], 2)
        b = player(e)
        if abs(a['x'] - b['x']) < .01 and abs(a['z'] - b['z']) < .01 and abs(b['y'] - 60) < .5:
            for i in range(10): e.step(0, 0, 0, 2)
            key = (round(b['x'], 2), round(b['z'], 2))
            if key not in fixed:
                fixed[key] = ((sx, sz), d); e.save(tmp + '.fx%d' % len(fixed))
fps = list(fixed.items())
if PART == 0: print('fixed points', [(k, v) for k, v in fps], flush=True)
fo = open(out, 'a'); hits = 0
jobs = [(i, m1) for i in range(len(fps)) for m1 in MOVES][PART::NP]
for (i, m1) in jobs:
    e.load(tmp + '.fx%d' % (i + 1)); do(m1); e.save(tmp + '.m1'); p1 = player(e)
    progs = [((m1,), p1)] if on_line(p1) else []
    for m2 in [None] + MOVES:
        if m2 is None: continue
        e.load(tmp + '.m1'); do(m2); p2 = player(e)
        if on_line(p2): progs.append(((m1, m2), p2)); e.save(tmp + '.c%d' % len(progs))
    for j, (prog, p) in enumerate(progs):
        if len(prog) == 1: e.load(tmp + '.m1')
        else: e.load(tmp + '.c%d' % (j + 1))
        ok = clip()
        rec = {'fixed': fps[i][0], 'from': fps[i][1], 'prog': prog, 'stand': [p['x'], p['z']], 'clip': ok}
        fo.write(json.dumps(rec) + '\n'); fo.flush()
        if ok: hits += 1; print(rec, flush=True)
print('done part', PART, len(jobs), 'first moves', hits, 'clips')
