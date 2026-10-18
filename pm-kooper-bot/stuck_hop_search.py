"""Random search for the natural early-Laki "stuck hop": from the flo_08 pre-load state, force exitTangent T and Mario
y Y through the load, steer Mario in the air (stick angle D for A frames, then neutral), and watch Laki for F frames.
Hit = Laki in follow state 2 (hop) with jumpScale == 0 and jumpVel == 0 for 30+ frames (the >1000-unit snap in
partner_flying_update_motion zeroes them without ending the hop). usage: stuck_hop_search.py PRE.st SEED0 N OUT.jsonl [F=400]"""
import json, math, os, random, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
pre, s0, n, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
F = int(sys.argv[5]) if len(sys.argv) > 5 else 400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/shs%d' % os.getpid())
fo = open(out, 'a')
def run(seed, log=False):
    rng = random.Random(seed)
    T, Y = rng.uniform(-8000, 8000), rng.choice((rng.uniform(-200, 900), 75.0))
    D, A = rng.uniform(0, 360), rng.randint(0, 80)
    e.load(pre)
    for i in range(400):
        e.wf32(e.u32(GAME_STATUS_PTR) + 0x94, T)
        if where(e)[0] != 19: e.wf32(PLAYER + PS_POS + 4, Y)
        e.step(0, 0, 0, 2)
        if where(e)[0] == 19 and e.s16(GAME_MODE) == GM_WORLD: break
    else: return None
    for i in range(2): e.wf32(PLAYER + PS_POS + 4, Y); e.step(0, 0, 0, 2)
    run_len = 0; first = None
    for f in range(F):
        e.step(0, *(stick_for(D, 80) if f < A else (0, 0)), 2)
        if where(e)[1] != 3: return None
        ls = [q for q in npcs(e) if q['id'] == -4]
        if not ls: return None
        a = ls[0]['addr']; st = e.u32(STATE) >> 16
        stuck = st == 2 and e.f32(a + 0x14) == 0 and e.f32(a + 0x1C) == 0
        run_len = run_len + 1 if stuck else 0
        if log and f % 10 == 0:
            p = player(e); l = ls[0]
            print(f, st, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), '|', round(l['x'], 1), round(l['y'], 1), round(l['z'], 1), 'spd %.2f js %.2f jv %.2f yaw %.0f mty %.0f' % (l['speed'], e.f32(a + 0x14), e.f32(a + 0x1C), e.f32(a + 0xC), e.f32(a + 0x64)))
        if run_len == 30 and first is None:
            p = player(e); l = ls[0]; first = f
            return {'seed': seed, 'T': T, 'Y': Y, 'D': D, 'A': A, 'frame': f, 'mario': [p['x'], p['y'], p['z']], 'laki': [l['x'], l['y'], l['z']],
                    'speed': l['speed'], 'yaw': e.f32(a + 0xC), 'mty': e.f32(a + 0x64)}
    return None
if os.environ.get('LOG'):
    run(s0, True); sys.exit()
for seed in range(s0, s0 + n):
    r = run(seed)
    if r: fo.write(json.dumps(r) + '\n'); fo.flush()
print('done', s0, n)
