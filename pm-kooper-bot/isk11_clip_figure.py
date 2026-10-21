"""Figure for isk11_clip_map.py results: top-down isk_11 (active floors shaded by height, walls red) with every
scanned spot drawn grey (no clip at any tested speed) or coloured by the lowest mount speed that reaches isk_19;
a ring marks spots whose clip speeds form more than one band. Also prints the speed bands per hit spot.
usage: isk11_clip_figure.py OUT.png JSONL..."""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
outp, files = sys.argv[1], sys.argv[2:]
d = json.load(open('/tmp/claude-0/pm/bot1/isk11_collision.json'))
rows = [json.loads(l) for fn in files for l in open(fn)]
def bands(hits, step):
    out = []
    for s in sorted(hits):
        if out and s - out[-1][1] <= step + 1e-6: out[-1][1] = s
        else: out.append([s, s])
    return out
fig, ax = plt.subplots(figsize=(15, 7)); cm = plt.get_cmap('Greys')
for c in d['colliders']:
    if c['flags'] & 0x7FFFFE00: continue
    for t in c['tris']:
        xs = [(v[0], v[2]) for v in t['v']]
        if t['n'][1] > 0.7:
            y = sum(v[1] for v in t['v']) / 3
            ax.add_patch(Polygon(xs, closed=True, fc=cm(0.15 + 0.6 * (y + 910) / 480), ec='none', alpha=.5))
        elif abs(t['n'][1]) < 0.3:
            ax.plot([p[0] for p in xs] + [xs[0][0]], [p[1] for p in xs] + [xs[0][1]], 'r-', lw=.4)
miss = [(r['x'], r['z']) for r in rows if not r['hits']]
ax.scatter([m[0] for m in miss], [m[1] for m in miss], s=4, c='#bbbbbb', marker='s', lw=0)
hit = [r for r in rows if r['hits']]
if hit:
    sc = ax.scatter([r['x'] for r in hit], [r['z'] for r in hit], s=22, c=[min(r['hits']) for r in hit], cmap='plasma', marker='s', lw=0)
    fig.colorbar(sc, ax=ax, label='lowest mount speed that reaches isk_19')
    multi = [r for r in hit if len(bands(r['hits'], 4)) > 1]
    ax.scatter([r['x'] for r in multi], [r['z'] for r in multi], s=60, facecolors='none', edgecolors='k', lw=.6)
ax.add_patch(Polygon([(188, 500), (252, 500), (252, 564), (188, 564)], closed=True, fill=False, ec='lime', lw=1.5))
ax.text(190, 497, 'isk_19 exit floor (y -910)', color='green', fontsize=8)
ax.set_aspect('equal'); ax.invert_yaxis(); ax.set_xlabel('x'); ax.set_ylabel('z (camera at bottom)')
ax.set_title('isk_11: where a Lakilester mount clips to isk_19 (%d spots scanned, %d clip)' % (len(rows), len(hit)))
plt.savefig(outp, dpi=80, bbox_inches='tight')
for r in sorted(hit, key=lambda r: (r['x'], r['z'])):
    print('(%.0f, %.0f) y %.0f floor %d: speeds %s' % (r['x'], r['z'], r['y'], r['floor'], ', '.join('%g-%g' % tuple(b) if b[0] != b[1] else '%g' % b[0] for b in bands(r['hits'], 4))))
