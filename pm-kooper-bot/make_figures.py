"""Shareable result figures for the nok_14 (Kooper skip) searches."""
import json, math, pickle, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import LogNorm, LinearSegmentedColormap
from matplotlib.lines import Line2D

RUNS = '/tmp/claude-0/pm/runs'
OUT = '/tmp/claude-0/pm/figures'

# reference palette: sequential blue ramp, orange for the exits, ink tokens for text
BLUES = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
SEQ = LinearSegmentedColormap.from_list('seq_blue', BLUES)
SURFACE = '#fcfcfb'
FLOOR = '#e9e8e4'
FLOOR_OOB = '#f3f2ef'
WALL = '#52514e'
INK = '#0b0b0b'
INK2 = '#52514e'
INK3 = '#8a8984'
EXIT = '#eb6834'
EXIT_FILL = '#fbe0d4'
MARK = '#2a78d6'

COLL = json.load(open('/tmp/claude-0/pm/bot/nok14_collision.json'))
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': INK3,
                     'axes.labelcolor': INK2, 'xtick.color': INK3, 'ytick.color': INK3})


def draw_room(ax, xlim=(-1000, 600), wall_label=(-60, 105)):
    for c in COLL['colliders']:
        ignored = c['flags'] & 0x10000
        for t in c['tris']:
            xz = [(v[0], v[2]) for v in t['v']]
            if t['n'][1] > 0.5:
                if c['id'] in (5, 21):
                    fc, ec = EXIT_FILL, EXIT
                else:
                    fc, ec = FLOOR, FLOOR
                ax.add_patch(Polygon(xz, closed=True, fc=fc, ec=ec, lw=0.4, zorder=1))
            elif not ignored:
                ax.plot([p[0] for p in xz + xz[:1]], [p[1] for p in xz + xz[:1]], color=WALL, lw=0.9,
                        solid_capstyle='round', zorder=4)
    ax.plot([-100, -100], [-100, -20], color=WALL, lw=2.2, zorder=5)
    ax.annotate('bridge wall\n(x = −100)', xy=(-100, -60), xytext=wall_label, fontsize=9, color=INK2,
                ha='left', arrowprops=dict(arrowstyle='-', color=INK3, lw=0.8), zorder=6)
    ax.text(-920, -112, 'exit to nok_13', color=EXIT, fontsize=9, ha='center', zorder=6)
    ax.text(500, -112, 'exit to nok_15\n(goal)', color=EXIT, fontsize=9, ha='center', zorder=6)
    ax.text(0, -60, 'floor across\nthe gap', color=INK3, fontsize=8, ha='center', va='center', zorder=6)
    ax.set_xlim(*xlim)
    ax.set_ylim(140, -260)       # game camera looks toward -z: back of the room at the top
    ax.set_aspect('equal')
    ax.set_facecolor(SURFACE)
    ax.set_xlabel('x (game units)')
    ax.set_ylabel('z (game units)')
    for s in ax.spines.values():
        s.set_visible(False)


def header(fig, title, subtitle, stats):
    fig.text(0.04, 0.95, title, fontsize=16, fontweight='bold', color=INK, va='top')
    fig.text(0.04, 0.895, subtitle, fontsize=10.5, color=INK2, va='top')
    x = 0.04
    for big, small in stats:
        fig.text(x, 0.82, big, fontsize=18, fontweight='bold', color=INK, va='top')
        fig.text(x, 0.765, small, fontsize=9, color=INK2, va='top')
        x += 0.17


def heat(ax, fig, xs, zs, weights, label, gridsize):
    hb = ax.hexbin(xs, zs, C=weights, reduce_C_function=sum, gridsize=gridsize, cmap=SEQ,
                   norm=LogNorm(vmin=1), mincnt=1, linewidths=0.2, edgecolors=SURFACE, zorder=3,
                   extent=(-1000, 600, -260, 140))
    cb = fig.colorbar(hb, ax=ax, fraction=0.018, pad=0.01)
    cb.set_label(label, color=INK2)
    cb.outline.set_visible(False)
    from matplotlib.ticker import FuncFormatter
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: '%g' % v))
    return hb


def new_fig():
    fig = plt.figure(figsize=(16, 8.2), facecolor=SURFACE)
    ax = fig.add_axes([0.05, 0.11, 0.9, 0.6])
    return fig, ax


def fig_lzs():
    A = pickle.load(open(RUNS + '/r1/archive.pkl', 'rb'))
    cells = list(A['cells'].values())
    fig, ax = new_fig()
    draw_room(ax)
    heat(ax, fig, [c['pos']['x'] for c in cells], [c['pos']['z'] for c in cells],
         [max(1, c['chosen']) for c in cells], 'jumps started from this area', 70)
    header(fig, 'Test 1 — LZS route search (loading zone storage jumps)',
           'Chained frame-perfect LZS jumps from the left exit, exploring where Mario can land with the exit still stored. '
           'Goal: reach the right exit.',
           [('33,654', 'jumps tried'), ('1,293', 'distinct landing spots'), ('0', 'routes to the goal')])
    fig.text(0.04, 0.018, 'Mario never got further out of bounds than ~7 units past the end of the left exit. '
             'Stopped when you asked for a clip without LZS.', fontsize=9, color=INK3)
    fig.savefig(OUT + '/1_lzs_search.png', dpi=110, facecolor=SURFACE)
    plt.close(fig)


