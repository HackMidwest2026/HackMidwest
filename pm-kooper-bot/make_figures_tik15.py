"""Shareable result figures for tik_15 (Rip Cheato's room, bombable wall)."""
import json, pickle, sys, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from matplotlib.lines import Line2D
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter
from make_figures import SEQ, SURFACE, FLOOR, WALL, INK, INK2, INK3, EXIT, EXIT_FILL, MARK, header

RUNS = '/tmp/claude-0/pm/runs'
OUT = '/tmp/claude-0/pm/figures'
COLL = json.load(open('/tmp/claude-0/pm/bot/tik15_collision.json'))
BOMB = '#e34948'


def draw_room(ax):
    for c in COLL['colliders']:
        ignored = c['flags'] & 0x10000
        for t in c['tris']:
            xz = [(v[0], v[2]) for v in t['v']]
            if t['n'][1] > 0.5:
                fc = EXIT_FILL if c['id'] == 12 else FLOOR
                ec = EXIT if c['id'] == 12 else FLOOR
                ax.add_patch(Polygon(xz, closed=True, fc=fc, ec=ec, lw=0.4, zorder=1))
            elif t['n'][1] >= -0.5 and not ignored and c['id'] != 11:
                ax.plot([p[0] for p in xz + xz[:1]], [p[1] for p in xz + xz[:1]], color=WALL, lw=0.9, zorder=4)
    ax.plot([-250, -250], [-50, 50], color=BOMB, lw=3, solid_capstyle='butt', zorder=5)
    ax.text(-262, -60, 'bombable wall', color=BOMB, fontsize=9, ha='right', zorder=6)
    ax.text(-300, 70, 'exit to tik_14\n(goal)', color=EXIT, fontsize=9, ha='center', zorder=6)
    ax.add_patch(Circle((-80, 0), 12, fc='#eda100', ec=SURFACE, lw=1, zorder=6))
    ax.text(-80, 24, 'Rip Cheato', color=INK2, fontsize=9, ha='center', zorder=7, clip_on=True)
    ax.text(70, -40, 'pipe to\nToad Town', color=INK3, fontsize=8, ha='center', zorder=7, clip_on=True)
    ax.set_xlim(-370, 170)
    ax.set_ylim(165, -165)
    ax.set_aspect('equal')
    ax.set_facecolor(SURFACE)
    ax.set_xlabel('x (game units)')
    ax.set_ylabel('z (game units)')
    for s in ax.spines.values():
        s.set_visible(False)


def new_fig():
    fig = plt.figure(figsize=(13, 9), facecolor=SURFACE)
    ax = fig.add_axes([0.08, 0.1, 0.84, 0.6])
    return fig, ax


def fig_search():
    A = pickle.load(open(RUNS + '/tik_c1/archive.pkl', 'rb'))
    cells = list(A['cells'].values())
    tries, clips = A['tries'], len(A['clips'])
    del A
    fig, ax = new_fig()
    draw_room(ax)
    hb = ax.hexbin([c['pos']['x'] for c in cells], [c['pos']['z'] for c in cells],
                   C=[max(1, c['chosen']) for c in cells], reduce_C_function=sum, gridsize=55, cmap=SEQ,
                   norm=LogNorm(vmin=1), mincnt=1, linewidths=0.2, edgecolors=SURFACE, zorder=3,
                   extent=(-370, 170, -165, 165))
    cb = fig.colorbar(hb, ax=ax, fraction=0.025, pad=0.01)
    cb.set_label('attempts started from this area', color=INK2)
    cb.outline.set_visible(False)
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: '%g' % v))
    header(fig, 'Rip Cheato room — clip search (no Bombette)',
           'Random short stick / jump / spin / hammer inputs from spots next to walls, with Goombario. '
           'Every frame is checked for Mario passing through a wall.',
           [(format(tries, ','), 'attempts'), (format(len(cells), ','), 'spots next to walls'), (str(clips), 'clips')])
    fig.text(0.04, 0.018, 'The pipe back to Toad Town was taken %s times; that is normal and not counted.'
             % OTHER_EXITS, fontsize=9, color=INK3)
    fig.savefig(OUT + '/5_rip_cheato_clip_search.png', dpi=110, facecolor=SURFACE)
    plt.close(fig)


def fig_corner():
    r = json.load(open(RUNS + '/tik_corner/results.json'))
    fig, ax = new_fig()
    draw_room(ax)
    ax.set_xlim(-300, -120)
    ax.set_ylim(140, -140)
    starts = r['starts']
    ax.scatter([s['pos'][0] for s in starts], [s['pos'][2] for s in starts], s=[10 + s['tries'] / 300 for s in starts],
               c=MARK, alpha=0.85, edgecolors=SURFACE, linewidths=1.0, zorder=8)
    for p, name in (((-250, -50), 'seam'), ((-250, 50), 'seam'), ((-230, -50), 'ledge corner'), ((-230, 50), 'ledge corner')):
        ax.add_patch(Circle(p, 4, fc='none', ec=INK, lw=1.3, zorder=9))
    ax.text(-244, -58, 'seam', fontsize=8.5, color=INK, zorder=9)
    ax.text(-244, 64, 'seam', fontsize=8.5, color=INK, zorder=9)
    ax.text(-226, -60, 'ledge corner', fontsize=8.5, color=INK, zorder=9)
    ax.text(-226, 66, 'ledge corner', fontsize=8.5, color=INK, zorder=9)
    ax.text(-240, -110, 'low ledge', fontsize=8, color=INK3, ha='center', rotation=90, zorder=9)
    ax.text(-240, 110, 'low ledge', fontsize=8, color=INK3, ha='center', rotation=90, zorder=9)
    ax.legend(handles=[Line2D([], [], marker='o', ls='', color=MARK, ms=7, label='start position (dot size = attempts)')],
              loc='center left', bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9, labelcolor=INK2)
    total = sum(s['tries'] for s in starts)
    header(fig, 'Rip Cheato room — corner and seam sweep at the bombable wall',
           'Every stick angle × 3 stick strengths × walk / spin / jump / hammer, from %d start positions around the '
           'two seams and two ledge corners.' % len(starts),
           [(format(total, ','), 'attempts'), (str(len(starts)), 'start positions'), (str(len(r['hits'])), 'clips')])
    fig.text(0.04, 0.018, 'A hit would be: Mario past the bombable wall, on the exit floor, taking the exit to tik_14, '
             'or crossing any wall. 16 more run-up starts fell behind the bombable wall (on the exit floor) and were '
             'left out.', fontsize=9, color=INK3)
    fig.savefig(OUT + '/6_rip_cheato_corner_sweep.png', dpi=110, facecolor=SURFACE)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    OTHER_EXITS = sys.argv[1] if len(sys.argv) > 1 else '?'
    fig_corner()
    fig_search()
