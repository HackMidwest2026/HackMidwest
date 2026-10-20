"""kpa_62 route A backups: run route A from the ledge with a deliberate mistake, then the recovery (dismount if riding, jump back up holding UP if Mario is on the y-50 ledge,
hold UP into the north-west corner, RIGHT, LEFT 12, run DOWN 12, mount, B, hold down, C-down on frame 34). Reports where
the mistake leaves Mario and whether the recovery clips.
usage: kpa62_backup.py STATE"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kbk%d' % os.getpid())
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
for f in range(50): e.step(0x80 if f < 25 else 0, *CARD['right'], 2)          # full jump holding right
for i in range(15): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/kbk%d.base' % os.getpid(); e.save(base)
def hold(d, k, rel=20):
    for i in range(k): e.step(0, *CARD[d], 2)
    for i in range(rel): e.step(0, 0, 0, 2)
def chain(left=12, down=12):
    hold('up', 120, 10); hold('right', 30); hold('left', left); hold('down', down, 40)
def attempt(T=34):
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 46):
        held = CARD['down'] if fr <= max(34, min(T, 36)) else (0, 0)       # a player lets go of DOWN once the C-down
        if fr == T: e.step(0x400, *held, 2)                                 # moment has passed
        else: e.step(0, *held, 2)
    ins = False
    for f in range(15):
        e.step(0, *(CARD['down'] if T <= 36 else (0, 0)), 2); q = player(e); ins |= inside_tower(q['x'], q['z'])
    for i in range(30): e.step(0, 0, 0, 2)
    return ins
def recover():
    p = player(e)
    if p['action'] == 33:                                                    # still riding: dismount
        e.step(0x40, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
    p = player(e)
    if p['y'] < 58:                                                          # on the y-50 ledge: jump back up holding up
        for f in range(50): e.step(0x80 if f < 25 else 0, *CARD['up'], 2)
        for i in range(15): e.step(0, 0, 0, 2)
    chain(); return attempt()
cases = [('C-down on frame 33', dict(T=33)), ('C-down on frame 35', dict(T=35)), ('C-down on frame 30', dict(T=30)),
         ('C-down on frame 40', dict(T=40)), ('no C-down', dict(T=99)), ('run down 11', dict(down=11)), ('run down 13', dict(down=13)),
         ('left 10', dict(left=10)), ('left 14', dict(left=14))]
for name, c in cases:
    e.load(base)
    chain(left=c.get('left', 12), down=c.get('down', 12))
    ok1 = attempt(c.get('T', 34)); p = player(e)
    where = 'y-60 platform' if abs(p['y'] - 60) < 1 and p['action'] != 33 else ('riding Laki' if p['action'] == 33 else 'y %.0f' % p['y'])
    ok2 = recover()
    print('%-20s first try %-5s -> Mario at (%.0f, %.0f, %.0f) %-14s recovery: %s' % (name, 'CLIP' if ok1 else 'miss', p['x'], p['y'], p['z'], where, 'CLIP' if ok2 else 'fails'), flush=True)
