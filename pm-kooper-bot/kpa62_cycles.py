"""kpa_62: wall pin + mount/dismount cycles (each cycle: C-down, ride 25, B, wait 30 moves Mario by about (-2.73, -2.73))
so the only exact input left is the C-down on frame 34. Pinned spots: from a grid of placements (and the y-35 ledge
after a jump up), optional 1-frame facing tap, hold cardinal P for n frames (10..200 step 5). After each of up to 25
cycles, if Mario stands on the line, run the clip (mount, ride 40, B, hold down, C-down on frame 34).
usage: kpa62_cycles.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcy%d' % os.getpid())
tmp = '/dev/shm/pmbot/kcy%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
STARTS = [(-500, -60), (-480, -100), (-460, -60), (-450, -100), (-440, -80), (-460, -30), (-430, -40), (-470, -120), (-490, -30), (-420, -60)]
def on_line(p): return -440.80 <= p['x'] <= -440.58 and -60 <= p['z'] <= -40 and abs(p['y'] - 60) < .5
def clip():
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2)
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
jobs = [(s, f, P) for s in STARTS for f in (None, 'left', 'right') for P in CARD][PART::NP]
fo = open(out, 'a'); seen = set(); hits = 0; tested = 0
for (s, face, P) in jobs:
    e.load(tmp + '.st0'); place(e, float(s[0]), float(s[1]))
    if face:
        e.step(0, *CARD[face], 2)
        for i in range(10): e.step(0, 0, 0, 2)
    prev = None
    for n in range(1, 201):
        e.step(0, *CARD[P], 2)
        if n < 10 or n % 5: continue
        p = player(e)
        if abs(p['y'] - 60) > .5: break
        moving = prev is not None and abs(p['x'] - prev[0]) > 10 and abs(p['z'] - prev[1]) > 10
        prev = (p['x'], p['z'])
        if moving: continue
        key = (round(p['x'], 1), round(p['z'], 1), face)
        if key in seen: continue
        seen.add(key); e.save(tmp + '.n')
        for i in range(30): e.step(0, 0, 0, 2)
        pin = player(e)
        for c in range(1, 26):
            e.step(0x400, 0, 0, 2)
            for i in range(25): e.step(0, 0, 0, 2)
            e.step(0x40, 0, 0, 2)
            for i in range(30): e.step(0, 0, 0, 2)
            q = player(e)
            if abs(q['y'] - 60) > .5: break
            if on_line(q):
                e.save(tmp + '.c'); tested += 1
                ok = clip(); hits += ok
                rec = {'start': s, 'face': face, 'P': P, 'n': n, 'pin': [pin['x'], pin['z']], 'cycles': c, 'stand': [q['x'], q['z']], 'clip': ok}
                fo.write(json.dumps(rec) + '\n'); fo.flush()
                if ok: print(rec, flush=True)
                e.load(tmp + '.c')
        e.load(tmp + '.n')
print('done part', PART, len(jobs), 'jobs', len(seen), 'spots', tested, 'on line', hits, 'clips')
