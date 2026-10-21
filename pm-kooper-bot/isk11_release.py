"""Release scan after the isk_11 Laki push: from STATE (Laki idle far from his frozen follow target), Mario follows
PATH_PTS (down the steps toward the lowest level) and presses C-down on game frame f. Logs per f: where Mario was,
which floor height, Laki's moveSpeed when the mount reads it, the mount landing point (Laki moveToPos), Mario's lowest
y in the next 150 frames, where he ends and the map. After the mount Mario steers toward STEER (default the isk_19 exit floor, 225,540; 'none' to idle) and 'isk19' records
whether the isk_19 exit loaded. usage: isk11_release.py STATE F0 F1 OUT.json  env: PATH_PTS, STEER"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
st0, F0, F1, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
PATH = [tuple(float(a) for a in p.split(',')) for p in os.environ.get('PATH_PTS', '285,530;320,540;365,500').split(';')]
STEER = tuple(float(v) for v in os.environ.get('STEER', '225,540').split(',')) if os.environ.get('STEER', '225,540') != 'none' else None
e = Emu('pm-jp.z64', '/dev/shm/pmbot/irl%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
res = []
for f in range(F0, F1 + 1):
    e.load(st0); k = 0; trail = []
    for i in range(f):
        q = player(e)
        while k < len(PATH) - 1 and math.hypot(PATH[k][0] - q['x'], PATH[k][1] - q['z']) < 10: k += 1
        st = stick_for(math.degrees(math.atan2(PATH[k][1] - q['z'], PATH[k][0] - q['x'])) % 360, 80)
        e.step(0x400 if i == f - 1 else 0, st[0], st[1], 2)
    pc = player(e); a = laki()['addr']; S = None; mt = None
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: S = e.f32(a + 0x18); mt = (e.f32(a + 0x60), e.f32(a + 0x64), e.f32(a + 0x68)); break
        e.step(0, 0, 0, 2)
    low = 1e9; ok = False
    for i in range(150):
        q = player(e)
        st = stick_for(math.degrees(math.atan2(STEER[1] - q['z'], STEER[0] - q['x'])) % 360, 80) if STEER else (0, 0)
        e.step(0, st[0], st[1], 2); low = min(low, e.f32(PLAYER + PS_POS + 4))
        if where(e)[1] == 16: ok = True; break
    q = player(e)
    r = {'f': f, 'press_at': (round(pc['x'], 1), round(pc['y'], 1), round(pc['z'], 1)), 'act': pc['action'], 'speed': None if S is None else round(S, 1),
         'target': None if mt is None else [round(v, 1) for v in mt], 'low': round(low, 1), 'end': (round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)), 'map': where(e), 'isk19': ok}
    res.append(r); print(r, flush=True)
json.dump(res, open(OUT, 'w'))
