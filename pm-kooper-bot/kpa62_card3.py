"""kpa_62 cardinal-only RTA search from the reliable 'up' corner (holding up from almost anywhere on the y-60 platform
ends at (-473.97, -125.65)). Explores every 1- and 2-move program (walk DIR 1..12 frames, spin DIR k, jump DIR k, or
hold DIR 60 frames into a wall), then predicts a third move from an open-ground displacement table and simulates only
third moves predicted to land within 1 unit of the line; spots on the line get the full clip check.
usage: kpa62_card3.py STATE PART NPARTS OUT.jsonl"""
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
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kc3%d' % os.getpid())
tmp = '/dev/shm/pmbot/kc3%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
MOVES = [('walk', d, k) for d in CARD for k in range(1, 13)] + [('spin', d, k) for d in CARD for k in (1, 6, 12, 20)] + \
        [('jump', d, k) for d in CARD for k in range(0, 15)] + [('hold', d, 60) for d in CARD]
def do(m):
    kind, d, k = m
    if kind in ('walk', 'hold'):
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
# displacement table on open ground (middle of the platform)
place(e, -455.0, -70.0); e.save(tmp + '.open'); o = player(e); DISP = {}
for m in MOVES:
    if m[0] == 'hold': continue
    e.load(tmp + '.open'); do(m); p = player(e); DISP[m] = (p['x'] - o['x'], p['z'] - o['z'])
# the corner
e.load(st0); e.step(0, 0, 0, 2); place(e, -480.0, -100.0)
for i in range(120): e.step(0, *CARD['up'], 2)
for i in range(10): e.step(0, 0, 0, 2)
c = player(e); e.save(tmp + '.c')
if PART == 0: print('corner (%.3f %.3f)' % (c['x'], c['z']), flush=True)
fo = open(out, 'a'); hits = 0; tested = 0
def check(prog, p):
    global hits, tested
    tested += 1
    ok = clip()
    rec = {'prog': prog, 'stand': [p['x'], p['z']], 'clip': ok}
    fo.write(json.dumps(rec) + '\n'); fo.flush()
    if ok: hits += 1; print(rec, flush=True)
for m1 in MOVES[PART::NP]:
    e.load(tmp + '.c'); do(m1); p1 = player(e)
    if abs(p1['y'] - 60) > .5: continue
    e.save(tmp + '.1')
    if on_line(p1): check([m1], p1); e.load(tmp + '.1')
    for m2 in MOVES:
        e.load(tmp + '.1'); do(m2); p2 = player(e)
        if abs(p2['y'] - 60) > .5: continue
        e.save(tmp + '.2')
        if on_line(p2): check([m1, m2], p2); e.load(tmp + '.2')
        for m3, (dx, dz) in DISP.items():
            if abs(p2['x'] + dx + 440.69) > 1.0 or not (-61 <= p2['z'] + dz <= -39): continue
            e.load(tmp + '.2'); do(m3); p3 = player(e)
            if on_line(p3): check([m1, m2, m3], p3)
print('done part', PART, tested, 'tested', hits, 'clips')
