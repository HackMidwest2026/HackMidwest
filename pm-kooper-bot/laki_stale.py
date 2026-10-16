"""pra_01: keep Lakilester idle while Mario's trail fills (stop-and-go into him), then run away; peak speed?"""
import os, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/stale')


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


res = []
for push_deg, g, s, n, away_deg in itertools.product((180, 90, 135, 225), (1, 2), (1, 2, 3), (40, 80, 160), (0, 90, 270, 315)):
    e.load('states/pra01_start.st')
    for i in range(20): e.step(0, 80, 0, 2)          # walk right; Lakilester trails on the left
    for i in range(10): e.step(0, 0, 0, 2)
    px, py = stick_for(push_deg, 40)
    for f in range(n):
        go = (f % (g + s)) < g
        e.step(0, px if go else 0, py if go else 0, 2)
    ax, ay = stick_for(away_deg, 80)
    best = (0, None)
    for f in range(40):
        e.step(0, ax, ay, 2)
        if tuple(where(e)[:2]) != (21, 0): break
        l, p = laki(), player(e)
        if l and l['speed'] > best[0]:
            best = (l['speed'], (f, round(p['x']), round(p['z']), round(l['x']), round(l['z'])))
    res.append((best[0], (push_deg, g, s, n, away_deg), best[1]))
res.sort(key=lambda r: -r[0])
for r in res[:12]: print('peak %.2f  push deg %d go %d stop %d frames %d, then run %d: %s' % ((r[0],) + r[1] + (r[2],)))
