"""Gap check at the low-speed clip spots in isk_11 (exploration: Mario's position and Laki's speed are RAM writes).
For Mario at (PX, PZ) on the -600 floor and each mount speed S, record the mount landing point (Laki moveToPos),
whether isk_19 loads when Mario steers toward the exit floor, the floors under the landing point, and the closest
Mario gets (x/z) to the exit floor rectangle (collider 13: x 188..252, z 500..564) while below y -600.
usage: isk11_gap.py X Z S0 S1"""
import json, math, sys
from emu import *
from pm import *
from corner_sweep import stick_for
PX, PZ = float(sys.argv[1]), float(sys.argv[2]); S0, S1 = int(sys.argv[3]), int(sys.argv[4])
exec(open('isk11_clip_map.py').read().split("e = Emu(")[0].split("PART, NP, out")[0])
d = json.load(open('isk11_collision.json'))
floors = [(c['id'], t['v']) for c in d['colliders'] if not (c['flags'] & 0x7FFFFE00) for t in c['tris'] if t['n'][1] > 0.7]
src = open('isk11_clip_map.py').read()
exec(src[src.index('def floors_at'):src.index('e = Emu(')])
def rect_dist(x, z): return math.hypot(max(188 - x, 0, x - 252), max(500 - z, 0, z - 564))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/igap')
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/igap.st'; e.save(base)
for S in range(S0, S1 + 1):
    e.load(base)
    lk = [q for q in npcs(e) if q['id'] == -4][0]['addr']
    e.wf32(PLAYER + PS_POS, PX); e.wf32(PLAYER + PS_POS + 4, -598.0); e.wf32(PLAYER + PS_POS + 8, PZ)
    e.wf32(lk + 0x38, PX - 20); e.wf32(lk + 0x3C, -580.0); e.wf32(lk + 0x40, PZ)
    for i in range(4): e.step(0, 0, 0, 2)
    e.wf32(lk + 0x18, float(S)); e.step(D_CBUTTON, 0, 0, 2); t = None
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: t = (e.f32(lk + 0x60), e.f32(lk + 0x68)); break
        e.wf32(lk + 0x18, float(S)); e.step(0, 0, 0, 2)
    if t is None: print(S, 'no mount'); continue
    below = [round(f[0]) for f in floors_at(t[0], t[1])]
    best = 1e9; ok = False; low = 1e9
    for f in range(150):
        q = player(e); st = stick_for(math.degrees(math.atan2(532 - q['z'], 220 - q['x'])) % 360, 80)
        e.step(0, st[0], st[1], 2); q = player(e); low = min(low, q['y'])
        if q['y'] < -605: best = min(best, rect_dist(q['x'], q['z']))
        if where(e)[1] == 16: ok = True; break
    print('S %3d landing (%.1f, %.1f) floors under %s  lowest y %.0f  closest to exit floor while below -605: %s  %s' % (S, t[0], t[1], below, low, 'n/a' if best > 1e8 else '%.1f' % best, 'ISK19' if ok else ''))
