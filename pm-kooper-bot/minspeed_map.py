"""Map by MARIO's position (reflected side of pra_01): colour = the minimum Lakilester speed at the mount that clips
Mario through the mirror from that spot (forced-speed data from rev_fullmap.py, speeds 20..300 step 5).
Grey = Mario can stand there but no tested speed clips. Hatched = clips for a run of >= 4 consecutive speed steps
(not just one exact value). Black outline = spots where the minimum is within reach in theory: the best speed the
follow formula allows with Lakilester anywhere on the floor, his next history point at a far corner, and him not
below Mario (speed_bound.py verified the formula in RAM).
usage: minspeed_map.py <fullmap.jsonl> <collision.json> <out.png>"""
import json, math, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
src, col, out = sys.argv[1:4]
rows = [json.loads(l) for l in open(src)]
xs = np.arange(500, 1001, 5); zs = np.arange(-215, -14, 5)
MIN = np.full((len(zs), len(xs)), np.nan); STAND = np.zeros_like(MIN, bool); RANGE = np.zeros_like(MIN, bool)
for r in rows:
    i = int((r['x'] - 500) / 5)
    for z, v in r['z'].items():
        j = int((int(z) + 215) / 5); STAND[j, i] = True
        S = v['S']
        if S:
            MIN[j, i] = min(S)
            run, best = 1, 1
            for a, b in zip(S, S[1:]):
                run = run + 1 if b == a + 5 else 1; best = max(best, run)
            RANGE[j, i] = best >= 4
# theoretical best speed for Mario at each spot
tris = [t['v'] for c in json.load(open(col))['colliders'] for t in c['tris'] if t['n'][1] > 0.5]
def has_floor(x, z):
    for (x1, _, z1), (x2, _, z2), (x3, _, z3) in tris:
        dd = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
        if abs(dd) < 1e-9: continue
        a = ((z2 - z3) * (x - x3) + (x3 - x2) * (z - z3)) / dd; b = ((z3 - z1) * (x - x3) + (x1 - x3) * (z - z3)) / dd
        if min(a, b, 1 - a - b) >= -1e-6: return True
    return False
LAKI = [(x, z) for x in range(470, 1001, 10) for z in range(-220, -5, 10) if has_floor(x, z)]
ENTRIES = [(985, -205), (987, -165), (980, -20), (505, -205), (505, -20), (740, -212)]
def speed(lx, lz, mx, mz, hx, hz):
    dM = math.hypot(lx - mx, lz - mz); d = math.hypot(lx - hx, lz - hz)
    s = 0.25 * dM if dM >= 50 else 3.0
    if s < d: s = 0.25 * d if s >= 0.25 * d else s + d / 16
    return s
BEST = np.full_like(MIN, np.nan)
for j, z in enumerate(zs):
    for i, x in enumerate(xs):
        if not np.isnan(MIN[j, i]):
            BEST[j, i] = max(speed(lx, lz, x, z, hx, hz) for lx, lz in LAKI for hx, hz in ENTRIES)
REACH = (~np.isnan(MIN)) & (BEST >= MIN)
ramp = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95', '#104281', '#0d366b']
cmap = LinearSegmentedColormap.from_list('blue', ramp)
INK, INK2, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': '#d6d5cf'})
fig, ax = plt.subplots(figsize=(11, 7.0), dpi=160, facecolor=SURF)
ax.set_facecolor(SURF)
G = np.where(STAND & np.isnan(MIN), 1.0, np.nan)
ax.pcolormesh(xs, zs, G, cmap=LinearSegmentedColormap.from_list('g', ['#d6d5cf', '#d6d5cf']), shading='nearest')
vmin, vmax = 100, 200
im = ax.pcolormesh(xs, zs, MIN, cmap=cmap, vmin=vmin, vmax=vmax, shading='nearest')
ax.contourf(xs, zs, RANGE.astype(float), levels=[0.5, 1.5], colors='none', hatches=['////'])
if REACH.any():
    ax.contour(xs, zs, REACH.astype(float), levels=[0.5], colors=[INK], linewidths=2)
ax.set_xlim(497.5, 1002.5); ax.set_ylim(-217.5, 0); ax.invert_yaxis()
ax.text(860, -4, 'mirror (z = 0)', color=INK2, fontsize=9)
ax.text(740, -216, 'top wall', color=INK2, fontsize=9, va='top')
ax.set_xlabel('x (where Mario stands)'); ax.set_ylabel('z')
ax.set_title('Minimum Lakilester speed needed to clip, by where Mario stands', loc='left', fontsize=12)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label('minimum speed that clips (100-200 shown)', color=INK2)
cb.outline.set_edgecolor('#d6d5cf')
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[Patch(facecolor='#d6d5cf', label='Mario can stand here, no speed 20-300 clips'),
                   Patch(facecolor='white', edgecolor=INK2, hatch='////', label='clips for a range of speeds (not one exact value)'),
                   Line2D([], [], color=INK, lw=2, label='reachable in theory (best possible Laki speed >= minimum)'),
                   Patch(facecolor=SURF, edgecolor='#d6d5cf', label='blank = Mario cannot stand here')],
          loc='upper left', bbox_to_anchor=(0, -0.11), ncol=2, fontsize=8, frameon=False)
fig.text(0.01, 0.01, 'Forced-speed test: Mario standing still, C-down, Laki speed set to S during the mount delay; 5-unit grid, speeds 20-300 in steps of 5.', fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(out, facecolor=SURF)
n = int((~np.isnan(MIN)).sum())
print('spots that clip:', n, ' min speed overall:', np.nanmin(MIN), ' reachable spots:', int(REACH.sum()))
for j, i in zip(*np.where(REACH)): print('  reachable: Mario (%d, %d) needs %d, best %.1f, range %s' % (xs[i], zs[j], MIN[j, i], BEST[j, i], RANGE[j, i]))
