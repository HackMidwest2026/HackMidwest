"""kpa_62: setups where the dismount spot comes from riding Laki into walls. Mount at a placed spot (facing set by an
optional 1-frame LEFT/RIGHT tap first), ride holding cardinal P1 for n1 frames then P2 for n2 frames (walls pin Laki),
release 10, B, hold cardinal D, C-down on frame T (28..45). Records every clip.
usage: kpa62_ridepin.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/krp%d' % os.getpid())
tmp = '/dev/shm/pmbot/krp%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
STARTS = [(-480, -80), (-450, -60), (-460, -110)]
N1 = [20, 40, 80, 150]; N2 = [0, 10, 20, 40, 80, 150]
jobs = [(s, f, P1, P2) for s in STARTS for f in (None, 'left', 'right') for P1 in CARD for P2 in CARD if P2 != P1][PART::NP]
fo = open(out, 'a'); seen = set(); hits = 0; tested = 0
def clipwin():
    e.save(tmp + '.r'); res = {}
    for D in CARD:
        e.load(tmp + '.r'); e.step(0x40, 0, 0, 2); win = []
        for fr in range(1, 46):
            if fr >= 28:
                e.save(tmp + '.h'); e.step(0x400, *CARD[D], 2); ok = False
                for f in range(30):
                    e.step(0, *CARD[D], 2); q = player(e)
                    if f > 18 and inside_tower(q['x'], q['z']): ok = True; break
                if ok: win.append(fr)
                e.load(tmp + '.h')
            e.step(0, *CARD[D], 2)
        if win: res[D] = win
    return res
for (s, face, P1, P2) in jobs:
    e.load(tmp + '.st0'); place(e, float(s[0]), float(s[1]))
    if face:
        e.step(0, *CARD[face], 2)
        for i in range(30): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(30): e.step(0, 0, 0, 2)
    e.save(tmp + '.m'); done1 = 0
    for n1 in N1:
        e.load(tmp + '.m')
        for i in range(n1): e.step(0, *CARD[P1], 2)
        e.save(tmp + '.1')
        for n2 in N2:
            e.load(tmp + '.1')
            for i in range(n2): e.step(0, *CARD[P2], 2)
            for i in range(10): e.step(0, 0, 0, 2)
            p = player(e)
            if abs(p['y'] - 71) > 3: continue
            key = (round(p['x'], 2), round(p['z'], 2), face)
            if key in seen: continue
            seen.add(key); tested += 1
            res = clipwin()
            if res:
                hits += 1
                rec = {'start': s, 'face': face, 'P1': P1, 'n1': n1, 'P2': P2, 'n2': n2, 'ride': [p['x'], p['z']], 'res': res}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print(rec, flush=True)
print('done part', PART, len(jobs), 'jobs', tested, 'ride spots', hits, 'hits')
