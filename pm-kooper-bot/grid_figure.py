"""figure for corner_grid.py: which poked landing spots push Mario through, vs where real spin-jumps land."""
import json, math, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

G = json.load(open(sys.argv[1]))
P = json.load(open(sys.argv[2]))
OUT = sys.argv[3]
SURF, INK, INK2 = '#fcfcfb', '#0b0b0b', '#52514e'
LIP, DIAG = ((-110, -102), (-100, -100)), ((-110, -102), (-52, -118))


def dseg(p, a, b):
    t = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)))
    return math.hypot(p[0] - a[0] - t * (b[0] - a[0]), p[1] - a[1] - t * (b[1] - a[1]))


def side(p, a, b):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def solid(p):
    ref = (-100, -101)
    return p[0] >= -100 or (p[0] > -110 and side(p, *DIAG) * side(ref, *DIAG) > 0 and side(p, *LIP) * side(ref, *LIP) >= 0)


fig, ax = plt.subplots(figsize=(7.2, 6.4), dpi=110, facecolor=SURF)
ax.set_facecolor(SURF)
ax.add_patch(Polygon([(-110, -102), (-100, -100), (-100, -104.76)], fc='#e8e7e3', ec='none', zorder=0))
ax.add_patch(Polygon([(-100, -125), (-95, -125), (-95, -90), (-100, -90)], fc='#e8e7e3', ec='none', zorder=0))
for (a, b) in (LIP, DIAG, ((-100, -100), (-100, -20))):
    ax.plot([a[0], b[0]], [a[1], b[1]], color='#e34948', lw=2.5, zorder=3)
cats = {'through': [], 'back': [], 'none': []}
for r in G:
    p = (r['x'], r['z'])
    ws = [h['why'] for h in r['hits']]
    if any('14' in w for w in ws):
        cats['through'].append(p)
    elif ws:
        cats['back'].append(p)
    else:
        cats['none'].append(p)
for k, c, lab in (('none', '#d4d3cf', 'no clip'), ('back', '#f2a7a7', 'pushed back west (start already inside the wall)'),
                  ('through', '#e34948', 'pushed east onto the gap floor (start inside the wall)')):
    if cats[k]:
        ax.scatter(*zip(*cats[k]), s=6, c=c, label='%s: %d' % (lab, len(cats[k])), zorder=2, marker='s')
real = [(p['pos'][0], p['pos'][2]) for p in P]
ax.scatter(*zip(*real), s=14, c='#2a78d6', label='real spin-jump landings (from inputs): %d' % len(real), zorder=4)
ax.set_xlim(-123, -95); ax.set_ylim(-95, -115)
ax.set_aspect('equal'); ax.tick_params(labelsize=7)
ax.set_xlabel('x', fontsize=8); ax.set_ylabel('z  (up = away from camera)', fontsize=8)
ax.legend(fontsize=7, loc='lower left', framealpha=0.95)
ax.set_title('nok_14 north corner: 1,517 landing spots x 91 stick angles x 2 strengths', fontsize=9, color=INK)
ax.text(-106.5, -104.6, 'solid\nwedge', fontsize=7, color=INK2, ha='center')
fig.tight_layout()
fig.savefig(OUT, facecolor=SURF)
legal_through = [p for p in cats['through'] if not solid(p)]
print('through:', len(cats['through']), 'from legal spots:', len(legal_through))
dists = sorted(min(dseg(p, *s) for s in (LIP, DIAG)) for p in real if not solid(p))
print('closest real landing to the wedge walls: %.2f' % dists[0])
