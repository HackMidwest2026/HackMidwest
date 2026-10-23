"""mac_01 OOB partner glitch. Exploration setup: Mario is teleported (RAM, once) onto the out-of-bounds grass ring at
START; everything after is inputs. Wait, then walk in world direction FALLYAW off the wall-less edge, fall into the
void, respawn at lastGoodPos; then STAY (idle) or WALK. Logs Mario and Laki every frame plus the history target height.
Flags snap frames (Laki within 3 units of Mario in 3D after being > 30 away the frame before).
usage: mac01_flicker.py OUT.json  env START=x,y,z WAIT FALLYAW N AFTER(idle|walk) SAVEAT=frame SAVE=path"""
import json, math, os, sys
from emu import *
from pm import *
from nav import stick_world
STATE, IDX, PTR, HIST = 0x8010D188, 0x8010D178, 0x8010D17C, 0x8010CEF8
P = lambda k, d: [float(v) for v in os.environ.get(k, d).split(',')]
START = P('START', '-480,20,368'); WAIT = int(os.environ.get('WAIT', '180')); FY = float(os.environ.get('FALLYAW', '180'))
N = int(os.environ.get('N', '900')); AFTER = os.environ.get('AFTER', 'idle'); SAVEAT = int(os.environ.get('SAVEAT', '-1'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mfl%d' % os.getpid())
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/mac01_e0.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, START[0]); e.wf32(PLAYER + PS_POS + 4, START[1]); e.wf32(PLAYER + PS_POS + 8, START[2])
for i in range(WAIT): e.step(0, 0, 0, 2)
log = []; prev = None; respawn = None; fell = False
for f in range(N):
    p = player(e)
    if respawn is None: st = stick_world(e, FY)
    elif AFTER == 'walk': st = stick_world(e, 90 if (f // 60) % 2 == 0 else 270)
    else: st = (0, 0)
    e.step(0, st[0], st[1], 2); p, l = player(e), lk(); ptr = e.u32(PTR)
    if p['y'] < START[1] - 50: fell = True
    if fell and respawn is None and log and abs(p['y'] - log[-1]['M'][1]) > 500: respawn = f
    d3 = math.sqrt((p['x'] - l['x']) ** 2 + (p['y'] - l['y']) ** 2 + (p['z'] - l['z']) ** 2)
    r = {'f': f, 'M': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)], 'L': [round(l['x'], 1), round(l['y'], 1), round(l['z'], 1)],
         'ls': round(l['speed'], 2), 'st': e.u32(STATE) >> 16, 'd3': round(d3, 1), 'tgtY': round(e.f32(HIST + 16 * ptr + 8), 0),
         'tgtXZ': [round(e.f32(HIST + 16 * ptr + 4), 0), round(e.f32(HIST + 16 * ptr + 12), 0)], 'full': e.u32(IDX) == (ptr - 1) % 40}
    r['snap'] = bool(prev and prev['d3'] > 30 and d3 < 4)
    log.append(r); prev = r
    if f == SAVEAT and os.environ.get('SAVE'): e.save(os.environ['SAVE'])
json.dump({'respawn': respawn, 'log': log}, open(sys.argv[1], 'w'))
print('respawn frame', respawn, 'snaps', sum(r['snap'] for r in log), 'frames with Laki within 4 of Mario after respawn',
      sum(1 for r in log if respawn and r['f'] > respawn and r['d3'] < 4))
