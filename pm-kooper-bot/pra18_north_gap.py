"""pra_18 north side: does an idle Lakilester left behind give the mount enough speed for the north->south clip?
DIAGNOSTIC SETUP: Mario+Laki placed at a start spot; Mario then walks (real stick) to a target in the clip zone, stops,
waits W frames, C-down. Logs Laki's speed on the C-down frame and whether Mario crosses."""
import os, sys, json, math
from emu import *
from pm import *
from nav import go_to
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ng%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/ng%d_b.st' % os.getpid(); e.save(b0)
res = []
for sx, sz in ((500, -18), (520, -40), (540, -70), (574, -80), (610, -60), (650, -40)):
    for tx in (566, 568, 570, 572, 574, 576):
        for tz in (-14, -17, -20, -23):
            e.load(b0)
            e.wf32(PLAYER + PS_POS, float(sx)); e.wf32(PLAYER + PS_POS + 8, float(sz))                 # DIAGNOSTIC
            L = laki(); e.wf32(L['addr'] + 0x38, sx - 20.0); e.wf32(L['addr'] + 0x40, float(sz))      # DIAGNOSTIC
            for i in range(30): e.step(0, 0, 0, 2)
            go_to(e, tx, tz, maxf=300, tol=1.0)
            mid = '/dev/shm/pmbot/ng%d_m.st' % os.getpid(); e.save(mid)
            for W in (0, 2, 5, 10, 20, 40):
                e.load(mid)
                for i in range(W): e.step(0, 0, 0, 2)
                p = player(e); L = laki(); gap = math.hypot(e.f32(L['addr'] + 0x38) - p['x'], e.f32(L['addr'] + 0x40) - p['z'])
                e.step(D_CBUTTON, 0, 0, 2); s = e.f32(laki()['addr'] + 0x18)
                for i in range(40): e.step(0, 0, 0, 2)
                q = player(e); ok = q['z'] > 0 and q['action'] == 33
                res.append([sx, sz, tx, tz, W, round(p['x'], 1), round(p['z'], 1), round(gap, 1), round(s, 2), ok])
                if ok or s > 30: print(res[-1], flush=True)
    print('start', sx, sz, 'max speed', max(r[8] for r in res if r[0] == sx), flush=True)
json.dump(res, open('/tmp/claude-0/pm/p18/north_gap.json', 'w')); print('done', sum(r[9] for r in res))
