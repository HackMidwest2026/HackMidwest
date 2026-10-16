"""pra_02 start state BEHIND the mirror: do the normal mirror clip (left-pillar push, down 10, right 4, walk up
slowly + C-down), get off Lakilester, walk to the back-left corner (up, then left) so Lakilester trails on Mario's
right facing left. Saves states/pra02_back_left.st."""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mkback')
e.load('states/pra02_leftpillar.st')
for i in range(30): e.step(0, 0, 0, 2)
while player(e)['x'] < 712:
    e.step(0, 80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
for k in range(10): e.step(0, 0, -80, 2)
for k in range(4): e.step(0, 80, 0, 2)
e.step(0, 0, 20, 2); e.step(CD, 0, 20, 2)
for k in range(45): e.step(0, 0, 0, 2)
p = player(e); print('after clip', p['action'], p['x'], p['z'])
e.step(CD, 0, 0, 2)
for k in range(40): e.step(0, 0, 0, 2)
p = player(e); print('dismounted', p['action'], p['x'], p['z'])
for k in range(60): e.step(0, 0, 80, 2)
for k in range(220): e.step(0, -80, 0, 2)
for k in range(60): e.step(0, 0, 0, 2)
p = player(e)
l = [n for n in npcs(e) if n['id'] == -4][0]
print('mario %.2f %.2f %.2f laki %.2f %.2f %.2f yaw %.0f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.f32(l['addr'] + 0x34)), where(e)[:2])
e.save('states/pra02_back_left.st')

# the push lane: against the back wall (z -212) just right of the back-left pillar (x 234..266), Lakilester on the
# right facing left (walk right, up to the wall, then left into the pillar)
for k in range(130): e.step(0, 80, 0, 2)
for k in range(30): e.step(0, 0, 80, 2)
for k in range(120):
    e.step(0, -80, 0, 2)
    if player(e)['x'] < 276 or player(e)['z'] > -211.5: break
for k in range(60): e.step(0, 0, 0, 2)
p = player(e)
l = [n for n in npcs(e) if n['id'] == -4][0]
print('pillar: mario %.2f %.2f %.2f laki %.2f %.2f %.2f yaw %.0f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.f32(l['addr'] + 0x34)), where(e)[:2])
e.save('states/pra02_back_pillar.st')
