"""kpa_62: can the remount clip be done straight from the reliable corner spots (no exact walk)? For each spot: settle,
mount, ride 40, B, hold cardinal D (or nothing), C-down on frame T (20..50); also a direct C-down from the spot with the
stick held. Spots: UP corner, UP corner + RIGHT, + LEFT 12 (left pin), and the tower corner from the ledge spin-jump.
usage: kpa62_corner_clip.py STATE"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80), 'none': (0, 0)}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcc%d' % os.getpid())
tmp = '/dev/shm/pmbot/kcc%d' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
def hold(d, k, rel=20):
    for i in range(k): e.step(0, *CARD[d], 2)
    for i in range(rel): e.step(0, 0, 0, 2)
spots = {}
e.load(tmp + '.st0'); place(e, -480.0, -100.0); hold('up', 120); e.save(tmp + '.U'); spots['UP corner'] = tmp + '.U'
hold('right', 30); e.save(tmp + '.UR'); spots['UP corner + RIGHT'] = tmp + '.UR'
hold('left', 12); e.save(tmp + '.URL'); spots['+ LEFT 12 (left pin)'] = tmp + '.URL'
e.load(tmp + '.st0'); place(e, -505.0, -20.0, y=35.0); hold('right', 150, 30)
e.step(0x20, *CARD['down'], 2)
for f in range(50): e.step(0x80 if f < 8 else 0, *CARD['right'], 2)
for i in range(15): e.step(0, 0, 0, 2)
e.save(tmp + '.TC'); spots['tower corner (spin-jump)'] = tmp + '.TC'
for name, f in spots.items():
    e.load(f); p = player(e); hits = []
    for i in range(40): e.step(0, 0, 0, 2)
    e.save(tmp + '.s')
    for D in CARD:                                    # direct mount from the spot, holding D
        e.load(tmp + '.s'); e.step(0x400, *CARD[D], 2)
        for k in range(40):
            e.step(0, *CARD[D], 2); q = player(e)
            if k > 18 and inside_tower(q['x'], q['z']): hits.append('direct mount holding %s' % D); break
    e.load(tmp + '.s'); e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2); e.save(tmp + '.b')
    for D in CARD:
        e.load(tmp + '.b'); win = []
        for fr in range(1, 51):
            if fr >= 20:
                e.save(tmp + '.h'); e.step(0x400, *CARD[D], 2)
                for k in range(30):
                    e.step(0, *CARD[D], 2); q = player(e)
                    if k > 18 and inside_tower(q['x'], q['z']): win.append(fr); break
                e.load(tmp + '.h')
            e.step(0, *CARD[D], 2)
        if win: hits.append('B, hold %s, C-down on frames %s' % (D, win))
    print('%-26s (%.1f, %.1f): %s' % (name, p['x'], p['z'], hits or 'no clip'), flush=True)
