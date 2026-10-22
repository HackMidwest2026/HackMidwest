"""Ruins Stones Skip, the RTA ending (exploration: the post-push spot is a RAM placement, everything after is inputs).
From RING (history full, Laki's target frozen at the push start), Laki is placed at LAKI and Mario at MARIO on the
-600 floor within the tether. Mario walks to S (jumping when blocked), stands, and Laki flies back to the frozen target
and returns. Pass 1 logs Laki's speed every frame; pass 2 replays and presses C-down on every frame where his speed is
>= MINSPD, then steers toward the isk_19 exit floor. Reports per frame: speed read by the mount, isk19 or not.
usage: isk11_return_brute.py RING OUT.json   env LAKI=x,y,z MARIO=x,z S=x,z MINSPD N"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
LK = [float(v) for v in os.environ.get('LAKI', '410,-548.8,445').split(',')]
M0 = [float(v) for v in os.environ.get('MARIO', '390,475').split(',')]
S = tuple(float(v) for v in os.environ.get('S', '367,545').split(','))
JF = [int(v) for v in os.environ.get('JUMPF', '-1,-1').split(',')]
MINSPD = float(os.environ.get('MINSPD', '40')); N = int(os.environ.get('N', '110'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/irb%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
def start():
    e.load(sys.argv[1]); a = laki()['addr']
    e.wf32(PLAYER + PS_POS, M0[0]); e.wf32(PLAYER + PS_POS + 4, -598); e.wf32(PLAYER + PS_POS + 8, M0[1])
    e.wf32(a + 0x38, LK[0]); e.wf32(a + 0x3C, LK[1]); e.wf32(a + 0x40, LK[2])
    for i in range(20): e.step(0, 0, 0, 2)
    return e.u32(STATE) >> 16
hist = []
def walk_frame(f, btn=0):
    q = player(e); dd = math.hypot(S[0] - q['x'], S[1] - q['z'])
    st = stick_for(math.degrees(math.atan2(S[1] - q['z'], S[0] - q['x'])) % 360, 80 if dd > 12 else 25) if dd > 2 else (0, 0)
    jump = JF[0] <= f < JF[1] or JF[0] < 0 and dd > 2 and len(hist) >= 3 and q['action'] in (1, 2) and math.hypot(hist[-3][0] - q['x'], hist[-3][1] - q['z']) < 1.0
    e.step(btn | (A if jump else 0), st[0], st[1], 2)
st0 = start(); log = []
for f in range(N):
    walk_frame(f); q = player(e); hist.append((q['x'], q['z'])); L = laki()
    log.append({'f': f, 'fs': e.u32(STATE) >> 16, 'spd': round(L['speed'], 2), 'laki': [round(L['x'], 1), round(L['y'], 1), round(L['z'], 1)],
                'mario': [round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)], 'act': q['action']})
cands = [r['f'] for r in log if r['spd'] >= MINSPD]
fr = sorted(set(g for f in cands for g in (f - 1, f, f + 1) if 0 <= g < N))
res = []
for f in fr:
    start(); hist.clear()
    for i in range(f + 1):
        walk_frame(i, D_CBUTTON if i == f else 0); q = player(e); hist.append((q['x'], q['z']))
    pc = player(e); a = laki()['addr']; spd = None
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: spd = e.f32(a + 0x18); break
        e.step(0, 0, 0, 2)
    ok = False
    for i in range(150):
        q = player(e); st = stick_for(math.degrees(math.atan2(532 - q['z'], 220 - q['x'])) % 360, 80)
        e.step(0, st[0], st[1], 2)
        if where(e)[1] == 16: ok = True; break
    r = {'f': f, 'press_at': [round(pc['x'], 1), round(pc['y'], 1), round(pc['z'], 1)], 'act': pc['action'], 'speed_read': None if spd is None else round(spd, 2),
         'laki_spd_log': log[f]['spd'], 'isk19': ok}
    res.append(r); print(r, flush=True)
json.dump({'laki0': LK, 'mario0': M0, 'S': S, 'state0': st0, 'log': log, 'runs': res}, open(sys.argv[2], 'w'))
