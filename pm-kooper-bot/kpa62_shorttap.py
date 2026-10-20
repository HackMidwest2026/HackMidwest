"""kpa_62: wall-pinned spot + one or two short cardinal taps (1-4 frames each) onto the line. Pinned spots: from a grid
of placements, optional 1-frame facing tap, then hold cardinal P for n frames (10..200), optionally followed by holding
a second cardinal P2 for 60 frames (corners). Taps are predicted at 3.215 units/axis/frame and simulated only when they
land within 0.3 of the line; on-line spots get the clip check (down after B, C-down frame 34).
usage: kpa62_shorttap.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
VEC = {'right': (1, -1), 'down': (1, 1), 'left': (-1, 1), 'up': (-1, -1)}
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kst%d' % os.getpid())
tmp = '/dev/shm/pmbot/kst%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
STARTS = [(-500, -60), (-480, -100), (-460, -60), (-450, -100), (-440, -80), (-460, -30), (-430, -40), (-470, -120), (-490, -30)]
TAPS = [((d, k),) for d in CARD for k in range(1, 5)] + [((d1, k1), (d2, k2)) for d1 in CARD for d2 in CARD if d2 != d1 for k1 in range(1, 5) for k2 in range(1, 5)]
def on_line(p): return -440.80 <= p['x'] <= -440.58 and -60 <= p['z'] <= -40 and abs(p['y'] - 60) < .5
def clip():
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2)
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
jobs = [(s, f, P, P2) for s in STARTS for f in (None, 'left', 'right') for P in CARD for P2 in [None] + list(CARD) if P2 != P][PART::NP]
fo = open(out, 'a'); seen = set(); hits = 0; tested = 0
for (s, face, P, P2) in jobs:
    e.load(tmp + '.st0'); place(e, float(s[0]), float(s[1]))
    if face:
        e.step(0, *CARD[face], 2)
        for i in range(10): e.step(0, 0, 0, 2)
    for n in range(1, 201):
        e.step(0, *CARD[P], 2)
        if n < 10 or n % 5: continue
        if abs(player(e)['y'] - 60) > .5: break
        e.save(tmp + '.n')
        if P2:
            for i in range(60): e.step(0, *CARD[P2], 2)
        for i in range(20): e.step(0, 0, 0, 2)
        p = player(e)
        key = (round(p['x'], 2), round(p['z'], 2), face, P, P2)
        if abs(p['y'] - 60) > .5 or key in seen: e.load(tmp + '.n'); continue
        seen.add(key); e.save(tmp + '.p')
        for taps in TAPS:
            x = p['x'] + sum(VEC[d][0] * k for d, k in taps) * 3.215; z = p['z'] + sum(VEC[d][1] * k for d, k in taps) * 3.215
            if abs(x + 440.69) > 0.3 or not (-60 <= z <= -40): continue
            e.load(tmp + '.p')
            for d, k in taps:
                for i in range(k): e.step(0, *CARD[d], 2)
                for i in range(20): e.step(0, 0, 0, 2)
            q = player(e)
            if not on_line(q): continue
            tested += 1; ok = clip(); hits += ok
            rec = {'start': s, 'face': face, 'P': P, 'n': n, 'P2': P2, 'pin': [p['x'], p['z']], 'taps': taps, 'stand': [q['x'], q['z']], 'clip': ok}
            fo.write(json.dumps(rec) + '\n'); fo.flush()
            if ok: print(rec, flush=True)
        e.load(tmp + '.n')
print('done part', PART, len(jobs), 'jobs', len(seen), 'pinned spots', tested, 'on line', hits, 'clips')