def fig_clip(run, fname, title, subtitle, stats, footer, xlim=(-1000, 600), gridsize=70):
    A = pickle.load(open(RUNS + '/%s/archive.pkl' % run, 'rb'))
    cells = list(A['cells'].values())
    del A
    fig, ax = new_fig()
    draw_room(ax, xlim)
    heat(ax, fig, [c['pos']['x'] for c in cells], [c['pos']['z'] for c in cells],
         [max(1, c['chosen']) for c in cells], 'attempts started from this area', gridsize)
    header(fig, title, subtitle, stats)
    fig.text(0.04, 0.018, footer, fontsize=9, color=INK3)
    fig.savefig(OUT + '/' + fname, dpi=110, facecolor=SURFACE)
    plt.close(fig)


def fig_corner():
    r = json.load(open(RUNS + '/corner/results.json'))
    fig, ax = new_fig()
    draw_room(ax, (-300, 60), wall_label=(-60, -135))
    ax.set_ylim(80, -160)
    ok = [s for s in r['starts'] if s['hits'] == 0]
    bad = [s for s in r['starts'] if s['hits'] > 0]
    for corner in ((-100, -100), (-100, -20)):
        ax.add_patch(plt.Circle(corner, 6, fc='none', ec=INK, lw=1.4, zorder=7))
    ax.text(-93, -108, 'north corner', fontsize=9, color=INK, zorder=7)
    ax.text(-93, -12, 'south corner', fontsize=9, color=INK, zorder=7)
    sizes = [12 + s['tries'] / 400 for s in ok]
    ax.scatter([s['pos'][0] for s in ok], [s['pos'][2] for s in ok], s=sizes, c=MARK, alpha=0.85,
               edgecolors=SURFACE, linewidths=1.0, zorder=8)
    ax.scatter([s['pos'][0] for s in bad], [s['pos'][2] for s in bad], s=60, marker='x', c=INK2,
               linewidths=1.6, zorder=8)
    for s in bad:
        ax.annotate('start was already\nout of bounds', xy=(s['pos'][0], s['pos'][2]), xytext=(-290, 62),
                    fontsize=8.5, color=INK2, arrowprops=dict(arrowstyle='-', color=INK3, lw=0.7), zorder=9)
        break
    ax.legend(handles=[Line2D([], [], marker='o', ls='', color=MARK, ms=7, label='start position (in bounds), no clip'),
                       Line2D([], [], marker='x', ls='', color=INK2, ms=7, mew=1.6,
                              label='invalid start (outside the wall), excluded')],
              loc='lower right', frameon=False, fontsize=9, labelcolor=INK2)
    total = sum(s['tries'] for s in r['starts'])
    valid = sum(s['tries'] for s in ok)
    header(fig, 'Test 4 — Exhaustive corner sweep at the bridge wall',
           'From 80 start positions around both corners: every stick angle × 4 stick strengths × walk / spin / jump / hammer. '
           'Enemy contact disabled so battles can\'t cut attempts short.',
           [('%s' % format(valid, ','), 'attempts from in-bounds starts'), ('78', 'in-bounds start positions'),
            ('0', 'clips through the wall')])
    fig.text(0.04, 0.018, 'Dot size = attempts from that start. The 109 "hits" all came from the 2 starts that '
             'were placed on floor sticking out past the front wall; Mario walked off it and fell under the map.',
             fontsize=9, color=INK3)
    fig.savefig(OUT + '/4_corner_sweep.png', dpi=110, facecolor=SURFACE)
    plt.close(fig)


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['1', '2', '3', '4']
    if '1' in which:
        fig_lzs()
    if '2' in which:
        fig_clip('c1', '2_clip_search_whole_room.png', 'Test 2 — Clip search, whole room (no LZS)',
                 'Random short stick / jump / spin / hammer inputs, keeping every new spot Mario reaches. Every frame is checked '
                 'for Mario passing through a solid wall.',
                 [('38,133', 'attempts'), ('10,566', 'distinct spots reached'), ('0', 'clips')],
                 'Restarted as Test 3 to concentrate on the walls nearest the bridge.')
    if '3' in which:
        fig_clip('c2', '3_clip_search_walls.png', 'Test 3 — Clip search focused on walls (no LZS)',
                 'Same search, restricted to spots within 40 units of a solid wall east of x = −480, '
                 'including the whole bridge wall.',
                 [('162,133', 'attempts'), ('4,888', 'spots next to walls'), ('0', 'clips')],
                 'Mario never gets closer than ~13 units to the bridge wall: the game pushes him back to his collision radius.',
                 xlim=(-520, 600), gridsize=90)
    if '4' in which:
        fig_corner()
