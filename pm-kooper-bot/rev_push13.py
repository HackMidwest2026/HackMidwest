"""pra_01: from the push start (Mario/Lakilester against the mirror, z 13), run right RUN frames so the push starts
further right, settle, then stop-and-go push Lakilester left (go 1 / stop 2, stick (-80,0)) along the mirror.
Prints the push, then for a few release moves Lakilester's speed per frame."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p13')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
def st(tag):
    p, l = player(e), laki()
    print(tag, 'mario %.2f %.2f %.2f laki %.2f %.2f %.2f spd %.2f yaw %.0f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], l['speed'], e.f32(l['addr'] + 0x34)), where(e)[:2], flush=True)
RUN = int(sys.argv[1])
e.load('states/pra01_pushstart.st')
for i in range(RUN): e.step(0, 80, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
st('start')
for c in range(300):
    e.step(0, -80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    if c % 20 == 0: st(c)
    if player(e)['x'] < 530: break
st('end %d' % c)
e.save('/dev/shm/pmbot/p13/end.st')
for deg in (90, 180, 0, 270, 135, 45):
    e.load('/dev/shm/pmbot/p13/end.st'); e.step(0,0,0,2)
    sx, sy = stick_for(deg, 80)
    sp = []
    for f in range(12):
        e.step(0, sx, sy, 2); sp.append(round(laki()['speed'], 1))
    p = player(e)
    print('release', deg, sp, 'mario %.1f %.1f' % (p['x'], p['z']))
