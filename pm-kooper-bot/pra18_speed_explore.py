"""pra_18: highest Lakilester mount speed reachable after a dismount, by random search. Ride (direction D, 8 frames),
dismount holding D, then 1-4 random segments (stick angle, magnitude, button Z/A/none on the first frame, A held or
not, 1-15 frames); on every frame try C-down and record the speed the mount reads (Laki's moveSpeed when Mario's
action becomes RIDE). Keeps the best sequences. DIAGNOSTIC SETUP as pra18_remount.py (placement + a 40-frame ride,
which resets Laki's follow history). usage: pra18_speed_explore.py SEED EPISODES OUT.jsonl"""
import os, sys, json, math, random
from emu import *
from pm import *
seed, EP, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/se%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC: keep Clubba 3 asleep
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 600.0); e.wf32(PLAYER + PS_POS + 8, -60.0)                     # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 580.0); e.wf32(L['addr'] + 0x40, -60.0)          # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/se%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/se%d_c.st' % os.getpid()
def mount_speed():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); v = None
    for i in range(12):
        if player(e)['action'] == 33: v = e.f32(laki()['addr'] + 0x18); break
        e.step(0, 0, 0, 2)
    p = player(e); e.load(cur); return v
fo = open(out, 'a'); best = 0
for ep in range(EP):
    D = rng.choice(range(0, 360, 45)); e.load(base)
    for i in range(8): e.step(0, *st(D, 80), 2)
    e.step(D_CBUTTON, *st(D, 80), 2)
    seq = []; top = (0, None)
    for k in range(rng.randint(1, 4)):
        a = rng.choice(range(0, 360, 15)); m = rng.choice((40, 80)); b = rng.choice((0, 0, Z, A)); hold = rng.random() < 0.5
        n = rng.randint(1, 15)
        for i in range(n):
            bb = b if i == 0 else (A if (b == A and hold) else 0)
            e.step(bb, *st(a, m), 2); seq.append((bb, a, m))
            v = mount_speed()
            if v is not None and v > top[0]:
                p = player(e); top = (v, len(seq), round(p['x'], 1), round(p['z'], 1))
    if top[0] > best * 0.9 and top[0] > 15:
        fo.write(json.dumps({'D': D, 'seq': seq[:top[1]], 'speed': top[0], 'at': top[2:]}) + '\n'); fo.flush()
    if top[0] > best: best = top[0]; print('best %.2f' % best, 'D', D, 'at', top[2:], 'len', top[1], flush=True)
    if ep % 100 == 0: print('ep', ep, 'best %.2f' % best, flush=True)
print('done', best)
