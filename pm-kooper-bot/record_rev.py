"""(no video plugin: saves a savestate per frame; render_states.py screenshots them) render the closest reverse mirror clip attempt (pra_01 reflected side, the legend route):
from states/pra01_top_rock.st (history pointer 2), replay the stop-and-go push into the top-right corner
(states/pra01_corner_seq.json), run down (world angle 80), press C-down on the frame that gives the highest
Lakilester speed at the mount (chosen by a scan first). Logs Mario, Lakilester speed, follow state, pointer, target."""
import json, math, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x0400
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SEQ = json.load(open('states/pra01_corner_seq.json'))
RUN = 80
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rrev')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
# scan: C-down on run frame f, speed when the mount starts
sx, sy = stick_for(RUN, 80)
best = (-1, None, None)
for f in range(45):
    e.load('states/pra01_corner.st'); e.step(0, 0, 0, 2)
    for i in range(f): e.step(0, sx, sy, 2)
    e.step(CD, sx, sy, 2)
    spd = None
    for i in range(30):
        if spd is None and player(e)['action'] == 33: spd = laki()['speed']
        if spd is None: last = laki()['speed']
        e.step(0, 0, 0, 2)
        if spd is None and player(e)['action'] == 33: spd = last
    p = player(e)
    if spd is not None and spd > best[0]: best = (spd, f, (round(p['x'], 1), round(p['z'], 1)))
print('best C-down run frame', best[1], 'speed at mount %.1f' % best[0], 'end', best[2])
CDF = best[1]
log, k = [], 0
def step(b, sx, sy, tag, shoot=True):
    global k
    e.step(b, sx, sy, 2)
    if not shoot: return
    p, l = player(e), laki()
    ptr = e.u32(PTR)
    log.append({'i': k, 'tag': tag, 'x': p['x'], 'z': p['z'], 'ls': l['speed'], 'st': e.u32(STATE) >> 16, 'ptr': ptr,
                'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'lx': l['x'], 'lz': l['z'], 'act': p['action']})
    e.save(os.path.join(OUT, 's%04d.st' % k))   # rendered later by render_states.py (video changes lag)
    k += 1
e.load('states/pra01_top_rock.st')
step(0, 0, 0, 'start: bottom of the mirror by the rock, Lakilester on the right (pointer 2)')
for item in SEQ:
    g, th, sl = item if len(item) == 3 else (*item, 2)
    p, l = player(e), laki()
    deg = math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th
    a, b = stick_for(deg % 360, 80)
    for i in range(g): step(0, a, b, 'stop-and-go push, aimed at Lakilester: he arcs up-right')
    for i in range(sl): step(0, 0, 0, 'stop-and-go push, aimed at Lakilester: he arcs up-right')
step(0, 0, 0, 'Lakilester in the top-right corner of the lower floor')
for i in range(CDF): step(0, sx, sy, 'run down')
step(CD, sx, sy, 'C-down (frame chosen for the highest speed at the mount)')
for i in range(50): step(0, 0, 0, 'mount: no clip, speed far below the 110+ needed')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('frames', k, 'end', log[-1])
