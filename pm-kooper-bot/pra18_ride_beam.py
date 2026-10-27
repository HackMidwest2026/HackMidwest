"""pra_18: beam search while RIDING Lakilester, starting from the -12.707 spot (pra18_from127.py setup), every frame trying
16 stick directions x 2 magnitudes + neutral, and C-down (dismount) with each held direction as a terminal move.
Keeps K best states by Mario z (memory-light: only kept states are saved). Goal dist2D to (717,70) < 80.
usage: pra18_ride_beam.py OUT.json"""
import os, sys, math, json
from emu import *
from pm import *
K, DEPTH = int(os.environ.get('K', '6')), int(os.environ.get('DEPTH', '80'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rb')
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dist = lambda p: math.hypot(p['x'] - 717, p['z'] - 70)
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 723.0); e.wf32(PLAYER + PS_POS + 8, -30.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 703.0); e.wf32(L['addr'] + 0x40, -30.0)           # DIAGNOSTIC
for i in range(40): e.step(0, 0, 0, 2)
pre = [(D_CBUTTON, 0, 0)] + [(0, 0, 0)] * 40 + [(0,) + st(110, 80)] * 25
for b, x, y in pre[1:]: pass
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
for i in range(25): e.step(0, *st(110, 80), 2)
for f in range(14):
    phase = (f // 7) % 2; s = st(6 if phase == 0 else 174, 80) if f % 7 < 6 else (0, 0)
    e.step(0, *s, 2); pre.append((0,) + s)
p = player(e); print('start', p['x'], p['z'], flush=True)
root = '/dev/shm/pmbot/rb_root.st'; e.save(root)
CAND = [(0,) + st(a, m) for a in range(0, 360, 22) for m in (20, 80)] + [(0, 0, 0)]
TERM = [(D_CBUTTON,) + st(a, 80) for a in range(0, 360, 45)] + [(D_CBUTTON, 0, 0)]
beam = [(p['z'], root, [])]; best = (p['z'], p['x'], dist(p), []); gen = 0
for depth in range(DEPTH):
    scored = []
    for z0, path, seq in beam:
        for c in CAND + TERM:
            e.load(path); e.step(*c[:1], c[1], c[2], 2); p = player(e); mz = p['z']; extra = []
            if c[0] == D_CBUTTON:
                for i in range(30):
                    e.step(0, c[1], c[2], 2); q = player(e)
                    if q['z'] < 0 and q['z'] > mz: mz = q['z']; p = q; extra = [(0, c[1], c[2])] * (i + 1)
            if mz >= 0: continue
            d = dist(p)
            if mz > best[0]: best = (mz, p['x'], d, seq + [c] + extra); print('  new best z %.4f x %.2f dist %.3f depth %d' % (mz, p['x'], d, depth), flush=True)
            if d < 80 and p['z'] < 0:
                print('HIT', depth, p['x'], p['z'], d, flush=True)
                json.dump({'hit': True, 'pre': pre, 'seq': seq + [c] + extra, 'x': p['x'], 'z': p['z'], 'dist': d}, open(sys.argv[1], 'w')); sys.exit(0)
            if c[0] == 0: scored.append((mz - 0.01 * abs(p['x'] - 720), path, seq, c, round(mz, 4), round(p['x'], 2)))
    scored.sort(key=lambda r: -r[0]); seen = set(); nb = []
    for r in scored:
        if (r[4], r[5]) in seen: continue
        seen.add((r[4], r[5]))
        e.load(r[1]); e.step(*r[3][:1], r[3][1], r[3][2], 2)
        fn = '/dev/shm/pmbot/rb_g%d_%d.st' % (gen, len(nb)); e.save(fn); nb.append((r[0], fn, r[2] + [r[3]]))
        if len(nb) >= K: break
    for _, path, _ in beam:
        if path != root and os.path.exists(path): os.remove(path)
    beam = nb; gen += 1
    if depth % 5 == 0: print('depth', depth, 'best z %.4f dist %.3f' % (best[0], best[2]), 'beam', [round(b[0], 3) for b in beam], flush=True)
json.dump({'hit': False, 'pre': pre, 'best_z': best[0], 'x': best[1], 'dist': best[2], 'seq': best[3]}, open(sys.argv[1], 'w'))
print('final best z %.4f x %.2f dist %.3f' % best[:3])
