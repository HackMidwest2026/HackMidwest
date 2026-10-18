"""pra_02 back side ending evaluator: from a push-end state (Laki idle far from his stale target at the far left),
Mario holds dir1 for n1 frames then dir2 to the end (cardinal only; dir1 may be 'N' = stand); C-down is tried on every
frame up to F; a clip = Mario on the front side (z > 1) 40 frames later. Prints the best speed and every clip.
usage: pra02_end_eval.py STATE [F=90]"""
import os, sys, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x400
SD = {'R': stick_for(0, 80), 'L': stick_for(180, 80), 'U': stick_for(270, 80), 'D': stick_for(90, 80), 'N': (0, 0)}
st0 = sys.argv[1]; F = int(sys.argv[2]) if len(sys.argv) > 2 else 90
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p2e%d' % os.getpid())
w = '/dev/shm/pmbot/p2e%d' % os.getpid()
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
best = (0,)
clips = []
for d1, n1, d2 in itertools.product('RDUN', (0, 4, 8, 12, 16, 24, 32), 'RDU'):
    if n1 == 0 and d1 != 'R': continue
    e.load(st0); e.step(0, 0, 0, 2)
    for f in range(F):
        s = SD[d1] if f < n1 else SD[d2]
        e.save(w + '/s.st')
        e.step(CD, *s, 2); spd = laki()['speed']; p = player(e)
        if spd > best[0]: best = (round(spd, 1), d1, n1, d2, f, round(p['x'], 1), round(p['z'], 1))
        if spd > 150:
            for i in range(40): e.step(0, 0, 0, 2)
            if player(e)['z'] > 1: clips.append((d1, n1, d2, f, round(spd, 1), round(p['x'], 1), round(p['z'], 1)))
        e.load(w + '/s.st'); e.step(0, *s, 2)
print('best speed', best)
print('clips', len(clips)); [print(' ', c) for c in clips[:30]]
