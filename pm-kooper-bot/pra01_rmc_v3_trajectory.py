import math, json
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/trj')
AIR = (3, 4, 5, 6, 8, 15)
log = []
def step(b, sx, sy, tag):
    e.step(b, sx, sy, 2); p = player(e)
    log.append(dict(x=p['x'], y=p['y'], z=p['z'], a=p['action'], b=int(bool(b & A)), sx=sx, sy=sy, tag=tag, m=list(where(e)[:2])))
e.load('states/pra01_ub_e3.st'); e.step(0, 0, 0, 2)
for f in range(200):
    p = player(e); dx, dz = 535 - p['x'], -60 - p['z']; d = math.hypot(dx, dz)
    if d < 0.5: break
    mag = max(14, min(80, int(d * 10))); e.step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)), 2)
for f in range(60):
    if player(e)['x'] <= 510: break
    e.step(0, -80, 0, 2)
for i in range(8): e.step(0, 0, 0, 2)
S = '/dev/shm/pmbot/trj_a.st'; e.save(S); e.step(0, 0, 0, 2); e.load(S)
step(0, 0, 0, 'standing, facing left')
for f in range(45):
    step(A if (f < 5 or 10 <= f < 12) else 0, -40, 0, 'tornado jump 1 (LEFT 40)')
    if f > 3 and player(e)['action'] not in AIR: break
S = '/dev/shm/pmbot/trj_b.st'; e.save(S); e.step(0, 0, 0, 2); e.load(S)
step(0, 0, 0, 'landed on cliff (sliding)'); step(0, 0, 0, 'landed on cliff (sliding)')
for f in range(60):
    step(A if (f < 5 or 6 <= f < 8) else 0, 0, 0, 'jump + tornado jump 2 (neutral)')
    if f > 3 and player(e)['action'] not in AIR: break
S = '/dev/shm/pmbot/trj_c.st'; e.save(S); e.step(0, 0, 0, 2); e.load(S)
step(0, 0, 0, 'on the ledge (sliding)'); step(0, 0, 0, 'on the ledge (sliding)')
for f in range(45):
    if f < 8: s, t = (-56, -56), 'jump 3 + DOWN-LEFT'
    else: s, t = (0, -80), 'DOWN: over the cave wall'
    step(A if f < 8 else 0, *s, t)
    if player(e)['y'] < -120: break
json.dump(log, open('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/traj.json', 'w'))
print(len(log), 'frames; y range', min(l['y'] for l in log), max(l['y'] for l in log), 'actions', sorted(set(l['a'] for l in log)))
