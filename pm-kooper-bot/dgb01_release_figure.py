"""Figure: remount speeds reachable after pushing Laki across dgb_01 (dgb01_release_map.py outputs). Each point is
where Mario mounts, coloured by Laki's speed; the clean-floor clip spots (speed >= 160 needed) are outlined in red.
usage: dgb01_release_figure.py OUT.png COLLISION.json CLIPMAP.jsonl RELEASE.jsonl ..."""
import json, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
outp, coll, clipmap, rels = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
d = json.load(open(coll))
fig, ax = plt.subplots(figsize=(10, 10))
for c in d['colliders']:
    if c['flags'] & 0x7ffffe00 == 0x7ffffe00: continue
    for t in c['tris']:
        ys = [v[1] for v in t['v']]
        if abs(t['n'][1]) < 0.5 and min(ys) < 40 and max(ys) > 5:
            xs = [v[0] for v in t['v']]; zs = [v[2] for v in t['v']]; ax.plot(xs + [xs[0]], zs + [zs[0]], color='#555', lw=0.6)
pts = []
for f in rels:
    for l in open(f):
        r = json.loads(l)
        if r['S'] > 0.5: pts.append((r['x'], r['z'], r['S']))
pts.sort(key=lambda p: p[2])
sc = ax.scatter([p[0] for p in pts], [p[1] for p in pts], c=[p[2] for p in pts], s=8, cmap='plasma', vmin=0, vmax=max(220, max(p[2] for p in pts)))
plt.colorbar(sc, ax=ax, shrink=0.7, label='Laki speed at the remount')
clip = [json.loads(l) for l in open(clipmap)]
cx = [r['x'] for r in clip if any(q[4] for q in r['r'])]; cz = [r['z'] for r in clip if any(q[4] for q in r['r'])]
ax.scatter(cx, cz, s=30, facecolors='none', edgecolors='red', label='spots that clip out (need speed >= 160)')
hi = [p for p in pts if p[2] >= 160]
ax.set_title('dgb_01 (floor intact): remount speeds after pushing Laki across the room\nmax %.1f; %d mount spots with speed >= 160' % (max(p[2] for p in pts), len(hi)))
ax.set_xlim(-620, 620); ax.set_ylim(620, -620); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(loc='lower right')
ax.set_xlabel('x'); ax.set_ylabel('z')
plt.savefig(outp, dpi=90); print(outp)
