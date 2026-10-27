"""Figure: pra_18 south->north lowest clipping Laki speed per standing spot, Mario facing left vs right (side by side)."""
import json, glob, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize
r = [x for f in glob.glob('/tmp/claude-0/pm/p18/facing_*.json') for x in json.load(open(f))]
d = json.load(open('pra18_collision.json'))
fig, axes = plt.subplots(1, 2, figsize=(11, 7.6), sharey=True, constrained_layout=True)
norm = Normalize(20, 60); cmap = plt.get_cmap('viridis')
for ax, face in zip(axes, ('left', 'right')):
    for c in d['colliders']:
        for t in c['tris']:
            v = t['v']
            if abs(t['n'][1]) < 0.3 and max(abs(p[2]) for p in v) < 60 and all(570 <= p[0] <= 640 for p in v):
                xs = [p[0] for p in v]; zs = [p[2] for p in v]
                ax.plot(xs + [xs[0]], zs + [zs[0]], color='#3a7bd5' if c['id'] == 19 else '#444', lw=3 if c['id'] == 19 else 1.4)
    pts = [(x, z, v) for x, z, f, v in r if f == face]
    ok = [(x, z, v) for x, z, v in pts if isinstance(v, (int, float))]
    no = [(x, z) for x, z, v in pts if v is None]
    un = [(x, z) for x, z, v in pts if v == 'unstandable']
    ax.scatter([p[0] for p in no], [p[1] for p in no], s=8, c='#ccc', marker='s', label='stands here, never clips (<=100)')
    ax.scatter([p[0] for p in un], [p[1] for p in un], s=8, c='#f2c0c0', marker='x', label="can't stand here (pushed out)")
    sc = ax.scatter([p[0] for p in ok], [p[1] for p in ok], s=26, c=[p[2] for p in ok], cmap=cmap, norm=norm, marker='s', edgecolors='k', linewidths=0.3, label='clips: colour = lowest speed')
    ax.plot(615.73, 27.22, marker='*', ms=18, color='gold', mec='k', label='video setup C-down spot (615.73, 27.22)')
    ax.set_title('Mario facing %s' % face.upper(), fontsize=13, color='crimson'); ax.set_xlim(603, 621); ax.set_ylim(48, -4); ax.set_aspect('equal'); ax.grid(alpha=.3)
    ax.set_xlabel('x'); ax.text(603.3, -2, 'mirror (z = 0) - north side above', color='#3a7bd5', fontsize=9)
axes[0].set_ylabel('z (south is down)')
fig.legend(*axes[1].get_legend_handles_labels(), loc='lower center', ncol=2, fontsize=9, bbox_to_anchor=(0.45, -0.07))
cb = fig.colorbar(sc, ax=axes, fraction=0.025); cb.set_label('lowest Lakilester speed that clips north')
fig.suptitle('pra_18 south->north mount clip: facing direction does not change where or at what speed it clips (493 spots, identical)', fontsize=12)
plt.savefig('/home/user/HackMidwest/pm-kooper-bot/figures/pra18_sn_facing.png', dpi=90, bbox_inches='tight')
