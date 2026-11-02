"""Compare the page's detections and locks with the emulator truth. usage: sr_analyze.py DIR"""
import json, sys
sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from rngsim import adv
D = sys.argv[1]; SH = 700 * (0xFFFFFFFF // 1010); VFPS = 30000 / 1001
T = json.load(open(D + '/truth.json')); P = json.load(open(D + '/page.json')); tr = T['truth']
rooms = [x for x in T['events'] if 'room' in x]
def room_at(gf):
    r = None
    for x in rooms:
        if x['gf'] <= gf: r = x['room']
    return r
states = set(); true_sh = []
for gf, vf, prev, k, mp, md, vis in tr:
    s = prev
    for i in range(k): states.add(s); s = adv(s)
    if k == 2 and adv(prev) >= SH: true_sh.append((gf, vf))
visf = [x[6] for x in tr]
# a shine is "showable" if the bar is up at the draw and for the next 10 frames, and has been up for 30 frames before
def showable(gf): return all(visf[g] for g in range(max(0, gf - 30), min(len(visf), gf + 10)))
hist = P['hist']
best = None
for off in range(-5000, 5000, 5):   # page ms = video ms + off, video ms of a shine = vf / VFPS * 1000
    sc = 0
    vt = [vf / VFPS * 1000 + off for gf, vf in true_sh]
    j = 0
    for h in hist:
        while j < len(vt) and vt[j] < h - 400: j += 1
        if j < len(vt) and abs(vt[j] - h) < 400: sc += 1
    if best is None or sc > best[0]: best = (sc, off)
# refine: residual distribution
off0 = best[1] + P['t0']
pairs = []; used = set()
for h in hist:
    v = (h - P['t0'] - best[1])
    c = min(true_sh, key=lambda x: abs(x[1] / VFPS * 1000 - v))
    pairs.append((h, c, v - c[1] / VFPS * 1000))
import statistics
med = statistics.median(p[2] for p in pairs)
hits = [p for p in pairs if abs(p[2] - med) < 80]
false = [p for p in pairs if abs(p[2] - med) >= 80]
det_gf = set(p[1][0] for p in hits)
show = [g for g, v in true_sh if showable(g)]
missed = [g for g in show if g not in det_gf]
print('true shines', len(true_sh), '| showable (bar up, steady)', len(show), '| page detections', len(hist))
print('detected showable', len([g for g in show if g in det_gf]), '/', len(show), '| missed showable', len(missed), '| false detections', len(false))
print('missed by room:', {r: sum(1 for g in missed if room_at(g) == r) for r in sorted(set(room_at(g) for g in missed))})
print('false detections (page s, nearest true off ms, room):', [(round((p[0] - P['t0']) / 1000, 1), round(p[2] - med), room_at(p[1][0])) for p in false][:15])
print('detection timing spread (ms):', round(min(p[2] for p in hits) - med), round(max(p[2] for p in hits) - med))
# locks
v0 = (rooms[0]['vf'] / VFPS * 1000) + best[1]
for ev in P['slog']:
    if ev['ev'] in ('lock', 'unlock', 'chainSearch', 'wideCarry', 'chainSearchStopped'):
        vt = ev['t'] - P['t0'] - best[1]; gf = min(range(len(tr)), key=lambda i: abs(tr[i][1] / VFPS * 1000 - vt))
        extra = ''
        if ev['ev'] == 'lock': extra = 'TRUE' if ev['seed'] in states else 'FALSE LOCK'
        print('%6.1f s (game frame %5d, %s) %s %s %s' % (vt / 1000, gf, room_at(gf), ev['ev'], {k: v for k, v in ev.items() if k not in ('t', 'ev')}, extra))
# coin "visible" by the page but bar hidden in truth?
cb = [ev for ev in P['slog'] if ev['ev'] == 'coinBack']
print('coinBack events', len(cb), 'hidden ms:', [ev.get('hiddenMs') for ev in cb][:40])
