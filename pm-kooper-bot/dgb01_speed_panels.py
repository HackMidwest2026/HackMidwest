"""dgb_01 speed vs position figures from dgb01_mount_map.py data (west region, 10-unit grid, speeds every 5).
  1) PANELS: one top-down map per Laki speed, spots that clip out at that speed highlighted.
  2) COLUMNS: for each x column, z (vertical) vs Laki speed (horizontal); green = clips out, grey = stays inside.
env: COLL (collision json), BOX=x0,x1,z0,z1 (region), GRID (keep only this grid), SMIN, PMIN, PSTEP (panel speeds), ALLCOLS=1
usage: dgb01_speed_panels.py MAP.jsonl[.gz] PANELS.png COLUMNS.png"""
import json, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import numpy as np
src, out1, out2 = sys.argv[1:4]
import os
BOX = [float(v) for v in os.environ.get('BOX', '-490,-200,-450,80').split(',')]      # x0,x1,z0,z1 of the region to draw
GRID = int(os.environ.get('GRID', '0')); SMIN = float(os.environ.get('SMIN', '150'))
PSTEP = int(os.environ.get('PSTEP', '10')); PMIN = int(os.environ.get('PMIN', '220'))
R = {}
import gzip
for l in (gzip.open(src, 'rt') if src.endswith('.gz') else open(src)):
    r = json.loads(l)
    if not (BOX[0] <= r['x'] <= BOX[1] and BOX[2] <= r['z'] <= BOX[3]) or (GRID and (r['x'] % GRID or r['z'] % GRID)): continue
    R.setdefault((r['x'], r['z']), {}).update({q[0]: q[4] for q in r['r'] if q[0] >= SMIN})
xs = sorted({k[0] for k in R}); zs = sorted({k[1] for k in R}); Ss = sorted({s for v in R.values() for s in v})
d = json.load(open(os.environ.get('COLL', 'dgb01_collision.json')))
walls = []
for c in d['colliders']:
    if c['flags'] & 0x7ffffe00 == 0x7ffffe00: continue
    for t in c['tris']:
        ys = [v[1] for v in t['v']]
        if abs(t['n'][1]) < 0.5 and min(ys) < 40 and max(ys) > 5:
            walls.append(([v[0] for v in t['v']], [v[2] for v in t['v']]))
def draw_walls(ax):
    for wx, wz in walls: ax.plot(wx + [wx[0]], wz + [wz[0]], color='#555', lw=0.5)
# 1) panels
panel_S = [s for s in Ss if s >= PMIN and (s - PMIN) % PSTEP == 0][:18]
cols = 6; rows = (len(panel_S) + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.6))
for ax, S in zip(axs.flat, panel_S):
    draw_walls(ax)
    inside = [(x, z) for (x, z), v in R.items() if S in v and not v[S]]
    clip = [(x, z) for (x, z), v in R.items() if S in v and v[S]]
    if inside: ax.scatter(*zip(*inside), s=5, c='#ccc', marker='s', lw=0)
    if clip: ax.scatter(*zip(*clip), s=7, c='#1a9850', marker='s', lw=0)
    ax.set_xlim(BOX[0] - 20, BOX[1] + 20); ax.set_ylim(BOX[3] + 20, BOX[2] - 20); ax.set_aspect('equal'); ax.set_title('Laki speed %g: %d spots' % (S, len(clip)), fontsize=9)
    ax.tick_params(labelsize=6)
for ax in list(axs.flat)[len(panel_S):]: ax.axis('off')
fig.suptitle('dgb_01 ground floor: spots where the mount clips Mario out, per Laki speed (green). x right, z down.', fontsize=11)
plt.tight_layout(rect=(0, 0, 1, 0.96)); plt.savefig(out1, dpi=85); plt.close(fig)
# 2) columns: z vs speed per x
cx = [x for x in xs if any(v.get(s) for (xx, z), v in R.items() if xx == x for s in v)] if not os.environ.get('ALLCOLS') else xs
cols = 4; rows = (len(cx) + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(cols * 4.2, rows * 3.4), squeeze=False)
for ax, x in zip(axs.flat, cx):
    img = np.full((len(zs), len(Ss)), np.nan)
    for i, z in enumerate(zs):
        v = R.get((x, z))
        if not v: continue
        for j, S in enumerate(Ss):
            if S in v: img[i, j] = v[S]
    cmap = matplotlib.colors.ListedColormap(['#d9d9d9', '#1a9850']); cmap.set_bad('white')
    ax.imshow(img, aspect='auto', cmap=cmap, vmin=0, vmax=1, origin='upper', extent=[Ss[0] - 2.5, Ss[-1] + 2.5, zs[-1] + 5, zs[0] - 5], interpolation='nearest')
    ax.set_title('x = %g' % x, fontsize=9); ax.set_xlabel('Laki speed', fontsize=8); ax.set_ylabel('z', fontsize=8); ax.tick_params(labelsize=7)
    ax.grid(alpha=.3)
for ax in list(axs.flat)[len(cx):]: ax.axis('off')
fig.suptitle('dgb_01: speed vs position. Each panel is one x column; green = that (z, speed) clips out, grey = stays inside, white = no floor', fontsize=11)
plt.tight_layout(rect=(0, 0, 1, 0.97)); plt.savefig(out2, dpi=85); print(out1, out2)
