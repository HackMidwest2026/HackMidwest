"""pra_01: Mario runs right (Lakilester trails on his left), then walks LEFT into Lakilester in stop-and-go cycles
(go g frames, stop s frames), pushing him. Prints the peak Lakilester speed for each (g, s) and where it happened."""
import os, sys, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/stopgo')


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


def trial(g, s, run_right, mag, total=200, zstart=None):
    e.load('states/pra01_start.st')
    if zstart is not None:
        for i in range(12): e.step(0, 0, -80 if zstart > 105 else 80, 2)
    for i in range(run_right): e.step(0, 80, 0, 2)
    best, trace = (0, None), []
    for f in range(total):
        go = (f % (g + s)) < g
        e.step(0, -mag if go else 0, 0, 2)
        if e.s16(GAME_MODE) != GM_WORLD or tuple(where(e)[:2]) != (21, 0):
            break
        p, l = player(e), laki()
        trace.append((f, go, round(p['x'], 1), round(p['z'], 1), round(l['x'], 1), round(l['z'], 1), round(l['speed'], 2)))
        if l['speed'] > best[0]:
            best = (l['speed'], f, round(p['x'], 1), round(p['z'], 1), round(l['x'], 1), round(l['z'], 1))
    return best, trace


if __name__ == '__main__':
    res = []
    for g, s, rr, mag in itertools.product((1, 2, 3, 5, 8, 12), (1, 2, 3, 5, 8), (60, 90), (80, 40, 20)):
        best, _ = trial(g, s, rr, mag)
        res.append((best[0], (g, s, rr, mag), best))
    res.sort(key=lambda r: -r[0])
    for r in res[:15]:
        print('go %d stop %d (after running right %d, stick %d): peak speed %.2f at frame %s, mario (%s, %s), laki (%s, %s)' % (r[1] + (r[0],) + r[2][1:]))
