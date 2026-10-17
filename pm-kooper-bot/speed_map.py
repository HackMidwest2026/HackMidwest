"""Colour-coded map of the reflected side of pra_01: Lakilester's follow speed (game formula, verified in RAM by
speed_bound.py) as a function of where Lakilester is, with Mario standing in the clip strip (878, -108) and
Lakilester's next history point at the top-right corner (985, -205), Lakilester not below Mario.
Overlays: the clip strip (any speed 120-190 crosses), the near-mirror spots that cross at one exact speed
(data/easy_near_mirror.json), the push start / stale target, the 100 and 120 contours; areas with no floor greyed.
usage: speed_map.py <collision.json> <easy_near_mirror.json> <out.png>"""
import json, math, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
col, near, out = sys.argv[1:4]
MX, MZ = 878.0, -108.0          # Mario in the strip
HX, HZ = 985.0, -205.0          # next history point (top-right corner)
def speed(lx, lz):
    dM = math.hypot(lx - MX, lz - MZ); d = math.hypot(lx - HX, lz - HZ)
    s = 0.25 * dM if dM >= 50 else 3.0
    if s < d:
        s = 0.25 * d if s >= 0.25 * d else s + d / 16
    return s
# floor presence on the reflected side from the collision dump
tris = [t['v'] for c in json.load(open(col))['colliders'] for t in c['tris'] if t['n'][1] > 0.5]
def has_floor(x, z):
    for (x1, _, z1), (x2, _, z2), (x3, _, z3) in tris:
        dd = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
        if abs(dd) < 1e-9: continue
        a = ((z2 - z3) * (x - x3) + (x3 - x2) * (z - z3)) / dd; b = ((z3 - z1) * (x - x3) + (x1 - x3) * (z - z3)) / dd
        if min(a, b, 1 - a - b) >= -1e-6: return True
    return False
xs = np.arange(470, 1001, 4); zs = np.arange(-225, 1, 4)
S = np.array([[speed(x, z) for x in xs] for z in zs])
F = np.array([[has_floor(x, z) for x in xs] for z in zs])
ramp = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95', '#104281', '#0d366b']
cmap = LinearSegmentedColormap.from_list('blue', ramp)
INK, INK2, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': '#d6d5cf'})
fig, ax = plt.subplots(figsize=(11, 7.0), dpi=160, facecolor=SURF)
ax.set_facecolor('#e4e3de')
Sm = np.where(F, S, np.nan)
im = ax.pcolormesh(xs, zs, Sm, cmap=cmap, vmin=0, vmax=130, shading='nearest')
cs = ax.contour(xs, zs, Sm, levels=[100, 120], colors=[INK2, INK], linewidths=[1.0, 2.0], linestyles=['--', '-'])
ax.clabel(cs, fmt={100: '100', 120: '120 (needed)'}, fontsize=9, inline=True)
# clip strip and near-mirror exact-speed spots
ax.add_patch(Rectangle((872, -144), 12, 72, fill=False, ec=INK, lw=2, hatch='////'))
ax.annotate('clip strip: Mario here,\nany speed 120-190 crosses', (884, -108), (905, -60), fontsize=9,
            arrowprops=dict(arrowstyle='-', color=INK2, lw=1))
nm = [tuple(map(int, k.split(','))) for k, v in json.load(open(near)).items() if v['S']]
ax.scatter([p[0] for p in nm], [p[1] for p in nm], s=4, c='#eb6834', lw=0, label='near-mirror spots: cross at ONE exact speed (110-150)')
ax.plot([MX], [MZ], marker='o', ms=8, mfc=SURF, mec=INK, mew=2, ls='none', label='Mario (878, -108) for this map')
ax.plot([HX], [HZ], marker='s', ms=8, mfc=SURF, mec=INK, mew=2, ls='none', label="Laki's next history point (985, -205)")
ax.plot([592], [-13], marker='^', ms=9, mfc=SURF, mec=INK, mew=2, ls='none', label='current push start / stale target (592, -13)')
ax.text(860, -4, 'mirror (z = 0)', color=INK2, fontsize=9)
ax.text(740, -220, 'top wall', color=INK2, fontsize=9, va='bottom')
ax.text(975, -120, 'palace', color=INK2, fontsize=9, rotation=90, va='center')
ax.set_xlim(470, 1000); ax.set_ylim(-225, 0)   # mirror at the top edge of the plot
ax.invert_yaxis()                               # top wall up, mirror down: as the camera sees this side
ax.set_xlabel('x'); ax.set_ylabel('z')
ax.set_title("Lakilester's speed by where he is (Mario in the clip strip, Laki not below Mario)", loc='left', fontsize=12, color=INK)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label('Laki speed at that spot', color=INK2)
cb.outline.set_edgecolor('#d6d5cf')
leg = ax.legend(loc='upper left', bbox_to_anchor=(0, -0.11), ncol=2, fontsize=8, frameon=False)
fig.text(0.01, 0.01, 'Speed = 0.25 x distance to Mario, then capped at 0.25 x distance to his next history point or raised by 1/16 of it (game formula). '
         'Grey = no floor. Laki lower than Mario is capped at 6 everywhere.', fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(out, facecolor=SURF)
print('max %.1f at' % np.nanmax(Sm), np.unravel_index(np.nanargmax(Sm), Sm.shape), 'cells >=120:', int(np.nansum(Sm >= 120)))
