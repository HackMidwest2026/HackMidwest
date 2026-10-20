"""kpa_62: which half-tilt ride holds into walls bring every hands-off miss spot (still riding Laki) to the same point?
For each sequence of 1-3 cardinal holds (90 frames each, half tilt), prints the distinct end points over all spots.
usage: kpa62_ride_converge.py SPOTS.json"""
import json, os, sys, itertools, collections
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HALF = {d: stick_for(a, 45) for d, a in (('right', 0), ('down', 90), ('left', 180), ('up', 270))}
spots = [s for s in json.load(open(sys.argv[1])) if s['riding']]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/krc%d' % os.getpid())
seqs = [(a,) for a in HALF] + [(a, b) for a in HALF for b in HALF if a != b] + [(a, b, c) for a in HALF for b in HALF for c in HALF if a != b and b != c]
res = []
for seq in seqs:
    ends = collections.Counter(); ok = True
    for s in spots:
        e.load(s['state']); e.step(0, 0, 0, 2)
        for d in seq:
            for i in range(90): e.step(0, *HALF[d], 2)
            for i in range(10): e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] != 33 or p['y'] < 55: ok = False; break
        ends[(round(p['x'], 1), round(p['z'], 1))] += 1
    if ok:
        res.append((len(ends), seq, ends.most_common(3)))
res.sort(key=lambda r: r[0])
for r in res[:15]: print(r, flush=True)
