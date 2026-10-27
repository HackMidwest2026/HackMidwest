"""pra_18 south->north: lowest Lakilester speed that clips from each standing spot, with Mario FACING LEFT vs FACING
RIGHT. DIAGNOSTIC (map only): Mario placed at (x, z), a 1-frame stick tap sets his facing, he is placed again at (x, z);
C-down with Laki's speed forced to S each frame until the mount. Binary search for the lowest S (checked clipping at
S = 100 first; every higher speed up to 100 clipped in the earlier maps). usage: pra18_sn_facing_map.py PART NPARTS OUT.json"""
import os, sys, json
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fm%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/fm%d_b.st' % os.getpid(); e.save(b0)
spot_st = '/dev/shm/pmbot/fm%d_s.st' % os.getpid()
def place(x, z, face):
    e.load(b0)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    for i in range(10): e.step(0, 0, 0, 2)
    e.step(0, face, 0, 2)
    for i in range(6): e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 8, z)
    for i in range(10): e.step(0, 0, 0, 2)
    p = player(e)
    if abs(p['x'] - x) > 0.3 or abs(p['z'] - z) > 0.3: return None
    e.save(spot_st); return p
def clips(S):
    e.load(spot_st); e.step(D_CBUTTON, 0, 0, 2)
    for i in range(30):
        if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))
        e.step(0, 0, 0, 2)
    q = player(e); return q['action'] == 33 and q['z'] < 0
spots = [(606 + 0.5 * i, float(z)) for i in range(29) for z in range(14, 47, 2)][part::nparts]
res = []
for x, z in spots:
    for face, name in ((-60, 'left'), (60, 'right')):
        p = place(x, z, face)
        if p is None: res.append([x, z, name, 'unstandable']); continue
        if not clips(100): res.append([x, z, name, None]); continue
        lo, hi = 6.0, 100.0
        if clips(lo): hi = lo
        while hi - lo > 0.25:
            mid = (lo + hi) / 2
            if clips(mid): hi = mid
            else: lo = mid
        res.append([x, z, name, round(hi, 2)])
    if len(res) % 40 < 2: print(x, z, res[-2:], flush=True)
json.dump(res, open(out, 'w')); print('done')
