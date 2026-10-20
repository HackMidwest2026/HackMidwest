"""Laki partner-swap upwarp at every reachable spot of dgb_01 2F east (walkway + debris slab, plus the two corners).
At each spot: mount Laki in place, ride DIR (half or full tilt) for k game frames, then C-DOWN + C-RIGHT on the same
frame (dismount hop + partner menu), pick Bombette (UP, A) -> Laki's PutAway hop, whose landing rays can set Mario's
y to any floor up to 37 above his head ("upwarp"). Afterwards hold POST. POST variants are only run when an upwarp
happened. Tubba parked (search only). Records peak y, every upwarp (y jump > 6 in one game frame) and the end.
usage: dgb01_upwarp_scan.py PART NPARTS OUT.jsonl"""
import json, sys
from emu import *
from pm import *

part, nparts, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/upw%d' % part)
e.load('states/dgb01_e4_ctrl.st')
e.w8(PLAYER_DATA, 2)
for p in (1, 2, 3, 8): e.w8(PLAYER_DATA + 0x14 + 8 * p, 1)
tubba = [n for n in npcs(e) if n['id'] == 4][0]['addr']
def step(b, x, y, n=1):
    for i in range(n):
        e.wf32(tubba + 0x38, 0.0); e.wf32(tubba + 0x3C, -1000.0); e.wf32(tubba + 0x40, 0.0)
        e.step(b, x, y, 1)
step(0, 0, 0, 2)
base = '/dev/shm/pmbot/upw_base%d.st' % part
e.save(base)
S = {'n': (0, 0), 'u': (0, 1), 'd': (0, -1), 'l': (-1, 0), 'r': (1, 0),
     'ul': (-.7, .7), 'ur': (.7, .7), 'dl': (-.7, -.7), 'dr': (.7, -.7)}
def stick(d, mag): return (round(S[d][0] * mag), round(S[d][1] * mag))
spots = json.load(open('dgb01_upwarp_spots.json'))[part::nparts]
f = open(outp, 'a')
for sx, sy, sz in spots:
    e.load(base); step(0, 0, 0)
    e.wf32(PLAYER + PS_POS, sx); e.wf32(PLAYER + PS_POS + 4, sy + 3); e.wf32(PLAYER + PS_POS + 8, sz)
    step(0, 0, 0, 30)
    step(D_CBUTTON, 0, 0, 2); step(0, 0, 0, 70)
    if player(e)['action'] != 33:
        print('no mount at', sx, sy, sz, player(e)); continue
    e.step(0, 0, 0, 1); riding = '/dev/shm/pmbot/upw_ride%d.st' % part; e.save(riding)
    combos = [('n', 0, 0)] + [(d, mag, k) for d in S if d != 'n' for mag in (40, 80) for k in (4, 10, 20)]
    for d, mag, k in combos:
        for post in ('n', 'u', 'd', 'l', 'r'):
            e.load(riding)
            sxy = stick(d, mag)
            step(0, *sxy, 2 * k)
            p0 = player(e)
            step(D_CBUTTON | R_CBUTTON, *sxy, 2)
            step(0, 0, 0, 24); step(0, 0, 80, 2); step(0, 0, 0, 6); step(A, 0, 0, 2)
            pxy = stick(post, 80)
            maxy, low, prev, warps = -1e9, 1e9, None, []
            for i in range(180):
                step(0, *pxy)
                if i % 2: continue
                q = player(e)
                if prev is not None and q['y'] - prev > 6: warps.append((round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)))
                prev = q['y']; maxy = max(maxy, q['y']); low = min(low, q['y'])
            q = player(e)
            r = {'spot': (sx, sy, sz), 'ride': d, 'mag': mag, 'k': k, 'post': post, 'from': (round(p0['x'], 1), round(p0['y'], 1), round(p0['z'], 1)),
                 'maxy': round(maxy, 1), 'low': round(low, 1), 'warps': warps,
                 'end': (round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)), 'partner': e.s8(PLAYER_DATA + 0x12)}
            f.write(json.dumps(r) + '\n')
            if low < 200 or q['y'] > 260: print('HIT', r, flush=True)
            if not warps: break          # POST only matters after an upwarp
    f.flush()
print('done part', part)
