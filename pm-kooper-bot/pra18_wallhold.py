"""pra_18 north side: ride Lakilester, hold a down-right stick direction into the mirror/east-pillar corner.
Logs where Mario ends up and Lakilester's speed, then at each hold frame tries C-down (dismount) and dismount+remount.
DIAGNOSTIC SETUP ONLY: Mario placed at START on foot; everything after is real inputs."""
import os, sys, json, math
from emu import *
from pm import *
sx0, sz0 = (float(v) for v in os.environ.get('START', '560,-30').split(','))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/wh%d' % os.getpid())
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, sx0); e.wf32(PLAYER + PS_POS + 8, sz0)          # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
assert player(e)['action'] == 33, player(e)['action']
base = '/dev/shm/pmbot/wh%d_base.st' % os.getpid(); e.save(base)
tmp = '/dev/shm/pmbot/wh%d_t.st' % os.getpid()
out = []
for deg in range(0, 91, 10):          # 0 = pure right, 90 = pure down
    for mag in (40, 80):
        sx, sy = int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg))))
        e.load(base); track = []
        for f in range(90):
            e.step(0, sx, sy, 2); p = player(e); L = laki()
            track.append((round(p['x'], 2), round(p['z'], 2), round(e.f32(L['addr'] + 0x18), 2)))
            if f % 3 == 2 and f >= 20:
                e.save(tmp)
                for hold in (0, 1):
                    for rw in (None, 0, 2, 5, 10, 20):   # None = dismount only; else remount after rw frames on foot
                        e.load(tmp)
                        e.step(D_CBUTTON, sx * hold, sy * hold, 2)
                        for i in range(30): e.step(0, sx * hold, sy * hold, 2)
                        q = player(e)
                        res = {'deg': deg, 'mag': mag, 'f': f, 'hold': hold, 'rw': rw, 'dis': (round(q['x'], 1), round(q['z'], 1), q['action'])}
                        if rw is not None:
                            for i in range(rw): e.step(0, 0, 0, 2)
                            L = laki(); res['laki_speed'] = round(e.f32(L['addr'] + 0x18), 2)
                            e.step(D_CBUTTON, 0, 0, 2)
                            for i in range(40): e.step(0, 0, 0, 2)
                            q = player(e); res['mount'] = (round(q['x'], 1), round(q['z'], 1), q['action'])
                        if q['z'] > 0: print('CROSS', res, flush=True); out.append(res)
                e.load(tmp)
        xs = [t[0] for t in track]; zs = [t[1] for t in track]
        print('deg %2d mag %d  end (%.2f, %.2f)  max x %.2f  max z %.2f  laki speeds %s' % (deg, mag, xs[-1], zs[-1], max(xs), max(zs), sorted({t[2] for t in track})), flush=True)
json.dump(out, open('/tmp/claude-0/pm/p18/wallhold_%d_%d.json' % (sx0, sz0), 'w'))
print('done', len(out))
