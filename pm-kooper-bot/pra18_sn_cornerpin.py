"""pra_18 south->north: Mario held into the pillar-SE-face / mirror corner by a held stick vector V sits deeper than his
normal push-out (e.g. (619.7, 13.75) for V=(-24,68) vs 625 standing). From each such stick-held rest spot, does a
C-down mount clip north, and for which Lakilester speeds? DIAGNOSTIC (map only): Mario placed at a start south of
the corner, V held 60 frames (real input), then C-down with Laki's speed forced to S until the mount.
usage: pra18_sn_cornerpin.py PART NPARTS OUT.json"""
import os, sys, json, math
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cp%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/cp%d_b.st' % os.getpid(); e.save(b0)
held = '/dev/shm/pmbot/cp%d_h.st' % os.getpid()
vecs = [(sx, sy) for sx in range(-60, 31, 3) for sy in range(20, 81, 3) if 50 <= math.hypot(sx, sy) <= 82][part::nparts]
starts = [(640, 60), (625, 50)]
res = []
for V in vecs:
    for S0 in starts:
        e.load(b0)
        e.wf32(PLAYER + PS_POS, float(S0[0])); e.wf32(PLAYER + PS_POS + 8, float(S0[1]))     # DIAGNOSTIC
        for i in range(10): e.step(0, 0, 0, 2)
        for i in range(60): e.step(0, *V, 2)
        p = player(e)
        if not (608 <= p['x'] <= 626 and 12 <= p['z'] <= 30): continue
        e.save(held); ok = []
        for S in list(range(6, 60, 2)) + [70, 90]:
            e.load(held)
            e.step(D_CBUTTON, *V, 2)
            for i in range(30):
                if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))   # DIAGNOSTIC
                e.step(0, *V, 2)
            q = player(e)
            if q['action'] == 33 and q['z'] < 0: ok.append(S)
        r = [V, S0, round(p['x'], 2), round(p['z'], 2), ok]
        res.append(r)
        if ok: print('PIN', r, flush=True)
json.dump(res, open(out, 'w')); print('done')
