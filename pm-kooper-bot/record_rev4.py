"""v4 (record_rev4.py): top step, wait 73 (the search stepped one extra neutral frame after its saved state), run down at stick angle 100 for 35 frames to the mirror, C-down (speed 107).
v3 (record_rev3.py): ends with the top-step version (jump down D 80, A at frame 4, 12 frames, stand, C-down on
frame 119, mount speed 89) and saves EVERY frame in the range [A, B) given by env (for chunked rendering).
Old header: record the best attempt of the full legend route (no video plugin; per-frame states for render_states.py):
pointer-2 start by the rock -> arc push into the lower floor's top-right corner (states/pra01_corner_seq.json) ->
1 frame right + jump onto the ledge -> stop-and-go right along the top wall to the palace wall (as
make_state_pra01_topright.py) -> running jump down onto the platform/stairs (rev_jumpdown2 best: D1 100, jump at 6,
14 frames; D2 165 for 20 frames) -> stand in the strip while Lakilester flies to his stale target and races back ->
C-down at run frame 126 (mount speed ~68; the crossing needs ~120)."""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x0400
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rrev2')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
log, k = [], 0
def step(b, sx, sy, tag):
    global k
    e.step(b, sx, sy, 2)
    p, l = player(e), laki(); ptr = e.u32(PTR)
    log.append({'i': k, 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'st': e.u32(STATE) >> 16, 'ptr': ptr,
                'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'lx': l['x'], 'lz': l['z'], 'act': p['action']})
    if int(os.environ.get('A', 0)) <= k < int(os.environ.get('B', 99999)):
        e.save(os.path.join(OUT, 's%04d.st' % k))
    k += 1
e.load('states/pra01_top_rock.st')
step(0, 0, 0, 'start: bottom of the mirror by the rock, Lakilester on the right (pointer 2)')
for item in json.load(open('states/pra01_corner_seq.json')):
    g, th, sl = item if len(item) == 3 else (*item, 2)
    p, l = player(e), laki()
    a, b = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
    for i in range(g): step(0, a, b, 'stop-and-go push aimed at Lakilester: the arc')
    for i in range(sl): step(0, 0, 0, 'stop-and-go push aimed at Lakilester: the arc')
step(0, 0, 0, 'corner of the lower floor')
rx, ry = stick_for(0, 80)
step(0, rx, ry, 'jump onto the ledge (right 1 frame, then A)')
for i in range(24):
    step(0x80 if i < 8 else 0, 0, 0, 'jump onto the ledge (right 1 frame, then A)')
    if i > 3 and player(e)['action'] in (0, 1, 2): break
for i in range(3): step(0, 0, 0, 'jump onto the ledge (right 1 frame, then A)')
for c in range(150):
    step(0, rx, ry, 'stop-and-go right along the top wall'); step(0, 0, 0, 'stop-and-go right along the top wall'); step(0, 0, 0, 'stop-and-go right along the top wall')
step(0, 0, 0, 'top-right corner: Lakilester 442 from his stale target')
s1 = stick_for(80, 80)
s2 = stick_for(100, 80)
seq = [(0x80 if 4 <= f < 12 else 0, *s1) for f in range(12)] + [(0, 0, 0)] * 73 + [(0, *s2)] * 36
for f in range(12 + 73 + 35):
    b, sx, sy = seq[f]
    step(b, sx, sy, 'running jump down onto the top step' if f < 12 else ('wait on the top step while Lakilester flies off' if f < 85 else 'run down to the mirror'))
step(CD, *s2, 'C-down next to the mirror (speed 107): Mario ends pressed on the mirror, no clip')
for i in range(45): step(0, 0, 0, 'mount: no clip')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('frames', k, 'end', {kk: log[-1][kk] for kk in ('x', 'y', 'z', 'act')})
m = max(log, key=lambda l: l['ls']); print('max laki speed', m['ls'], 'at', m['i'], m['tag'])
