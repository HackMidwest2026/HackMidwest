"""side-by-side explainer for the jan_04 log clip: in-game footage + top-down collision view + wall heights."""
import json, math, os, subprocess, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle, FancyArrowPatch

SRC = sys.argv[1]          # dir with g####.png + log.json from record_logclip.py
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(SRC, 'log.json')))
C = json.load(open('/tmp/claude-0/pm/bot/jan04_collision.json'))

SURF, INK, INK2, INK3 = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984'
WALL, LOW, MARIO, OOB = '#e34948', '#8a8984', '#2a78d6', '#fbe0d4'
R, H75 = 13.0, 37 * 0.75


def caption(l):
    i, tag = l['i'], l['tag']
    if tag == 'stand':
        return '1. Mario stands against the full-height part of the wall at x = -150.'
    if tag == 'spin':
        return '2. Spin into the wall: he slides north along it.'
    if tag == 'jump':
        return '3. Jump out of the spin: the spin heading carries him north-west.'
    if l['x'] > -150 and l['z'] < 30:
        return ('4. Center just north of z = 30: here the x = -150 wall is underground only,\n'
                '    so his wall rays (feet, feet+27.75) pass over it. He reaches the wall line.')
    if l['z'] < 40:
        return ('5. Landing on the log\'s sloped side shoves him +2.3 in z (no wall check).\n'
                '    His center is now behind the full-height wall, so push-out goes the wrong way: x = -163.')
    return '6. Pushed again by the z = 30 wall: z = 43. Mario is out of bounds behind both walls.'


def draw(idx):
    l = L[idx]
    fig = plt.figure(figsize=(7.2, 4.86), dpi=100, facecolor=SURF)
    ax = fig.add_axes([0.07, 0.25, 0.6, 0.68])
    # log floor (sloped) and other floors
    for c in C['colliders']:
        for t in c['tris']:
            if t['n'][1] > 0.5:
                xz = [(v[0], v[2]) for v in t['v']]
                if c['id'] == 26:
                    ax.add_patch(Polygon(xz, closed=True, fc='#cde2fb', ec='#9ec5f4', lw=0.4, zorder=1))
    ax.add_patch(Rectangle((-210, 30), 60, 50, fc=OOB, ec='none', zorder=0))
    ax.text(-200, 72, 'out of bounds', fontsize=7, color='#eb6834', zorder=2)
    ax.text(-198, 22, 'log (sloped floor)', fontsize=7, color='#184f95', zorder=2)
    # walls
    ax.plot([-150, -150], [-5, 30], color=LOW, lw=2, ls='--', zorder=3)
    ax.text(-148, 2, 'x=-150 wall:\nunderground only', fontsize=6.5, color=INK2, zorder=3)
    ax.plot([-150, -150], [30, 62], color=WALL, lw=3, zorder=3)
    ax.plot([-150, -62], [62, 150], color=WALL, lw=3, zorder=3)
    ax.plot([-210, -150], [30, 30], color=WALL, lw=3, zorder=3)
    ax.text(-148, 50, 'full-height', fontsize=6.5, color=WALL, zorder=3)
    ax.text(-208, 33, 'z=30 wall', fontsize=6.5, color=WALL, zorder=3)
    # slope push arrow on the crossing frame
    if l['tag'] == 'switch' and abs(l['x'] + 163) < 0.01:
        ax.add_patch(FancyArrowPatch((-152.94, 29.96), (-152.94, 32.26), arrowstyle='-|>', mutation_scale=8, color='#184f95', lw=1.5, zorder=6))
        ax.add_patch(FancyArrowPatch((-152.94, 32.26), (-163, 32.26), arrowstyle='-|>', mutation_scale=8, color=WALL, lw=1.5, zorder=6))
    # trail and mario
    xs = [p['x'] for p in L[:idx + 1]]; zs = [p['z'] for p in L[:idx + 1]]
    ax.plot(xs, zs, color=MARIO, lw=1, alpha=0.6, zorder=4)
    ax.add_patch(Circle((l['x'], l['z']), R, fc=MARIO, alpha=0.18, ec=MARIO, lw=1, zorder=5))
    ax.plot([l['x']], [l['z']], 'o', color=MARIO, ms=4, zorder=6)
    yaw = math.radians(l['yaw'])
    if l['tag'] != 'stand':
        ax.add_patch(FancyArrowPatch((l['x'], l['z']), (l['x'] + R * math.sin(yaw), l['z'] - R * math.cos(yaw)),
                                     arrowstyle='-|>', mutation_scale=7, color=INK, lw=1, zorder=6))
    ax.set_xlim(-210, -110); ax.set_ylim(80, 0)       # z grows toward the camera (down the screen)
    ax.set_aspect('equal'); ax.tick_params(labelsize=7)
    ax.set_xlabel('x', fontsize=8); ax.set_ylabel('z', fontsize=8)
    ax.set_title('top-down collision (circle = Mario, radius 13; arrow = heading)', fontsize=8, color=INK)
    # side view of the x = -150 wall at mario's z, and his ray heights
    bx = fig.add_axes([0.74, 0.25, 0.23, 0.68])
    full = l['z'] >= 30
    bx.add_patch(Rectangle((0, -120), 1, 220 if full else 120, fc=WALL if full else LOW, alpha=0.7))
    bx.axhline(0, color=INK3, lw=0.6)
    for h, name in ((l['y'], 'feet ray'), (l['y'] + H75, 'upper ray')):
        bx.plot([-0.4, 1.4], [h, h], color=MARIO, lw=1.5)
        bx.text(-0.4, h + 3, name, fontsize=6.5, color=MARIO)
    bx.set_xlim(-0.5, 1.5); bx.set_ylim(-30, 110); bx.set_xticks([])
    bx.tick_params(labelsize=7)
    bx.set_title('x=-150 wall at\nMario\'s z (%.2f)' % l['z'], fontsize=7.5, color=INK)
    bx.set_ylabel('height (y)', fontsize=7)
    fig.text(0.02, 0.02, caption(l), fontsize=8, color=INK, va='bottom')
    fig.text(0.07, 0.135, 'frame %d    x %.2f   y %.2f   z %.2f' % (l['i'], l['x'], l['y'], l['z']), fontsize=7.5, color=INK2, va='bottom')
    fig.savefig(os.path.join(OUT, 'd%04d.png' % idx), facecolor=SURF)
    plt.close(fig)


for i in range(len(L)):
    draw(i)
print('drew', len(L))
