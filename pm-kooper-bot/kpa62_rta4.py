"""kpa_62 remount clip: timing search relative to the dismount. Laki's post-dismount return (follow state 15) lasts 16
frames; on the first frame after it his speed is 0.25 * distance to Mario, and that speed is what the remount uses. So the
C-down must come a fixed number of frames after the dismount. This searches, from many dismount spots on the y-60
platform, programs: after the dismount B (frame 0), wait until frame F0, press X (none / Z spin / A jump) while pushing
notch direction D, hold D until frame REL (or keep holding), and press C-down on frame T (T = 26..42).
Reports programs where several T work (the RTA window).
usage: kpa62_rta4.py STATE PART NPARTS OUT.jsonl   env: F0S, RELS"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
A, B, Z = 0x0080, 0x0040, 0x0020
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
ev = lambda k, d: [int(v) for v in os.environ.get(k, d).split(',')]
F0S, RELS = ev('F0S', '1,8,14'), ev('RELS', '99,18,21,24,27,30')
TS = range(26, 43)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62d%d' % os.getpid())
tmp = '/dev/shm/pmbot/k62d%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, -460.0); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, -60.0)
for i in range(20): e.step(0, 0, 0, 2)
e.save(tmp + '.seed')
walks = [tuple(int(v) for v in t.split(':')) for t in os.environ['WALKS'].split(';')] if os.environ.get('WALKS') else [(a, k) for a in range(0, 360, 30) for k in (0, 8, 16, 24)]
def near(p): return abs(p['y'] - 50) < 3 and -390 <= p['x'] <= -370 and -10 <= p['z'] <= 30
def try_cdown(st):
    e.step(0x400, *st, 2)
    for f in range(30):
        e.step(0, *st, 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
fo = open(out, 'a'); seen = set(); good = 0
for (wa, wk) in walks[PART::NP]:
    e.load(tmp + '.seed')
    for i in range(wk): e.step(0, *stick_for(wa, 80), 2)
    for i in range(6): e.step(0, 0, 0, 2)
    s = player(e); key = (round(s['x'] / 4), round(s['z'] / 4))
    if abs(s['y'] - 60) > 2 or key in seen: continue
    seen.add(key)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(B, 0, 0, 2)                                      # dismount = frame 0
    d = player(e); e.save(tmp + '.dis')
    for X in ev('XS', '0,%d,%d' % (Z, A)):
        for D in ev('DS', '0,45,90,135,180,225,270,315'):
            for F0 in F0S:
                for REL in RELS:
                    e.load(tmp + '.dis'); st = stick_for(D, 80); win = []
                    for fr in range(1, max(TS) + 1):
                        cur = (0, 0) if fr < F0 or fr >= REL else st
                        if fr in TS and near(player(e)):
                            e.save(tmp + '.h')
                            if try_cdown(cur): win.append(fr)
                            e.load(tmp + '.h')
                        e.step(X if fr == F0 else 0, *cur, 2)
                    if win:
                        good += 1
                        rec = {'walk': [wa, wk], 'start': [s['x'], s['z']], 'dis': [d['x'], d['z']], 'X': X, 'D': D, 'F0': F0, 'REL': REL, 'T': win}
                        fo.write(json.dumps(rec) + '\n'); fo.flush()
                        if len(win) > 1: print(rec, flush=True)
print('done part', PART, len(seen), 'starts', good, 'programs with hits')
