"""Figure for dgb01_mount_map.py output: for each Mario spot, the smallest Laki speed whose mount target is out of bounds
(colour), grey = standable but no tested speed clips out; walls from the collision dump.
usage: dgb01_map_figure.py OUT.png MAP.jsonl [MAP2.jsonl ...]"""
import json, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
outp, files = sys.argv[1], sys.argv[2:]
cells = {}
for f in files:
    for l in open(f):
        r = json.loads(l); k = (r['x'], r['z'])
        oo = [q[0] for q in r['r'] if q[4]]
        prev = cells.get(k)
        cand = min(oo) if oo else None
        if prev is None or (cand is not None and (prev is None or prev == -1 or cand < prev)): cells[k] = cand if cand is not None else (prev if prev is not None else -1)
d = json.load(open('dgb01_collision.json'))
fig, ax = plt.subplots(figsize=(10, 10))
for c in d['colliders']:
    if c['flags'] & 0x7ffffe00 == 0x7ffffe00: continue
    for t in c['tris']:
        if abs(t['n'][1]) < 0.5:
            ys = [v[1] for v in t['v']]
            if min(ys) > 40 or max(ys) < 5: continue
            xs = [v[0] for v in t['v']]; zs = [v[2] for v in t['v']]
            ax.plot(xs + [xs[0]], zs + [zs[0]], color='#555', lw=0.6)
gx = [k[0] for k, v in cells.items() if v == -1]; gz = [k[1] for k, v in cells.items() if v == -1]
ax.scatter(gx, gz, s=6, c='#ddd', marker='s', label='no clip with tested speeds')
hx = [k[0] for k, v in cells.items() if v not in (None, -1)]; hz = [k[1] for k, v in cells.items() if v not in (None, -1)]; hv = [v for v in cells.values() if v not in (None, -1)]
sc = ax.scatter(hx, hz, s=14, c=hv, cmap='viridis_r', marker='s')
plt.colorbar(sc, ax=ax, shrink=0.7, label='smallest Laki speed that clips out (mount target past the wall)')
ax.set_xlim(-620, 620); ax.set_ylim(620, -620); ax.set_aspect('equal'); ax.grid(alpha=.3)
ax.set_title('dgb_01 (bridges smashed), ground floor: Laki speed needed to clip out at each spot')
ax.set_xlabel('x'); ax.set_ylabel('z'); ax.legend(loc='lower right')
plt.savefig(outp, dpi=90); print(outp)
