"""pra_18 statue 1: neutral-stick tornado jump from a grid of standing positions around the club.
DIAGNOSTIC (map only): Mario placed on foot at (x, z) in RAM, settles, then A held 6 (full jump), second A d2 frames
after the first press (Ultra Boots tornado), stick neutral throughout. Success = Mario ends standing on the club
(y >= 70) or the statue top (y >= 99). usage: pra18_statue1_grid.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s1g_%d' % os.getpid())
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/s1g_%d_b.st' % os.getpid(); e.save(b0)
pos = [(x, z) for x in range(200, 241) for z in range(-112, -39)][part::nparts]
fo = open(out, 'a')
for x, z in pos:
    e.load(b0); e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 8, float(z))      # DIAGNOSTIC
    for i in range(8): e.step(0, 0, 0, 2)
    p0 = player(e)
    if abs(p0['x'] - x) > 0.6 or abs(p0['z'] - z) > 0.6 or p0['y'] > 1: continue            # not a valid standing spot
    s = '/dev/shm/pmbot/s1g_%d_s.st' % os.getpid(); e.save(s)
    best = 0; ok = []
    for d2 in range(6, 18):
        e.load(s)
        for i in range(d2):
            e.step(A if i < 6 else 0, 0, 0, 2)
        e.step(A, 0, 0, 2); my = 0
        for i in range(45): e.step(0, 0, 0, 2); my = max(my, player(e)['y'])
        q = player(e); best = max(best, my)
        if q['y'] >= 70 and q['action'] in (0, 1, 2): ok.append((d2, round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)))
    rec = {'x': x, 'z': z, 'peak': round(best, 1), 'ok': ok}
    fo.write(json.dumps(rec) + '\n'); fo.flush()
    if ok: print('UP', rec, flush=True)
print('done')
