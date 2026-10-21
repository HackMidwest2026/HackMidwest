"""Ruins Stones Skip setup in isk_11 (Stone Puzzle Room), no position edits.
1. From the room entry, walk to START (approached from the east so Mario faces west and Laki idles on his right),
   settle, then wiggle north/south at low tilt until the 40-entry move history is full: Laki idles in follow state 5
   and his target (the oldest history entry) freezes near START.
2. Stop-and-go push (go 1 frame, stop 2): Mario first lines up BACK units behind Laki (opposite GOAL) at low tilt, then
   steps toward GOAL. partner_do_player_collision moves him
   1 unit away from Mario plus 2 units along the camera with no collision test. A cycle is kept only while the follow
   state stays 5 and the frozen target is unchanged.
3. Release: Mario follows PATH (toward the lowest level); C-down on frame f. The mount reads Laki's moveSpeed (0.25 x
   his distance to the frozen target when he is above Mario) to build the landing point. Reports per f: speed, landing
   point, lowest y over 150 frames and the map Mario ends in.
usage: isk11_push.py SX SZ GX GZ OUT.json   env: PATH_PTS "x,z;x,z;...", MAXC, F0, F1, BACK, ALIGN, MAG"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
from nav import go_to
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
SX, SZ, GX, GZ = (float(v) for v in sys.argv[1:5]); OUT = sys.argv[5]
MAXC = int(os.environ.get('MAXC', '900'))
PATH = [tuple(float(a) for a in p.split(',')) for p in os.environ.get('PATH_PTS', '300,520;370,500').split(';')]
F0, F1 = int(os.environ.get('F0', '1')), int(os.environ.get('F1', '90'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ip%d' % os.getpid())
tmp = '/dev/shm/pmbot/ip%d' % os.getpid()
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
go_to(e, SX + 50, SZ + 10, maxf=300); go_to(e, SX, SZ, maxf=200, tol=3)
for i in range(60): e.step(0, 0, 0, 2)
for k in range(400):
    e.step(0, *stick_for(-90 if k % 2 == 0 else 90, 25), 2)
    if e.u32(IDX) == (e.u32(PTR) - 1) % 40: break
for i in range(10): e.step(0, 0, 0, 2)
ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
p, l = player(e), laki()
print('ring full: state %d target (%.1f, %.1f); Mario (%.1f, %.1f) Laki (%.1f, %.1f, %.1f)' % (e.u32(STATE) >> 16, tx, tz, p['x'], p['z'], l['x'], l['y'], l['z']), flush=True)
def intact(): return e.u32(PTR) == ptr0 and (e.u32(STATE) >> 16) == 5 and e.f32(HIST + 16 * ptr0 + 4) == tx and e.f32(HIST + 16 * ptr0 + 12) == tz
e.save(tmp + '.good'); cyc = 0
BACK, ALIGN, MAG = float(os.environ.get('BACK', '14')), float(os.environ.get('ALIGN', '5')), int(os.environ.get('MAG', '50'))
for cyc in range(MAXC):
    p, l = player(e), laki()
    ux, uz = GX - l['x'], GZ - l['z']; n = math.hypot(ux, uz) or 1; ux, uz = ux / n, uz / n
    px, pz = l['x'] - ux * BACK, l['z'] - uz * BACK          # spot behind Laki, opposite the goal
    if math.hypot(px - p['x'], pz - p['z']) > ALIGN:
        aim = math.degrees(math.atan2(pz - p['z'], px - p['x'])); mag = 30
    else:
        aim = math.degrees(math.atan2(uz, ux)); mag = MAG
    e.step(0, *stick_for(aim % 360, mag), 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    if not intact():
        print('push broke at cycle %d' % cyc); e.load(tmp + '.good'); break
    e.save(tmp + '.good')
    l = laki()
    if cyc % 60 == 0: print('  cycle %d Mario (%.0f, %.0f) Laki (%.0f, %.0f, %.0f) d %.1f' % (cyc, p['x'], p['z'], l['x'], l['y'], l['z'], math.hypot(l['x'] - tx, l['z'] - tz)), flush=True)
    if math.hypot(GX - l['x'], GZ - l['z']) < 20: break
p, l = player(e), laki(); d = math.hypot(l['x'] - tx, l['z'] - tz)
print('push end after %d cycles: Mario (%.1f, %.1f, %.1f) Laki (%.1f, %.1f, %.1f) d %.1f' % (cyc, p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], d), flush=True)
e.step(0, 0, 0, 2); e.save(tmp + '.end'); e.step(0, 0, 0, 2); e.save('/dev/shm/pmbot/isk_pushend.st')
res = []
for f in range(F0, F1 + 1):
    e.load(tmp + '.end'); k = 0
    for i in range(f):
        q = player(e)
        while k < len(PATH) - 1 and math.hypot(PATH[k][0] - q['x'], PATH[k][1] - q['z']) < 10: k += 1
        st = stick_for(math.degrees(math.atan2(PATH[k][1] - q['z'], PATH[k][0] - q['x'])) % 360, 80)
        e.step(0x400 if i == f - 1 else 0, st[0], st[1], 2)
    a = laki()['addr']; S = None; mt = None
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: S = e.f32(a + 0x18); mt = (e.f32(a + 0x60), e.f32(a + 0x64), e.f32(a + 0x68)); break
        e.step(0, 0, 0, 2)
    pc = player(e); low = 1e9
    for i in range(150):
        e.step(0, 0, 0, 2); low = min(low, e.f32(PLAYER + PS_POS + 4))
    q = player(e)
    r = {'f': f, 'press_at': (round(pc['x'], 1), round(pc['y'], 1), round(pc['z'], 1)), 'speed': None if S is None else round(S, 1),
         'target': None if mt is None else [round(v, 1) for v in mt], 'low': round(low, 1), 'end': (round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)), 'map': where(e)}
    res.append(r); print(r, flush=True)
json.dump({'start': (SX, SZ), 'goal': (GX, GZ), 'frozen_target': (tx, tz), 'laki_end': (l['x'], l['y'], l['z']), 'd': d, 'runs': res}, open(OUT, 'w'))
