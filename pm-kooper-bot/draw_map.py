"""top-down map of nok_14 collision: floors filled by height, walls as lines."""
import json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

d = json.load(open('nok14_collision.json'))
LZ = {5: 'deili1 (exit to nok_13)', 21: 'deili2 (exit to nok_15)'}
fig, ax = plt.subplots(figsize=(18, 7))
cmap = plt.get_cmap('viridis')
for c in d['colliders']:
    ignored = c['flags'] & 0x10000
    for t in c['tris']:
        xz = [(v[0], v[2]) for v in t['v']]
        ny = t['n'][1]
        if ny > 0.5:
            y = sum(v[1] for v in t['v']) / 3
            col = 'red' if c['id'] in LZ else cmap((y + 25) / 125)
            ax.add_patch(Polygon(xz, closed=True, fc=col, ec='k', lw=0.2, alpha=0.5 if not ignored else 0.15))
        else:
            ax.plot([p[0] for p in xz + xz[:1]], [p[1] for p in xz + xz[:1]],
                    color='orange' if ignored else ('purple' if c['flags'] & 0x8000 else 'black'),
                    lw=0.6 if not ignored else 0.4, ls='--' if ignored else '-')
for c in d['colliders']:
    if c['tris']:
        xs = [v[0] for t in c['tris'] for v in t['v']]; zs = [v[2] for t in c['tris'] for v in t['v']]
        ax.text(sum(xs) / len(xs), sum(zs) / len(zs), str(c['id']), fontsize=7, color='blue')
for i, name in LZ.items():
    t = d['colliders'][i]['tris'][0]['v']
    ax.text(t[0][0], t[0][2] - 12, name, fontsize=8, color='red')
for a in sys.argv[1:]:
    x, z = map(float, a.split(','))
    ax.plot([x], [z], 'r*', ms=12)
ax.set_xlim(-1050, 650); ax.set_ylim(140, -260)   # z down the screen like the game camera
ax.set_aspect('equal'); ax.set_xlabel('x'); ax.set_ylabel('z')
ax.set_title('nok_14 collision (floors colored by height, walls black, shell-passable walls purple, disabled dashed orange)')
plt.tight_layout(); plt.savefig('nok14_map.png', dpi=110)
