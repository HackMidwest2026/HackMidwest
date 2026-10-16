"""log the partner follow internals (JP addresses = US + 0x1C0): follow state, history index/pointer, the history
point the partner chases, distance partner->Mario (dM) and partner->target (dH), partner speed.
usage: follow_probe.py <state> '<json [[b,sx,sy,n],...]>' [from_frame]"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/fp')
e.load(sys.argv[1])
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
f, start = 0, int(sys.argv[3]) if len(sys.argv) > 3 else 0
for b, sx, sy, n in json.loads(sys.argv[2]):
    for i in range(n):
        e.step(b if i == 0 else 0, sx, sy, 2)
        if f >= start:
            p, l = player(e), laki()
            ptr = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)
            print(f, '(%3d,%3d)' % (sx, sy), 'M %.1f %.1f L %.1f %.1f st %d idx %d ptr %d tgt (%.0f,%.0f) dM %.1f dH %.1f spd %.1f act %d' % (
                p['x'], p['z'], l['x'], l['z'], e.u32(STATE) >> 16, e.u32(IDX), ptr, tx, tz,
                math.hypot(p['x'] - l['x'], p['z'] - l['z']), math.hypot(tx - l['x'], tz - l['z']), l['speed'], p['action']))
        f += 1
