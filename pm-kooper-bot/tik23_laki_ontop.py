"""tik_23: get Mario ON TOP of the Super Hammer block (top y 30) with Lakilester. Ride into the block face at stick
angle ANG (degrees from straight-at-the-face) for N frames, then C-down to dismount. During the dismount hop the game
casts rays down from Mario's head (feet + 37) around him; if one is over the block it snaps Mario to y 30.
Inputs only after states/tik23_westzone.st (Mario + Lakilester in the block's area, enemies parked).
usage: tik23_laki_ontop.py OUT.json"""
import os, sys, json, math
from emu import *
from pm import *
from nav import go_to
CD = 0x0400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lt%d' % os.getpid())
res = []
# faces: east face (x=-255) approached from x>-255 pushing west; north face (z=5) pushing south; south face (z=-45) pushing north
FACES = {'east': ((-215, -20), (-80, 0), (0, 1)), 'north': ((-280, 45), (0, 80), (1, 0)), 'south': ((-280, -85), (0, -80), (1, 0))}
for face, (start, push, side) in FACES.items():
    for ang in (0, 20, 35, 50, 60, 70, 80):
        for sgn in (1, -1):
            if ang == 0 and sgn == -1: continue
            e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
            go_to(e, *start, maxf=200, tol=2)
            for i in range(10): e.step(0, 0, 0, 2)
            e.step(CD, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
            a = math.radians(ang) * sgn
            px, py = push; sx, sy = side
            mag = 80
            sx_ = int(round((px / 80 * math.cos(a) + sx * math.sin(a)) * mag))
            sy_ = int(round((py / 80 * math.cos(a) + sy * math.sin(a)) * mag))
            for i in range(45): e.step(0, sx_, sy_, 2)
            p = player(e)
            pre = (round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), p['action'])
            e.step(CD, sx_, sy_, 2)
            ys = []
            for i in range(30): e.step(0, 0, 0, 2); ys.append(round(player(e)['y'], 1))
            p = player(e)
            r = {'face': face, 'ang': ang * sgn, 'stick': [sx_, sy_], 'before': pre, 'after': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), p['action']], 'maxy': max(ys)}
            res.append(r); print(r, flush=True)
            if p['y'] > 25: e.save('states/tik23_ontop_%s_%d.st' % (face, ang * sgn)); e.step(0, 0, 0, 1)
json.dump(res, open(sys.argv[1], 'w'))
