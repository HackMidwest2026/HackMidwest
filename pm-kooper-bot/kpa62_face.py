"""kpa_62: Mario pressed against the tower's west face (collider 1, x -409 at z -55 to x -414 at z -75).
1) slide trace: start at START (x, z), hold stick ANG for N frames, print (x, z) per frame;
2) window test: for each slide length k, then hold LEFT (screen) for M frames, and check the clip
   (mount, ride, C-down dismount, hold down, C-down on frame 34).
usage: kpa62_face.py trace X Z ANG N | kpa62_face.py window X Z ANG K0 K1 M"""
import os, sys
from emu import *
from pm import *
from kpa62_place import place
from kpa62_runner import run, clip, stick
e = Emu('pm-jp.z64', '/dev/shm/pmbot/kf%d' % os.getpid())
def start(x, z):
    e.load('states/kpa62_e1.st'); e.step(0, 0, 0, 2); place(e, x, z, y=60.0)
mode, X, Z, ANG = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
if mode == 'trace':
    start(X, Z)
    for i in range(int(sys.argv[5])):
        e.step(0, *stick(ANG), 2); p = player(e)
        print(i + 1, '%.4f %.4f' % (p['x'], p['z']))
else:
    k0, k1, M = int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
    for k in range(k0, k1):
        start(X, Z)
        for i in range(k): e.step(0, *stick(ANG), 2)
        for i in range(10): e.step(0, 0, 0, 2)
        p0 = player(e)
        for i in range(M): e.step(0, *stick(180), 2)
        for i in range(14): e.step(0, 0, 0, 2)
        s, ok, q = clip(e, 18, 34)
        print('slide %3d -> face (%.4f, %.4f)  left %d -> stand (%.4f, %.4f) %s' % (k, p0['x'], p0['z'], M, s['x'], s['z'], 'CLIP' if ok else 'no'), flush=True)
