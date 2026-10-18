"""Out-of-bounds fall search for a Lakilester freeze: teleport Mario to a random point of the room with no floor below
(he falls until the timeInAir > 100 respawn at lastGoodPos), steer in the air for a random time, then random-walk
(laki_stuck_search_policy) after the respawn. Flags runs where, for 90 frames after the respawn, Mario travels > 100
while Laki either stays within 3 units or stays > 150 away (3D). Writes jsonl lines with everything needed to replay.
usage: laki_oob_search.py STATE COLLISION.json SEED0 NRUNS OUT.jsonl [F=600]
env STUCKHOP=1: instead flag Laki stuck in the hop (state 2, jumpScale 0, jumpVel 0) for 30 frames.
env REPLAY=1: print every frame (EVERY=k) of each seed instead of searching; SAVE_AT=f SAVE=path saves a state."""
import json, math, os, random, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from laki_stuck_search_policy import policy
IDX, PTR, STATE = 0x8010D178, 0x8010D17C, 0x8010D188
st0, coll, s0, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
F = int(sys.argv[6]) if len(sys.argv) > 6 else 600
C = json.load(open(coll)); C = C['colliders'] if isinstance(C, dict) else C
floors = [t for c in C for t in c['tris'] if t['n'][1] > 0.5]
def has_floor(x, z):
    for t in floors:
        (ax, _, az), (bx, _, bz), (cx, _, cz) = t['v']
        d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(d) < 1e-9: continue
        u = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d; v = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d
        if u >= 0 and v >= 0 and u + v <= 1: return True
    return False
xs = [v[0] for t in floors for v in t['v']]; zs = [v[2] for t in floors for v in t['v']]
X0, X1, Z0, Z1 = min(xs) - 60, max(xs) + 60, min(zs) - 60, max(zs) + 60
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/los%d' % os.getpid())
fo = open(out, 'a')
def setup(rng):
    while True:
        x, z = rng.uniform(X0, X1), rng.uniform(Z0, Z1)
        if not has_floor(x, z): break
    return x, rng.uniform(0, 60), z, rng.uniform(0, 360), rng.randint(0, 60), rng.choice((0, 0, 30, 60, 90))
for seed in range(s0, s0 + n):
    rng = random.Random(seed); x, y, z, d, air, pre = setup(rng); seq = policy(rng, F)
    e.load(st0); e.step(0, 0, 0, 2)
    for i in range(pre): e.step(0, 0, 0, 2)  # let Laki settle / go idle first
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
    M, L, resp = [], [], None; hop_run = 0
    for f in range(130 + F):
        if f < 130: b, sx, sy = (0,) + (stick_for(d, 80) if f < air else (0, 0))
        else: b, sx, sy = seq[f - 130]
        e.step(b, sx, sy, 2)
        p = player(e); ls = [q for q in npcs(e) if q['id'] == -4]
        if not ls: break
        l = ls[0]; M.append((p['x'], p['y'], p['z'])); L.append((l['x'], l['y'], l['z']))
        if os.environ.get('STUCKHOP'):
            a = l['addr']; sh = (e.u32(STATE) >> 16) == 2 and e.f32(a + 0x14) == 0 and e.f32(a + 0x1C) == 0
            hop_run = hop_run + 1 if sh else 0
            if hop_run == 30:
                fo.write(json.dumps({'state': st0, 'seed': seed, 'F': F, 'frame': f, 'kind': 'stuckhop', 'mario': M[-1], 'laki': L[-1],
                                     'speed': l['speed'], 'yaw': e.f32(a + 0xC), 'oob': [x, y, z], 'air_dir': d, 'air': air, 'pre': pre}) + '\n'); fo.flush()
                break
            continue
        if os.environ.get('SAVE_AT') and f == int(os.environ['SAVE_AT']): e.save(os.environ['SAVE'])
        if os.environ.get('REPLAY'):
            if f % int(os.environ.get('EVERY', '1')) == 0:
                pt = e.u32(PTR)
                print('%4d b%02x M (%7.1f %7.1f %7.1f) act %2d | L (%7.1f %7.1f %7.1f) st %2d ptr %2d idx %2d tgt (%7.1f %7.1f %7.1f) spd %6.2f fl %08x d3 %.0f' % (
                    f, b, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, pt, e.u32(IDX),
                    e.f32(0x8010CEF8 + 16 * pt + 4), e.f32(0x8010CEF8 + 16 * pt + 8), e.f32(0x8010CEF8 + 16 * pt + 12), l['speed'], l['flags'], math.dist(M[-1], L[-1])))
            continue
        if resp is None and f > 0 and M[-2][1] < M[-1][1] - 100: resp = f
        if resp is not None and f >= resp + 90 and f >= 130 + 90:
            path = sum(math.dist(M[i], M[i - 1]) for i in range(f - 89, f + 1))
            still = max(math.dist(L[f], L[i]) for i in range(f - 90, f)) < 3
            far = min(math.dist(M[i], L[i]) for i in range(f - 90, f + 1)) > 150
            if path > 100 and (still or far) and math.dist(M[f], L[f]) > 60:
                fo.write(json.dumps({'state': st0, 'seed': seed, 'F': F, 'frame': f, 'resp': resp, 'kind': 'still' if still else 'far',
                                     'st': e.u32(STATE) >> 16, 'ptr': e.u32(PTR), 'idx': e.u32(IDX), 'mario': M[f], 'laki': L[f],
                                     'oob': [x, y, z], 'air_dir': d, 'air': air, 'pre': pre}) + '\n'); fo.flush()
                break
print('done', s0, n)
