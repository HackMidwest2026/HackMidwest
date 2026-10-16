"""pra_01: Mario runs right along z~Z (Lakilester trails on his left), stops, then pushes Lakilester LEFT with the
stop-and-go (go 1 / stop 2 at stick (-80,0)) back toward the corridor. Prints per cycle Mario/Laki/speed."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p60')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
UP, RUN, Z = int(sys.argv[1]), int(sys.argv[2]), 0
e.load('states/pra01_start.st')
for i in range(UP): e.step(0, 0, 80, 2)
for i in range(RUN): e.step(0, 80, 0, 2)
for i in range(30): e.step(0, 0, 0, 2)
p, l = player(e), laki()
print('start mario %.2f %.2f %.2f laki %.2f %.2f %.2f yaw %.0f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.f32(l['addr'] + 0x34)))
for c in range(200):
    e.step(0, -80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    p, l = player(e), laki()
    if c % 10 == 0 or p['x'] < 520:
        print(c, 'mario %.2f %.2f %.2f laki %.2f %.2f %.2f spd %.2f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], l['speed']), where(e)[:2])
    if p['x'] < 505 or where(e)[:2] != (21, 0): break
