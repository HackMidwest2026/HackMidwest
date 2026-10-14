import pickle, sys, json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import LogNorm
A = pickle.load(open(sys.argv[1], 'rb'))
d = json.load(open('nok14_collision.json'))
fig, axes = plt.subplots(2, 1, figsize=(18, 13))
cells = list(A['cells'].values())
for ax, mode in zip(axes, ('height', 'tries')):
    for c in d['colliders']:
        ign = c['flags'] & 0x10000
        for t in c['tris']:
            xz = [(v[0], v[2]) for v in t['v']]
            if t['n'][1] > 0.5:
                col = '#f4a3a3' if c['id'] in (5, 21) else '#d9d9d9'
                ax.add_patch(Polygon(xz, closed=True, fc=col, ec='#bbbbbb', lw=0.2, alpha=0.25 if ign else 0.8, zorder=1))
            elif not ign:
                ax.plot([p[0] for p in xz + xz[:1]], [p[1] for p in xz + xz[:1]], color='black', lw=0.7, zorder=3)
    xs = [c['pos']['x'] for c in cells]; zs = [c['pos']['z'] for c in cells]
    if mode == 'height':
        sc = ax.scatter(xs, zs, c=[c['pos']['y'] for c in cells], s=3, cmap='viridis', zorder=4)
        fig.colorbar(sc, ax=ax, label='Mario height (y)', fraction=0.02)
        ax.set_title('Every distinct spot Mario has reached (%d spots, %d attempts). Black = solid walls, red = exits.' % (len(cells), A['tries']))
    else:
        tries = [max(1, c['chosen']) for c in cells]
        sc = ax.scatter(xs, zs, c=tries, s=4, cmap='inferno_r', norm=LogNorm(1, max(tries)), zorder=4)
        fig.colorbar(sc, ax=ax, label='attempts started from this spot', fraction=0.02)
        ax.set_title('How many attempts started from each spot (darker = tested more)')
    ax.axvline(-100, color='blue', lw=0.8, ls=':', zorder=2)
    ax.text(-97, 120, 'bridge wall\nx = -100', color='blue', fontsize=8)
    ax.set_xlim(float(sys.argv[3]) if len(sys.argv) > 3 else -1000, 600); ax.set_ylim(140, -260); ax.set_aspect('equal')
    ax.set_xlabel('x'); ax.set_ylabel('z')
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=90)
