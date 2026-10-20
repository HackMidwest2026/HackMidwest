"""kpa_62: landing spots on the y-60 platform from the pinned y-35 ledge spot, for jump programs: optional spin (Z tap,
UP held s frames), jump with A held a frames and RIGHT held d frames. Groups landings that are identical across a run
of d values (forgiving jumps) and prints them.
usage: kpa62_landings.py STATE OUT.json"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/klnd%d' % os.getpid())
tmp = '/dev/shm/pmbot/klnd%d' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
e.save(tmp + '.fp')
res = []
for s in (0, 1, 2, 3):
    for SD in (('up', 'right', 'down', 'left') if s else ('none',)):
        for a in (3, 5, 8, 12, 25):
            row = []
            for d in range(0, 46):
                e.load(tmp + '.fp')
                if s:
                    e.step(0x20, *CARD[SD], 2)
                    for i in range(s - 1): e.step(0, *CARD[SD], 2)
                for f in range(50): e.step(0x80 if f < a else 0, *(CARD['right'] if f < d else (0, 0)), 2)
                for i in range(15): e.step(0, 0, 0, 2)
                p = player(e)
                row.append((d, round(p['x'], 2), round(p['y'], 1), round(p['z'], 2)))
            # group runs of identical landings on y 60
            i = 0
            while i < len(row):
                j = i
                while j + 1 < len(row) and row[j + 1][1:] == row[i][1:]: j += 1
                if abs(row[i][2] - 60) < .5 and j - i >= 2:
                    res.append({'spin': [SD, s] if s else None, 'a': a, 'd': [row[i][0], row[j][0]], 'land': [row[i][1], row[i][3]]})
                    print(res[-1], flush=True)
                i = j + 1
json.dump(res, open(sys.argv[2], 'w'))
