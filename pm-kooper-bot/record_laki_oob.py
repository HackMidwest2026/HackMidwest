"""Video frames of one laki_oob_search.py seed (same setup and inputs): OUT/f%04d.png (SHOT=1) + OUT/log.json.
usage: record_laki_oob.py STATE COLLISION.json SEED OUT [F=600]"""
import json, math, os, random, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from laki_stuck_search_policy import policy
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0, coll, seed, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
F = int(sys.argv[5]) if len(sys.argv) > 5 else 600
os.makedirs(OUT, exist_ok=True)
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
rng = random.Random(seed)
while True:
    x, z = rng.uniform(X0, X1), rng.uniform(Z0, Z1)
    if not has_floor(x, z): break
y, d, air, pre = rng.uniform(0, 60), rng.uniform(0, 360), rng.randint(0, 60), rng.choice((0, 0, 30, 60, 90))
seq = policy(rng, F)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rlo%d' % os.getpid())
log = []
def st(b, sx, sy, tag):
    e.step(b, sx, sy, 2)
    p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]; pt = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'], 'ls': l['speed'],
                'st': e.u32(STATE) >> 16, 'ptr': pt, 'idx': e.u32(IDX), 'tx': e.f32(HIST + 16 * pt + 4), 'ty': e.f32(HIST + 16 * pt + 8), 'tz': e.f32(HIST + 16 * pt + 12),
                'hist': [(e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12)) for k in range(40)]})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
e.load(st0); e.step(0, 0, 0, 2)
for i in range(pre): st(0, 0, 0, 'start (mac_01 left entrance): Laki follows normally')
e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
for f in range(130 + F):
    if f < 130:
        b, sx, sy = (0,) + (stick_for(d, 80) if f < air else (0, 0))
        tag = os.environ.get('FALL_TAG', 'Mario put out of bounds (RAM) at (%.0f, %.0f): falls; every frame adds a history entry') % (x, z)
    else:
        b, sx, sy = seq[f - 130]; tag = 'random walking after the respawn'
    st(b, sx, sy, tag)
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), 'frames; max Laki speed %.1f' % max(l['ls'] for l in log))
