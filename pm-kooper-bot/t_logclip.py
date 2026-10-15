"""reproduce the jan_04 log clip from the video's inputs."""
import sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jan')
def setup():
    e.load('states/jan04_start.st')
    e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, -137.0); e.wf32(PLAYER + PS_POS + 4, 2.457098); e.wf32(PLAYER + PS_POS + 8, 37.07176)
    for i in range(10): e.step(0, -128, 26, 2) if False else e.step(0, 0, 0, 2)
    e.save('/dev/shm/pmbot/jan/pre.st')
setup()
def run(spin_frames, air_frames, verbose=False):
    e.load('/dev/shm/pmbot/jan/pre.st')
    tr = []
    seq = [(Z, -128, 26)] + [(0x20, -128, 26)] * (spin_frames - 1) + [(A | Z, -128, 26)] * air_frames + [(A, -128, -128)] * 14
    for i, (b, x, y) in enumerate(seq):
        e.step(b, x, y, 2)
        p = player(e)
        tr.append((i, ACTION_NAMES.get(p['action'], p['action']), round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), round(p['speed'], 1)))
    return tr
best = None
for sf in range(3, 9):
    for af in range(6, 14):
        tr = run(sf, af)
        minx = min(t[2] for t in tr)
        if best is None or minx < best[0]:
            best = (minx, sf, af, tr)
print('best spin frames %d air frames %d min x %.2f' % (best[1], best[2], best[0]))
for t in best[3]: print('  ', t)

print('--- search for the clip: end west of x=-150 and south of z=30 (behind both walls) ---')
found = []
for sf in range(2, 14):
    for af in range(3, 16):
        for sw in ((-128, -128), (-128, -100), (-128, -60), (-100, -128), (-128, 0)):
            e.load('/dev/shm/pmbot/jan/pre.st')
            seq = [(Z, -128, 26)] + [(0x20, -128, 26)] * (sf - 1) + [(A | Z, -128, 26)] * af + [(A, sw[0], sw[1])] * 14
            prev = None; cross = None
            for i, (b, x, y) in enumerate(seq):
                e.step(b, x, y, 2)
                p = player(e)
                if prev and prev[0] > -150 >= p['x']: cross = (round(prev[2], 2), round(p['z'], 2))
                prev = (p['x'], p['y'], p['z'])
            if prev[0] < -150 and prev[2] > 30:
                found.append((sf, af, sw, cross, [round(v, 2) for v in prev]))
print(len(found), 'clips')
for f in found[:15]: print('  spin frames %d, air frames %d, then stick %s: z before/after crossing x=-150 %s, end %s' % f)
