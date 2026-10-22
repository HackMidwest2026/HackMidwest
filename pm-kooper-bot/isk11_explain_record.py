"""Headless recorder for the isk_11 explainer videos. Runs a scenario, saves a state for each recorded frame to
DIR/s%05d.st and writes DIR/log.json (Mario, Laki, follow state, history pointer, frozen target, history ring).
A separate video-enabled process (isk11_explain_render.py) screenshots the states. Throttles when >MAXPEND states wait.
usage: isk11_explain_record.py SCEN DIR   SCEN: push | ledgepush | release_se | release_s | fake"""
import glob, json, math, os, sys, time
from emu import *
from pm import *
from corner_sweep import stick_for
from nav import go_to
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
SCEN, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
MAXPEND = 80
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ier_%s' % SCEN)
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
log = []; k = [0]
def rec(tag, every=1, force=False):
    p, l = player(e), laki(); ptr = e.u32(PTR); idx = e.u32(IDX)
    r = {'k': k[0], 'tag': tag, 'm': [p['x'], p['y'], p['z']], 'act': p['action'], 'l': [l['x'], l['y'], l['z']], 'ls': l['speed'],
         'st': e.u32(STATE) >> 16, 'ptr': ptr, 'idx': idx, 't': [e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)],
         'hist': [[round(e.f32(HIST + 16 * i + 4), 1), round(e.f32(HIST + 16 * i + 12), 1)] for i in range(40)], 'map': where(e)[1], 'shot': False}
    if force or k[0] % every == 0:
        while len(glob.glob(os.path.join(OUT, 's*.st'))) > MAXPEND: time.sleep(0.5)
        e.save(os.path.join(OUT, 's%05d.st' % k[0])); r['shot'] = True
    log.append(r); k[0] += 1
def step(b, sx, sy, tag, every=1, force=False):
    e.step(b, sx, sy, 2); rec(tag, every, force)
def walk_to(x, z, tag, every=1, maxf=300, tol=4, jump_stuck=False):
    hold = 0; h = []
    for i in range(maxf):
        p = player(e); d = math.hypot(x - p['x'], z - p['z'])
        if d < tol: return
        st = stick_for(math.degrees(math.atan2(z - p['z'], x - p['x'])) % 360, 80 if d > 12 else 30)
        b = 0
        if hold: hold -= 1; b = A
        elif jump_stuck and len(h) > 3 and p['action'] in (1, 2) and math.hypot(h[-3][0] - p['x'], h[-3][1] - p['z']) < 1: hold = 9; b = A
        step(b, st[0], st[1], tag, every); h.append((p['x'], p['z']))
def do(d, t, hh, w, tag, every):
    if hh < 0:
        for i in range(-hh): step(A, *stick_for(d % 360, t), tag, every)
    else:
        for i in range(hh): step(0, *stick_for(d % 360, t), tag, every)
    for i in range(w): step(0, 0, 0, tag, every)
def release(path, S, tag2):
    for i in range(10): step(0, 0, 0, 'Laki idles next to Mario: follow state 5, target still frozen far left')
    pts = path + [S]; j = 0
    for f in range(140):
        p = player(e)
        while j < len(pts) - 1 and math.hypot(pts[j][0] - p['x'], pts[j][1] - p['z']) < 10: j += 1
        T = pts[j]; d = math.hypot(T[0] - p['x'], T[1] - p['z'])
        st = stick_for(math.degrees(math.atan2(T[1] - p['z'], T[0] - p['x'])) % 360, 80 if d > 12 or j < len(pts) - 1 else 25) if d > 2 else (0, 0)
        step(0, st[0], st[1], tag2)
if SCEN == 'push':
    e.load('states/isk11_laki_ready.st')
    for i in range(10): step(0, 0, 0, 'start: west end of isk_11, Laki following', 2)
    walk_to(-100, 518, 'walk to the push start (x -150), just left of the leftmost pedestal', 2, tol=3)
    walk_to(-150, 508, 'walk to the push start (x -150), just left of the leftmost pedestal', 2, tol=3)
    for i in range(40): step(0, 0, 0, 'stand still: Laki stops next to Mario (follow state 5)', 2)
    for j in range(400):
        step(0, *stick_for(-90 if j % 2 == 0 else 90, 25), 'wiggle up/down: every move is saved in the 40-slot history', 1)
        if e.u32(IDX) == (e.u32(PTR) - 1) % 40: break
    for i in range(60): step(0, 0, 0, 'history full: recording stops. Laki\'s target (yellow X) is now FROZEN here', 1)
    for (d, t, hh, w) in json.load(open('states/isk_pushrec_-150.st.json')):
        do(d, t, hh, w, 'stop-and-go push: Laki moves, his target stays frozen at the start', 3)
    for i in range(40): step(0, 0, 0, 'push end: Laki 417 units from his frozen target', 1, True)
elif SCEN == 'ledgepush':
    e.load('states/isk_push_-150.st')
    for i in range(10): step(0, 0, 0, 'push end (x -150 start)', 1)
    for (d, t, hh, w) in json.load(open('states/isk_pushrec_ledge.st.json')):
        do(d, t, hh, w, 'push with jumps: Laki goes up onto the lock ledge, target still frozen', 2)
    for i in range(30): step(0, 0, 0, 'Laki on the lock ledge, 486 units from the frozen target', 1, True)
elif SCEN in ('release_se', 'release_s'):
    e.load('states/isk_pushrec_ledge.st')
    if SCEN == 'release_se':
        release([(355, 455)], (368, 520), 'walk SOUTH-EAST off the ledge: Mario leaves the 40 tether on the wrong side')
    else:
        release([(330, 480), (345, 505)], (368, 520), 'walk SOUTH off the ledge first, then over to (368, 520)')
elif SCEN == 'fake':
    e.load('states/isk_ring_-150.st'); a = laki()['addr']
    e.wf32(PLAYER + PS_POS, 390); e.wf32(PLAYER + PS_POS + 4, -598); e.wf32(PLAYER + PS_POS + 8, 475)
    e.wf32(a + 0x38, 410); e.wf32(a + 0x3C, -548.8); e.wf32(a + 0x40, 445)
    for i in range(20): step(0, 0, 0, 'RAM placement: Laki low, east of the lock; target frozen at x -145')
    CF = int(os.environ.get('CF', '43')); S = (368.0, 520.0)
    for f in range(CF + 1):
        p = player(e); d = math.hypot(S[0] - p['x'], S[1] - p['z'])
        st = stick_for(math.degrees(math.atan2(S[1] - p['z'], S[0] - p['x'])) % 360, 80 if d > 12 else 25) if d > 2 else (0, 0)
        step(D_CBUTTON if f == CF else 0, st[0], st[1], 'C-DOWN (frame %d)' % f if f == CF else 'walk to (368, 520) and stand')
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: break
        step(0, 0, 0, 'mount reads Laki\'s speed')
    for i in range(160):
        p = player(e); st = stick_for(math.degrees(math.atan2(532 - p['z'], 220 - p['x'])) % 360, 80)
        step(0, st[0], st[1], 'hold toward the isk_19 exit floor while falling')
        if where(e)[1] == 16: break
    for i in range(40): step(0, 0, 0, 'isk_19' if where(e)[1] == 16 else 'loading isk_19')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
open(os.path.join(OUT, 'DONE'), 'w').write('1')
print('recorded', len(log), 'frames')
