"""pra_18 south->north, pure-LEFT setup from the east wall:
  1. ride Lakilester diagonally into the east wall (stick right + a bit up/down) so he slides along it (x pins ~732.25),
     release somewhere with z 18..42 (wait w frames)
  2. hold full left for N frames (riding moves exactly 6/frame)
  3. C-down (get off) holding left, keep holding left
  4. C-down on frame K after the get-off press
DIAGNOSTIC SETUP ONLY: Mario's start (690, z0) placed in RAM (Clubba 3 parked = defeated); everything after is real input
and Laki's speed is never written. Reports, for each slide stick / release z / wait, which N and K clip."""
import os, sys, json
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ls%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/ls%d_0.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/ls%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for j in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    r = player(e); e.load(cur); return r['action'] == 33 and r['z'] < 0, sp
res = []
for start_z, slide, slide_frames in [(80, (60, 20), 30), (80, (60, 20), 36), (80, (60, 20), 42), (80, (80, 28), 30), (80, (80, 28), 38),
                                     (10, (40, -12), 30), (10, (40, -12), 40), (10, (60, -20), 34), (50, (40, 16), 30), (50, (40, 16), 40)]:
    for wait in (0, 5, 20):
        e.load(b0)
        e.wf32(PLAYER + PS_POS, 690.0); e.wf32(PLAYER + PS_POS + 8, float(start_z))   # DIAGNOSTIC start
        for i in range(20): e.step(0, 0, 0, 2)
        e.step(D_CBUTTON, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
        for i in range(slide_frames): e.step(0, *slide, 2)
        for i in range(wait): e.step(0, 0, 0, 2)
        pin = player(e)
        pinned = '/dev/shm/pmbot/ls%d_p.st' % os.getpid(); e.save(pinned)
        for N in (3, 4, 5):
            e.load(pinned)
            for i in range(N): e.step(0, -80, 0, 2)
            px = player(e)['x']
            e.step(D_CBUTTON, -80, 0, 2); ks = []
            for K in range(1, 41):
                e.step(0, -80, 0, 2); q = player(e)
                if K >= 28 and q['action'] in (0, 1, 2):
                    ok, sp = try_clip()
                    if ok: ks.append((K, round(sp, 2)))
            r = {'slide': slide, 'frames': slide_frames, 'wait': wait, 'pin': [round(pin['x'], 3), round(pin['z'], 2)], 'N': N, 'getoff_x': round(px, 2), 'clip_K': ks}
            res.append(r); print(r, flush=True)
json.dump(res, open('/tmp/claude-0/pm/p18/left_setup.json', 'w')); print('done')
