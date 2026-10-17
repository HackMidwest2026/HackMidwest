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
# theoretical best speed for Mario at each spot: Lakilester can only turn around at a point of Mario's history, so
# both his position L and his next history point H range over spots where Mario can stand (5-unit grid). For a given
# L the best H is the farthest one (dmax): speed = 0.25*dM + dmax/16 if dmax > dM else 0.25*dM.
tris = [t['v'] for c in json.load(open(col))['colliders'] for t in c['tris'] if t['n'][1] > 0.5]
def has_floor(x, z):
    for (x1, _, z1), (x2, _, z2), (x3, _, z3) in tris:
        dd = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
        if abs(dd) < 1e-9: continue
        a = ((z2 - z3) * (x - x3) + (x3 - x2) * (z - z3)) / dd; b = ((z3 - z1) * (x - x3) + (x1 - x3) * (z - z3)) / dd
        if min(a, b, 1 - a - b) >= -1e-6: return True
    return False
SP = np.array([(x, z) for j, z in enumerate(zs) for i, x in enumerate(xs) if STAND[j, i]], float)
DMAX = np.array([np.hypot(SP[:, 0] - lx, SP[:, 1] - lz).max() for lx, lz in SP])
ROCK = np.array([[555.0, -13.0], [592.0, -13.0]])          # turnaround with the rock start (history fill)
ROCK_DMAX = np.array([np.hypot(SP[:, 0] - lx, SP[:, 1] - lz).max() for lx, lz in ROCK])
def best_from(L, dmax, mx, mz):
    dM = np.hypot(L[:, 0] - mx, L[:, 1] - mz)
    s = np.where(dmax > dM, 0.25 * dM + dmax / 16, 0.25 * dM)
    return s.max()
BEST = np.full_like(MIN, np.nan); BEST_ROCK = np.full_like(MIN, np.nan)
for j, z in enumerate(zs):
    for i, x in enumerate(xs):
        if not np.isnan(MIN[j, i]):
            BEST[j, i] = best_from(SP, DMAX, x, z); BEST_ROCK[j, i] = best_from(ROCK, ROCK_DMAX, x, z)
TOL = 4                                                    # 5-step grid: the true minimum can be up to 4 lower
OVER = (~np.isnan(MIN)) & (MIN - TOL > BEST)               # needs more than Laki can ever reach there
REACH = (~np.isnan(MIN)) & (MIN - TOL <= BEST_ROCK)        # reachable with the rock-start route
print('room-wide max possible speed at any clip spot: %.1f' % np.nanmax(BEST))
MIN = np.where(OVER, np.nan, MIN); RANGE = RANGE & ~OVER
ramp = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95', '#104281', '#0d366b']
cmap = LinearSegmentedColormap.from_list('blue', ramp)
INK, INK2, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': '#d6d5cf'})
fig, ax = plt.subplots(figsize=(11, 7.0), dpi=160, facecolor=SURF)
ax.set_facecolor(SURF)
G = np.where(STAND & np.isnan(MIN) & ~OVER, 1.0, np.nan)
GO = np.where(OVER, 1.0, np.nan)
ax.pcolormesh(xs, zs, G, cmap=LinearSegmentedColormap.from_list('g', ['#d6d5cf', '#d6d5cf']), shading='nearest')
ax.pcolormesh(xs, zs, GO, cmap=LinearSegmentedColormap.from_list('o', ['#b9b8b1', '#b9b8b1']), shading='nearest')
vmin, vmax = 110, 140
im = ax.pcolormesh(xs, zs, MIN, cmap=cmap, vmin=vmin, vmax=vmax, shading='nearest')
ax.contourf(xs, zs, RANGE.astype(float), levels=[0.5, 1.5], colors='none', hatches=['////'])
if REACH.any():
    ax.contour(xs, zs, REACH.astype(float), levels=[0.5], colors=[INK], linewidths=2)
ax.set_xlim(497.5, 1002.5); ax.set_ylim(-217.5, 0); ax.invert_yaxis()
ax.text(860, -4, 'mirror (z = 0)', color=INK2, fontsize=9)
ax.text(740, -216, 'top wall', color=INK2, fontsize=9, va='top')
ax.set_xlabel('x (where Mario stands)'); ax.set_ylabel('z')
ax.set_title('Minimum Lakilester speed needed to clip, by where Mario stands (unreachable spots removed)', loc='left', fontsize=12)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label('minimum speed that clips', color=INK2)
cb.outline.set_edgecolor('#d6d5cf')
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[Patch(facecolor='#d6d5cf', label='Mario can stand here, no speed 20-300 clips'),
                   Patch(facecolor='white', edgecolor=INK2, hatch='////', label='clips for a range of speeds (not one exact value)'),
                   Patch(facecolor='#b9b8b1', label='clips only above the most Laki can reach there (removed)'),
                   Line2D([], [], color=INK, lw=2, label='reachable with the rock-start push (turnaround x 555-592)'),
                   Patch(facecolor=SURF, edgecolor='#d6d5cf', label='blank = Mario cannot stand here')],
          loc='upper left', bbox_to_anchor=(0, -0.11), ncol=2, fontsize=8, frameon=False)
fig.text(0.01, 0.01, 'Forced-speed test: 5-unit grid, speeds in steps of 5 (true minimum up to 4 lower; the strip is really 116).\nMax reachable: verified follow formula, with Laki and his next history point anywhere Mario can stand (at most %.0f anywhere).' % np.nanmax(BEST), fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.045, 1, 1))
fig.savefig(out, facecolor=SURF)
n = int((~np.isnan(MIN)).sum())
print('spots that clip:', n, 'removed (unreachable):', int(OVER.sum()), ' min speed overall:', np.nanmin(MIN), ' reachable spots:', int(REACH.sum()))
for j, i in list(zip(*np.where(REACH)))[:0]: print('  reachable: Mario (%d, %d) needs %d, best %.1f, range %s' % (xs[i], zs[j], MIN[j, i], BEST[j, i], RANGE[j, i]))
