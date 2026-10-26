"""Brute force the pra_18 mirror clips, v2. DIAGNOSTIC SETUP: Mario placed at START; LAKI=x,z optionally places
Lakilester. Episode = random 'speed building' phase (random stick segments, stops, Z spins; R steps) then Mario is
steered straight at a random target inside the clip zone; on every step inside the zone the state is saved and C-down
is tried (that step and 1-3 steps later). Success = riding on the other side of the mirror.
usage: pra18_brute2.py MODE SEED EPISODES OUT.jsonl"""
import os, sys, json, random, math
from emu import *
from pm import *
from nav import stick_world, world_yaw_to
mode, seed, EP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/b2%d' % os.getpid())
if mode == 'N':
    START = (560, -80); ZONE = (552, 578, -24, -11); crossed = lambda p: p['z'] > 0
else:
    START = tuple(int(v) for v in os.environ.get('START', '660,60').split(',')); ZONE = (610, 618, 13, 41); crossed = lambda p: p['z'] < 0
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, float(START[0])); e.wf32(PLAYER + PS_POS + 8, float(START[1]))     # DIAGNOSTIC
lx, lz = (float(v) for v in os.environ.get('LAKI', '%d,%d' % (START[0] - 40, START[1])).split(','))
l = laki(); e.wf32(l['addr'] + 0x38, lx); e.wf32(l['addr'] + 0x40, lz)                       # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/b2%d_base.st' % os.getpid(); e.save(base)
cand = '/dev/shm/pmbot/b2%d_cand.st' % os.getpid()
fo = open(out, 'a'); st = {'tries': 0, 'succ': 0, 'maxspeed_zone': 0.0}
inzone = lambda p: ZONE[0] <= p['x'] <= ZONE[1] and ZONE[2] <= p['z'] <= ZONE[3]
for ep in range(EP):
    e.load(base); inputs = []
    R = rng.randint(0, 90)
    while len(inputs) < R:
        if rng.random() < 0.2: b, sx, sy, d = 0, 0, 0, rng.randint(1, 8)
        else:
            a = rng.uniform(0, 2 * math.pi); m = rng.choice((30, 55, 80))
            b, sx, sy, d = (Z if rng.random() < 0.1 else 0), int(m * math.cos(a)), int(m * math.sin(a)), rng.randint(1, 10)
        for k in range(d):
            e.step(b if k == 0 else 0, sx, sy, 2); inputs.append((b if k == 0 else 0, sx, sy))
    tx, tz = rng.uniform(ZONE[0], ZONE[1]), rng.uniform(ZONE[2], ZONE[3])
    mag = rng.choice((30, 55, 80))
    done = False
    for k in range(120):
        p = player(e)
        if inzone(p):
            l = laki(); s = e.f32(l['addr'] + 0x18) if l else 0
            st['maxspeed_zone'] = max(st['maxspeed_zone'], s)
            e.save(cand)
            for extra in (0, 1, 2, 3):
                e.load(cand)
                for j in range(extra): e.step(0, 0, 0, 2)
                e.step(D_CBUTTON, 0, 0, 2)
                for i in range(35): e.step(0, 0, 0, 2)
                q = player(e); st['tries'] += 1
                if crossed(q) and q['action'] == 33:
                    st['succ'] += 1
                    rec = {'mode': mode, 'seed': seed, 'ep': ep, 'mario': [round(p['x'], 2), round(p['z'], 2)], 'laki_speed': round(s, 2),
                           'extra_wait': extra, 'end': [round(q['x'], 1), round(q['z'], 1)], 'inputs': inputs[:]}
                    fo.write(json.dumps(rec) + '\n'); fo.flush()
                    print('SUCCESS', rec['mode'], 'ep', ep, 'mario', rec['mario'], 'speed', rec['laki_speed'], 'wait', extra, '->', rec['end'], flush=True)
                    done = True; break
            e.load(cand)
            if done: break
        sx, sy = stick_world(e, world_yaw_to(p, tx, tz), mag) if math.hypot(p['x'] - tx, p['z'] - tz) > 1.5 else (0, 0)
        e.step(0, sx, sy, 2); inputs.append((0, sx, sy))
        if math.hypot(p['x'] - tx, p['z'] - tz) <= 1.5 and k > 5 and not inzone(p): break
    if ep % 25 == 0: print('ep', ep, st, flush=True)
print('final', st, flush=True)
