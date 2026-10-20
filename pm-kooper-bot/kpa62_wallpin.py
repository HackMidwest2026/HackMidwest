"""kpa_62: setups where Mario's mount spot comes only from holds into walls (no exact walk counts). Start spots: from a
grid of placements on the y-60 platform, optionally set facing with a 1-frame LEFT or RIGHT tap, then hold cardinal P
for n frames (n = 10..160): Mario ends pinned against walls or creeping along them. For each distinct spot: settle,
mount, ride 40, B, hold cardinal D after the B, C-down on frame T (28..45). Records every (spot, D, T) that clips.
usage: kpa62_wallpin.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kwp%d' % os.getpid())
tmp = '/dev/shm/pmbot/kwp%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
STARTS = [(-500, -60), (-480, -100), (-460, -60), (-450, -100), (-440, -80), (-460, -30), (-430, -40), (-470, -120)]
jobs = [(s, f, P) for s in STARTS for f in (None, 'left', 'right') for P in CARD][PART::NP]
fo = open(out, 'a'); seen = set(); hits = 0; tested = 0
for (s, face, P) in jobs:
    e.load(tmp + '.st0'); place(e, float(s[0]), float(s[1]))
    if face:
        e.step(0, *CARD[face], 2)
        for i in range(10): e.step(0, 0, 0, 2)
    prev = None
    for n in range(1, 161):
        e.step(0, *CARD[P], 2)
        if n < 10 or n % 3: continue
        p = player(e)
        if abs(p['y'] - 60) > .5: break
        key = (round(p['x'], 2), round(p['z'], 2), face, P)
        if prev and abs(p['x'] - prev[0]) > 2.5 and abs(p['z'] - prev[1]) > 2.5: prev = (p['x'], p['z']); continue   # free running, not on a wall
        prev = (p['x'], p['z'])
        if key in seen: continue
        seen.add(key); e.save(tmp + '.n')
        for i in range(40): e.step(0, 0, 0, 2)
        sp = player(e)
        e.step(0x400, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
        e.step(0x40, 0, 0, 2); e.save(tmp + '.b')
        for D in CARD:
            e.load(tmp + '.b'); win = []
            for fr in range(1, 46):
                if fr >= 28:
                    e.save(tmp + '.h'); e.step(0x400, *CARD[D], 2); ok = False
                    for f in range(30):
                        e.step(0, *CARD[D], 2); q = player(e)
                        if f > 18 and inside_tower(q['x'], q['z']): ok = True; break
                    if ok: win.append(fr)
                    e.load(tmp + '.h')
                e.step(0, *CARD[D], 2)
            tested += 1
            if win:
                hits += 1
                rec = {'start': s, 'face': face, 'P': P, 'n': n, 'spot': [sp['x'], sp['z']], 'D': D, 'T': win}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print(rec, flush=True)
        e.load(tmp + '.n')
print('done part', PART, len(jobs), 'jobs', tested, 'tests', hits, 'hits')
