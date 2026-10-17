"""Video of the newest setup (CountPerOp 1, run with M64P_DATA set), stage by stage from the same saved states the
searches used, so every frame matches them:
 1 fill   states/pra01_top_rock.st      wiggle until the history ring is full (fill_history.py)
 2 arc    states/pra01_top_rock_full.st arc push into the lower corner (states/pra01_corner_full_seq.json)
 3 ledge  states/pra01_corner_full.st   3 up, jump holding right, 1 right + jump, push to the palace wall, 30 frames
 4 run    states/pra01_topright_full.st the brute force's best sequence (BEST json), C-down, mount
Saves one savestate per frame of stage STAGE into OUT (render_states.py turns them into frames) and appends the
per-frame log to OUT/log.json. usage: STAGE=n record_rev5.py OUT BEST.json"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x0400
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT, BEST = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
STAGE = int(os.environ['STAGE'])
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rr5')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
logp = os.path.join(OUT, 'log.json')
log = json.load(open(logp)) if os.path.exists(logp) else []
k = len(log)
def step(b, sx, sy, tag):
    global k
    e.step(b, sx, sy, 2)
    p, l = player(e), laki(); ptr = e.u32(PTR)
    log.append({'i': k, 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'act': p['action']})
    e.save(os.path.join(OUT, 's%04d.st' % k)); k += 1
if STAGE == 1:
    e.load('states/pra01_top_rock.st'); step(0, 0, 0, 'start by the rock: Laki idle on the right, history pointer 2')
    up, dn = stick_for(270, 30), stick_for(90, 30)
    for f in range(120):
        step(0, *(up if f % 2 == 0 else dn), 'wiggle in place: fill Laki\'s history with points at the rock')
        if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
    for i in range(11): step(0, 0, 0, 'history full: every old point is at the rock')
elif STAGE == 2:
    e.load('states/pra01_top_rock_full.st'); step(0, 0, 0, 'stop-and-go push aimed at Laki: the arc')
    for g, th, sl in json.load(open('states/pra01_corner_full_seq.json')):
        p, l = player(e), laki()
        sx, sy = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(g): step(0, sx, sy, 'stop-and-go push aimed at Laki: the arc')
        for i in range(sl): step(0, 0, 0, 'stop-and-go push aimed at Laki: the arc')
elif STAGE == 3:
    e.load('states/pra01_corner_full.st'); step(0, 0, 0, 'lower corner reached')
    rx, ry = stick_for(0, 80)
    for i in range(3): step(0, *stick_for(270, 80), '3 frames up to the top wall')
    for W, H, tag in ((0, 12, 'jump holding right: Laki goes up the ledge'), (1, 0, '1 frame right + jump: Mario up the ledge')):
        for i in range(W): step(0, rx, ry, tag)
        for i in range(24):
            step(0x80 if i < 8 else 0, rx if i < H else 0, ry if i < H else 0, tag)
            if i > 3 and player(e)['action'] in (0, 1, 2): break
        for i in range(3): step(0, 0, 0, tag)
    for c in range(150):
        step(0, rx, ry, 'stop-and-go push right along the top wall'); step(0, 0, 0, 'stop-and-go push right along the top wall'); step(0, 0, 0, 'stop-and-go push right along the top wall')
        if laki()['x'] >= 984: break
    for i in range(30): step(0, 0, 0, 'palace corner: Laki 442.7 from his stale target; wait ~1 s')
else:
    e.load('states/pra01_topright_full.st'); step(0, 0, 0, 'release (brute-force best)')
    seq = json.load(open(BEST))['seq']
    for b, sx, sy in seq: step(b, sx, sy, 'release (brute-force best): Laki flies to the rock and races back')
    step(CD, seq[-1][1], seq[-1][2], 'C-down in the strip (mount speed 75.2; 116 needed)')
    for i in range(35): step(0, 0, 0, 'mount: no clip')
json.dump(log, open(logp, 'w'))
print('stage', STAGE, 'frames now', k, 'last', {kk: round(log[-1][kk], 1) for kk in ('x', 'z', 'lx', 'lz', 'ls')})
