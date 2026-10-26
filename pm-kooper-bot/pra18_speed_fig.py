"""Figure: pra_18 overview + zoom on the east pillar with the Lakilester speed needed to clip from each spot."""
import json, collections, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
d = json.load(open('pra18_collision.json')); P = '/tmp/claude-0/pm/p18/'
def load(f): return [r for r in json.load(open(P + f)) if r[3] == 'CROSS']
fn, fs, cs = load('fine_n.json'), load('fine_s.json'), load('map_s_560.json')
fig, (ax0, ax) = plt.subplots(2, 1, figsize=(13, 15), gridspec_kw={'height_ratios': [1, 2.1]}, constrained_layout=True)
def draw(a):
    for c in d['colliders']:
        for t in c['tris']:
            v = t['v']; n = t['n']
            if abs(n[1]) > 0.7:
                if max(p[1] for p in v) < 1: a.add_patch(Polygon([(p[0], p[2]) for p in v], color='#e3e8ef', zorder=0))
            else:
                xs = [p[0] for p in v]; zs = [p[2] for p in v]
                col = '#3a7bd5' if c['id'] == 19 else ('#d35400' if c['id'] in (39, 40, 41) else '#555')
                a.plot(xs + [xs[0]], zs + [zs[0]], color=col, lw=4 if c['id'] == 19 else 1.2, zorder=2)
draw(ax0)
for x, lab in ((268, 'Clubba 1'), (490, 'Clubba 2'), (717, 'Clubba 3')):
    ax0.add_patch(Circle((x, 70), 80, fill=False, ls='--', ec='green', alpha=.6)); ax0.plot(x, 70, 'g^', ms=9); ax0.text(x, 92, lab, ha='center', color='green', fontsize=9)
for cid, lab in ((41, 'statue 1'), (40, 'statue 2'), (39, 'statue 3')):
    vs = [p for t in d['colliders'][cid]['tris'] for p in t['v']]; x0 = min(p[0] for p in vs); x1 = max(p[0] for p in vs)
    ax0.add_patch(Rectangle((x0, -100), x1 - x0, 50, color='#d35400', alpha=.35)); ax0.text((x0 + x1) / 2, -108, lab, ha='center', fontsize=8, color='#a04000')
ax0.add_patch(Rectangle((540, -45), 110, 93, fill=False, ec='red', lw=2)); ax0.text(652, -38, 'zoom below', color='red', fontsize=9)
ax0.text(760, -75, 'door to\npra_33', fontsize=8)
ax0.set_xlim(-60, 810); ax0.set_ylim(160, -160); ax0.set_aspect('equal'); ax0.grid(alpha=.2)
ax0.set_title('pra_18 Bridge Mirror Hall (top view, north = up; mirror = blue line at z = 0)')
draw(ax); cmap = plt.get_cmap('viridis')
spotN = collections.defaultdict(list)
for x, z, S, _, ex, ez in fn: spotN[(x, z)].append(S)
sc = ax.scatter([k[0] for k in spotN], [k[1] for k in spotN], c=[min(v) for v in spotN.values()], cmap=cmap, vmin=20, vmax=60, s=70, marker='s', edgecolors='k', linewidths=.3, zorder=5)
for x in sorted({k[0] for k in spotN}):
    if x % 2: continue
    v = sorted({S for (xx, z), Ss in spotN.items() if xx == x for S in Ss})
    ax.text(x, -26.5, '%d' % v[0] if len(v) == 1 else '%d-%d' % (v[0], v[-1]), ha='center', fontsize=9, rotation=90, va='bottom')
ax.text(565, -36, 'speed needed at each x', ha='center', fontsize=9)
spotS = collections.defaultdict(list)
for x, z, S, _, ex, ez in fs: spotS[(x, z)].append(S)
ax.scatter([k[0] for k in spotS], [k[1] for k in spotS], c=[min(v) for v in spotS.values()], cmap=cmap, vmin=20, vmax=60, s=70, marker='o', edgecolors='k', linewidths=.3, zorder=5)
hiS = {(x, z) for x, z, S, _, ex, ez in cs if x <= 590}
ax.scatter([k[0] for k in hiS], [k[1] for k in hiS], marker='x', c='red', s=50, zorder=5, label='south side x 584-586: speeds 50-300 also cross')
ax.scatter([586] * 4, [-20, -25, -30, -40], marker='x', c='purple', s=50, zorder=5, label='north side x 586: only speed 300 (lands near Clubba 2)')
ft = json.load(open(P + 'foot_S.json'))
ax.scatter([r[0] + .4 for r in ft], [r[1] + .4 for r in ft], marker='v', s=60, c='white', edgecolors='red', linewidths=1.2, zorder=7, label='south side: STANDING C-down mount (speed 0) also clips north')
ax.plot(626, 13.5, marker='*', ms=20, color='gold', mec='k', zorder=6); ax.text(629, 9, 'north->south\nlanding (~625, 14)', fontsize=10, va='bottom')
ax.plot(625, -25.5, marker='*', ms=20, color='gold', mec='k', zorder=6); ax.text(629, -31, 'south->north\nlanding (~625, -25)', fontsize=10)
ax.text(543, -44, 'NORTH -> SOUTH (squares): speed ~= 616 - x,\nonly a 1-2 speed window per spot', fontsize=11, va='top')
ax.text(543, 46, 'SOUTH -> NORTH: x 612-616, z 16-39 hugging the pillar tip.\nNo speed needed: a standing C-down mount (triangles) clips;\nriding at speed 22-40 (circles) works too', fontsize=11, va='bottom')
ax.text(600, 1.8, 'east pillar', ha='center', fontsize=9)
ax.set_xlim(540, 650); ax.set_ylim(48, -48); ax.set_aspect('equal'); ax.grid(alpha=.3)
ax.set_xlabel('x'); ax.set_ylabel('z'); ax.legend(loc='lower right', fontsize=9)
cb = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.01); cb.set_label('lowest Lakilester speed (at C-down) that clips from this spot')
ax.set_title('Where Mario must stand and how fast Lakilester must be to clip through the mirror')
plt.savefig('/home/user/HackMidwest/pm-kooper-bot/figures/pra18_clip_speeds.png', dpi=90)
