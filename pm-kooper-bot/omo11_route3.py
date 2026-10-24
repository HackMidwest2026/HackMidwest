"""Second half of the omo_11 route (after omo11_route2.py reaches the floor west of platform 57):
floor -> step 27 (y35, front) -> bobbing 60 (58..140) -> top of block 30 (y140) -> bobbing 63 (140..210)
-> top of block 22 (y210) -> under the Super Block. usage: omo11_route3.py START.st OUT.st [STAGE_DIR] [DELAY]"""
import os, sys
from omo11_routelib import *
SD = sys.argv[3] if len(sys.argv) > 3 else None
import omo11_routelib as L; L.SD = SD
DELAY = int(sys.argv[4]) if len(sys.argv) > 4 else 0
def sg():
    return [n for n in npcs(e) if n['id'] == 0][0]
def to27():
    walk(-5, -60, 'around22'); walk(-250, -68, 'behind22'); walk(-300, 40, 'west floor'); walk(-275, 105, 'by27w', tol=4)
    jump_to(-237, 105, tag='onto27', expect_y=35)
    for i in range(30): e.step(0, 0, 0, 2); chk('settle27')
# The Shy Guy wanders around step 27; leave when it is in a spot that lets Mario get by (a runner watches it).
# Try departures DELAY, DELAY+20, ... until one reaches step 27 without a battle.
e.load(sys.argv[1]); e.step(0, 0, 0, 2)   # a save right after a load is dropped by the core
TMP = '/dev/shm/pmbot/r3_%d.st' % os.getpid(); e.save(TMP); e.step(0, 0, 0, 2)
for d in range(DELAY, DELAY + 800, 20):
    e.load(TMP)
    for i in range(d): e.step(0, 0, 0, 2)
    g = sg(); gpos = (round(g['x']), round(g['z']))
    try:
        to27(); print('left after', d, 'steps; Shy Guy was at', gpos, flush=True); break
    except SystemExit:
        continue
else:
    print('no departure worked'); sys.exit(1)
stage('q_step27', 35)
wait_until(lambda: box(60)[1] < 61, 'wait60'); jump_to(-300, 110, tag='onto60', expect_y=lambda: box(60)[1]); stage('r_on60')
ride(60, lambda: box(60)[1] > 139.5, 'ride60'); walk(-395, 110, 'onto30'); stage('s_top30', 140)
walk(-395, -105, 'top30 back'); wait_until(lambda: box(63)[1] < 141, 'wait63')
walk(-313, -105, 'onto63', tol=5, maxf=60); stage('t_on63')
ride(63, lambda: box(63)[1] > 209.5, 'ride63'); walk(-285, -108, 'edge63', tol=3, maxf=60)
jump_to(-195, -110, hold=12, tag='onto22', expect_y=210); stage('u_top22', 210)
walk(-115, -112, 'under block', tol=1.5); stage('o_under_block', 210)
e.save(sys.argv[2])
