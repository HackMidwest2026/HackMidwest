"""From STATE (Mario on the lock ledge), walk to TARGET on the y -600 floor, then idle and log Laki every frame.
env TARGET=x,z  HAMMER=frame (press B once that many frames after arriving)  N=frames to log"""
import math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
T = tuple(float(v) for v in os.environ.get('TARGET', '365,545').split(','))
HAM = int(os.environ.get('HAMMER', '-1')); N = int(os.environ.get('N', '200'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/idw%d' % os.getpid())
e.load(sys.argv[1])
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
FS = lambda: e.u32(0x8010D188) >> 16
for i in range(200):
    q = player(e)
    if math.hypot(T[0] - q['x'], T[1] - q['z']) < 3 and q['action'] in (0, 1, 2): break
    st = stick_for(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])) % 360, 80 if math.hypot(T[0] - q['x'], T[1] - q['z']) > 12 else 25)
    e.step(0, st[0], st[1], 2)
    L = lk(); print('walk', i, round(q['x']), round(q['y']), round(q['z']), q['action'], '| laki', round(L['x']), round(L['y']), round(L['z']), round(L['speed'], 1), FS())
for i in range(N):
    e.step(B if i == HAM else 0, 0, 0, 2)
    q = player(e); L = lk()
    print('idle', i, round(q['x']), round(q['y']), round(q['z']), q['action'], '| laki', round(L['x'], 1), round(L['y'], 1), round(L['z'], 1), 'spd', round(L['speed'], 2), 'fs', FS(), 'd', round(math.hypot(L['x'] - q['x'], L['z'] - q['z']), 1))
