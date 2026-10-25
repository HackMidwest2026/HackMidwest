"""kpa_62 blockless, corner setup: full jump off the y-35 ledge holding screen-right, keep holding right until Mario
stops against the tower at (-429.263, -90.233), up-left UL frames, down 12 frames, then mount, ride, C-down dismount,
hold down, C-down on frame 34 after the dismount, and let Mario fall inside the tower.
usage: kpa62_corner_setup.py START.st [UL]   (START: Mario on the ledge with Laki settled)"""
import os, sys
from emu import *
from pm import *
from kpa62_runner import run, stick
from kpa62_tower import inside_tower
CD = 0x400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kcs%d' % os.getpid())
e.load(sys.argv[1]); e.step(0, 0, 0, 2)
UL = int(sys.argv[2]) if len(sys.argv) > 2 else 21
for i in range(15): e.step(0, 0, 0, 2)
run(e, 'J:0:10:25')                                   # full jump holding right
for i in range(70): e.step(0, *stick(0), 2)           # keep holding right into the tower
for i in range(10): e.step(0, 0, 0, 2)
print('stopped at', player(e), flush=True)
for i in range(UL): e.step(0, *stick(225), 2)         # up-left
for i in range(12): e.step(0, *stick(90), 2)          # down, exactly 12
for i in range(14): e.step(0, 0, 0, 2)
print('stand', player(e), flush=True)
e.step(CD, 0, 0, 2)                                   # mount
for i in range(17): e.step(0, 0, 0, 2)
e.step(CD, *stick(90), 2)                             # dismount, hold down
for f in range(1, 34): e.step(0, *stick(90), 2)
e.step(CD, *stick(90), 2)                             # C-down on frame 34
ok = False
for f in range(40):
    e.step(0, *stick(90), 2); q = player(e)
    if f > 18 and inside_tower(q['x'], q['z']): ok = True
e.step(CD, 0, 0, 2)                                   # get off Laki inside the tower
for f in range(60): e.step(0, 0, 0, 2)
print('CLIP' if ok else 'no', player(e), flush=True)
