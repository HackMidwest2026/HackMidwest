"""Detailed figure for a fine isk11_clip_map.py run (right side of isk_11): left panel = lowest mount speed that
reaches isk_19 at each spot, right panel = how many tested speeds clip there (band width x speed step). Grey = no
clip at any tested speed. Floors shaded by height, walls red, isk_19 exit floor green, RTA spot (x 316 on the -575
step) marked. usage: isk11_clip_figure2.py OUT.png STEP JSONL..."""
import json, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
outp, step, files = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
d = json.load(open('/tmp/claude-0/pm/bot1/isk11_collision.json'))
rows = [json.loads(l) for fn in files for l in open(fn)]
hit = [r for r in rows if r['hits']]; miss = [r for r in rows if not r['hits']]
fig, axs = plt.subplots(1, 2, figsize=(20, 9))
for ax, key, label, cmap in ((axs[0], lambda r: min(r['hits']), 'lowest mount speed that reaches isk_19', 'plasma'),
                             (axs[1], lambda r: len(r['hits']) * step, 'width of the clipping speed range (speeds)', 'viridis')):
    for c in d['colliders']:
        if c['flags'] & 0x7FFFFE00: continue
        for t in c['tris']:
            xs = [(v[0], v[2]) for v in t['v']]
            if t['n'][1] > 0.7:
                y = sum(v[1] for v in t['v']) / 3
                ax.add_patch(Polygon(xs, closed=True, fc=plt.get_cmap('Greys')(0.15 + 0.6 * (y + 910) / 480), ec='none', alpha=.5))
            elif abs(t['n'][1]) < 0.3:
                ax.plot([p[0] for p in xs] + [xs[0][0]], [p[1] for p in xs] + [xs[0][1]], 'r-', lw=.5)
    ax.scatter([r['x'] for r in miss], [r['z'] for r in miss], s=6, c='#c8c8c8', marker='s', lw=0)
    sc = ax.scatter([r['x'] for r in hit], [r['z'] for r in hit], s=16, c=[key(r) for r in hit], cmap=cmap, marker='s', lw=0)
    fig.colorbar(sc, ax=ax, label=label, fraction=0.04)
    ax.add_patch(Rectangle((188, 500), 64, 64, fill=False, ec='lime', lw=1.5)); ax.text(190, 497, 'isk_19 exit floor', color='green', fontsize=8)
    ax.plot([316], [530], marker='*', ms=14, mfc='none', mec='k'); ax.text(318, 527, 'RTA spot', fontsize=8)
    for yv, (tx, tz) in ((-520, (250, 470)), (-550, (262, 560)), (-575, (300, 590)), (-600, (400, 450)), (-470, (360, 400))):
        ax.text(tx, tz, 'y %d' % yv, fontsize=8, color='#444')
    ax.set_xlim(230, 450); ax.set_ylim(610, 360); ax.set_aspect('equal'); ax.set_xlabel('x'); ax.set_ylabel('z (camera at bottom)')
axs[0].set_title('isk_11 right side: lowest clip speed (%d spots, %d clip)' % (len(rows), len(hit)))
axs[1].set_title('how forgiving: number of speeds that clip')
plt.savefig(outp, dpi=80, bbox_inches='tight')
print('saved', outp, len(rows), 'spots', len(hit), 'clip')
