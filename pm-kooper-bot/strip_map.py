"""Close-up of where Mario can stand for the reverse mirror clip on pra_01's second step (and the stair rail),
from fine forced-speed data (fine_zone.py, x step 0.25, z step 1). Categories per spot: clips AND Lakilester can
reach the needed speed there (distance >= 370.4 from the rock-top turnaround (530.8, -13), walking toward it), clips
but too close for Laki to get fast enough, rail (sloped floor, Mario can stand) without clip, flat floor without
clip (second step y -20 / third step y -10), not standable (blank). Marks the working clip's C-down spot.
usage: strip_map.py <out.png> <fine json> [more fine jsons]"""
import json, math, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
out = sys.argv[1]
D = {}
for f in sys.argv[2:]:
    for k, v in json.load(open(f)).items():
        D.setdefault(k, v)
        if v['S']: D[k] = v
X0, X1, Z0, Z1 = 862, 895, -175, -62
xs = np.arange(X0, X1 + 0.001, 0.25); zs = np.arange(Z0, Z1 + 1)
G = np.full((len(zs), len(xs)), np.nan)
NEED = 115.75 / 0.3125
for k, v in D.items():
    x, z = map(float, k.split(','))
    if not (X0 <= x <= X1 and Z0 <= z <= Z1): continue
    i = int(round((x - X0) / 0.25)); j = int(round(z - Z0))
    y = v['y']
    if v['S']:
        G[j, i] = 4 if math.hypot(x - 530.8, z + 13) >= NEED else 3
    elif abs(y + 20) < 0.3 or abs(y + 10) < 0.3:
        G[j, i] = 0 if abs(y + 20) < 0.3 else 1
    else:
        G[j, i] = 2                                   # sloped rail
cols = ['#e4e3de', '#cfcdc6', '#eb6834', '#9ec5f4', '#1c5cab']
INK, INK2, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': '#d6d5cf'})
fig, ax = plt.subplots(figsize=(11, 7.4), dpi=160, facecolor=SURF)
ax.set_facecolor(SURF)
ax.pcolormesh(xs, zs, G, cmap=ListedColormap(cols), vmin=-0.5, vmax=4.5, shading='nearest')
ax.plot([882.7], [-144.7], marker='*', ms=16, mfc='#fcfcfb', mec=INK, mew=1.5, ls='none')
ax.annotate('working clip: C-down at (882.7, -144.7)', (882.7, -144.7), (886, -118), fontsize=9,
            arrowprops=dict(arrowstyle='-', color=INK2, lw=1))
ax.plot([886.3], [-151.6], marker='o', ms=7, mfc='none', mec=INK, mew=1.5, ls='none')
ax.annotate('your screenshot: Mario on the rail (886.3, -151.6)', (886.3, -151.6), (868, -168), fontsize=9,
            arrowprops=dict(arrowstyle='-', color=INK2, lw=1))
ax.set_xlim(X0, X1); ax.set_ylim(Z0, Z1); ax.invert_yaxis()
ax.set_xlabel('x'); ax.set_ylabel('z  (top wall up, mirror down)')
ax.set_title('Where Mario can stand for the reverse mirror clip (second step, pra_01)', loc='left', fontsize=12)
ax.legend(handles=[Patch(facecolor=cols[4], label='clips, and Laki can reach the speed here (walking toward the rock)'),
                   Patch(facecolor=cols[3], label='clips at 115.75-193.75, but too close to the rock: Laki tops out below 115.75'),
                   Patch(facecolor=cols[2], label='stair rail (sloped): Mario can stand, never clips'),
                   Patch(facecolor=cols[0], label='second step (y -20): Mario can stand, no clip'),
                   Patch(facecolor=cols[1], label='third step (y -10): Mario can stand, no clip'),
                   Patch(facecolor=SURF, edgecolor='#d6d5cf', label='blank = Mario cannot stand still here')],
          loc='upper left', bbox_to_anchor=(0, -0.09), ncol=2, fontsize=8, frameon=False)
fig.text(0.01, 0.01, 'Forced-speed C-down tests on a 0.25 x 1 unit grid. "Laki can reach" = 0.25 x d + d/16 >= 115.75 with d = distance to the rock-top turnaround (530.8, -13), d >= 370.4.', fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(out, facecolor=SURF)
print('counts:', {n: int((G == i).sum()) for i, n in enumerate(['step2', 'step3', 'rail', 'clip_far', 'clip_ok'])})
