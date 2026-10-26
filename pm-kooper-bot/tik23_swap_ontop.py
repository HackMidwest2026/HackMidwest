"""tik_23: ride Lakilester into the Super Hammer block (box x -305..-255, z -45..5, top y 30), then swap partners
while riding (C-right, A -> Goombario). Lakilester's PutAway hop snaps Mario onto any floor a downward ray from his
head finds; the rays are 14.4 units out at Lakilester's yaw and +-120 deg. Does Mario end up ON the block?
Inputs only after states/tik23_westzone.st (stick y + moves toward -z here).
usage: tik23_swap_ontop.py OUT.json"""
import os, sys, json
from emu import *
from pm import *
from nav import go_to
e = Emu('pm-jp.z64', '/dev/shm/pmbot/so%d' % os.getpid())
res = []
STARTS = {'north': (-280, 45), 'east': (-225, -20), 'south': (-280, -85)}
STICKS = {'north': [(sx, sy) for sx in (-60, -30, -15, 0, 15, 30, 60) for sy in (60, 80)],
          'east': [(sx, sy) for sx in (-80, -60) for sy in (-60, -40, -20, 0, 20, 40, 60)],
          'south': [(sx, sy) for sx in (-60, -30, -15, 0, 15, 30, 60) for sy in (-60, -80)]}
for face, start in STARTS.items():
    for (sx, sy) in STICKS[face]:
        for hold in (6, 10, 16, 24):
            e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
            go_to(e, *start, maxf=200, tol=2)
            for i in range(10): e.step(0, 0, 0, 2)
            e.step(D_CBUTTON, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
            for i in range(hold): e.step(0, sx, sy, 2)
            p = player(e); pre = [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)]
            e.step(R_CBUTTON, 0, 0, 2)
            for i in range(20): e.step(0, 0, 0, 2)
            e.step(0, 0, 80, 2)
            for i in range(6): e.step(0, 0, 0, 2)
            e.step(A, 0, 0, 2)
            mx = -99
            for i in range(70):
                e.step(0, 0, 0, 2); mx = max(mx, player(e)['y'])
            p = player(e)
            r = {'face': face, 'stick': [sx, sy], 'hold': hold, 'pre': pre, 'after': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), p['action']],
                 'maxy': round(mx, 1), 'partner': e.s8(PLAYER_DATA + 0x12)}
            res.append(r); print(r, flush=True)
            if p['y'] > 25: e.save('states/tik23_ontop_swap_%s_%d_%d_%d.st' % (face, sx, sy, hold)); e.step(0, 0, 0, 1)
json.dump(res, open(sys.argv[1], 'w'))
print('ON TOP:', [r for r in res if r['after'][1] > 25])
