"""dgb_01: re-check mount-map targets against the real floor: a target is out of bounds if no enabled floor triangle
(normal y > 0.5) lies under it (x, z), whatever its height. Uses the collision dump of the matching state.
usage: dgb01_floorcheck.py COLLISION.json MAP.jsonl[.gz] ..."""
import gzip, json, sys
d = json.load(open(sys.argv[1]))
tris = []
for c in d['colliders']:
    if (c['flags'] & 0x7ffffe00) == 0x7ffffe00: continue
    for t in c['tris']:
        if t['n'][1] > 0.5: tris.append([(v[0], v[2]) for v in t['v']])
def inside_tri(p, t):
    (x1, z1), (x2, z2), (x3, z3) = t
    d1 = (p[0] - x2) * (z1 - z2) - (x1 - x2) * (p[1] - z2)
    d2 = (p[0] - x3) * (z2 - z3) - (x2 - x3) * (p[1] - z3)
    d3 = (p[0] - x1) * (z3 - z1) - (x3 - x1) * (p[1] - z1)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
def has_floor(x, z): return any(inside_tri((x, z), t) for t in tris)
n = out = 0; cells = {}
for f in sys.argv[2:]:
    for l in (gzip.open(f, 'rt') if f.endswith('.gz') else open(f)):
        r = json.loads(l)
        for q in r['r']:
            n += 1
            if not has_floor(q[1], q[3]):
                out += 1; cells.setdefault((r['x'], r['z']), []).append(q[0])
print(n, 'targets checked,', out, 'with no floor under them, at', len(cells), 'spots')
for k, v in sorted(cells.items())[:30]: print('  spot', k, 'speeds', sorted(v)[:12])
