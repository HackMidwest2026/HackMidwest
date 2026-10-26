"""tik_23: dismount Lakilester at every phase of his 18-frame bob (Mario rides at laki.y + 10 + |bounce| * 0.34, up to
+3.06 higher at the peak), from riding spots next to the stone block, with the plain C-down dismount and with a
partner swap (put-away). Logs Mario's ride y at the press, the hop apex and where he ends (on the block = y ~30).
Inputs only after states/tik23_westzone.st. usage: tik23_bounce_phase.py OUT.json"""
import os, sys, json
from emu import *
from pm import *
from nav import go_to
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bp%d' % os.getpid())
SPOTS = {'north_angle': ((-280, 45), (-60, 60), 10), 'east_press': ((-225, -20), (-80, 0), 20), 'east_corner': ((-225, -20), (-60, -60), 6)}
res = []
for name, (start, stick, hold) in SPOTS.items():
    e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
    go_to(e, *start, maxf=200, tol=2)
    for i in range(10): e.step(0, 0, 0, 2)
    e.step(D_CBUTTON, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    for i in range(hold): e.step(0, stick[0], stick[1], 2)
    base = '/dev/shm/pmbot/bp%d_%s.st' % (os.getpid(), name); e.save(base); e.step(0, 0, 0, 1)
    for mode in ('cdown', 'swap'):
        for ph in range(20):
            e.load(base); e.step(0, 0, 0, 2)
            for i in range(ph): e.step(0, 0, 0, 2)
            p = player(e); y0 = p['y']; pos0 = (round(p['x'], 1), round(p['z'], 1))
            if mode == 'cdown':
                e.step(D_CBUTTON, 0, 0, 2)
            else:
                e.step(R_CBUTTON, 0, 0, 2)
                for i in range(20): e.step(0, 0, 0, 2)
                e.step(0, 0, 80, 2)
                for i in range(6): e.step(0, 0, 0, 2)
                e.step(A, 0, 0, 2)
            mx = -99
            for i in range(70): e.step(0, 0, 0, 2); mx = max(mx, player(e)['y'])
            q = player(e)
            r = {'spot': name, 'mode': mode, 'phase': ph, 'ride_y': round(y0, 2), 'pos': pos0, 'apex': round(mx, 2), 'end': [round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action']]}
            res.append(r); print(r, flush=True)
            if q['y'] > 25: e.save('states/tik23_ON_BLOCK_%s_%s_%d.st' % (name, mode, ph)); e.step(0, 0, 0, 1)
json.dump(res, open(sys.argv[1], 'w'))
