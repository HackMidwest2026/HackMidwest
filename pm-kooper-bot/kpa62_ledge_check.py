"""kpa_62: end-to-end check of setups that start on the y-35 ledge (pinned by holding RIGHT). Program tokens:
DIR:k (hold cardinal k frames, then 20 neutral), Z:DIR:k (spin: Z + DIR, held k frames), A:DIR:a:d (jump: A held a
frames, DIR held d frames, 45 frames total, then 10 neutral). Then settle, mount, ride, B, hold down, C-down on frame 34.
usage: kpa62_ledge_check.py STATE 'Z:up:2 A:right:25:5 up:120 right:30 left:12 down:12' ..."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/klc%d' % os.getpid())
base = '/dev/shm/pmbot/klc%d.base' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
e.save(base)
def run_prog(prog):
    for t in prog.split():
        f = t.split(':')
        if f[0] == 'Z':
            e.step(0x20, *CARD[f[1]], 2)
            for i in range(int(f[2]) - 1): e.step(0, *CARD[f[1]], 2)
        elif f[0] == 'A':
            a, d = int(f[2]), int(f[3])
            for i in range(45): e.step(0x80 if i < a else 0, *(CARD[f[1]] if i < d else (0, 0)), 2)
            for i in range(10): e.step(0, 0, 0, 2)
        else:
            for i in range(int(f[1])): e.step(0, *CARD[f[0]], 2)
            for i in range(20): e.step(0, 0, 0, 2)
for prog in sys.argv[2:]:
    e.load(base); run_prog(prog)
    for i in range(40): e.step(0, 0, 0, 2)
    s = player(e)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2); ok = False
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): ok = True
    print('%-58s stand (%.3f %.2f) %s' % (prog, s['x'], s['z'], 'CLIP' if ok else 'no'), flush=True)
