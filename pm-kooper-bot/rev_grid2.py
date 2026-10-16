"""ASCII standability map of pra_01 real side near the left rock: '.' Mario stays where placed, '#' pushed/fell."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rg')
e.load(os.environ.get('ST','states/pra01_start.st')); e.step(0,0,0,2); e.save('/dev/shm/pmbot/rg/b.st')
X0, X1, XS = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
Z0, Z1, ZS = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
for z in range(Z1, Z0 - 1, -ZS):
    row = ''
    for x in range(X0, X1 + 1, XS):
        e.load('/dev/shm/pmbot/rg/b.st')
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, float(os.environ.get('PY','-57'))); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(8): e.step(0, 0, 0, 2)
        p = player(e)
        ok = tuple(where(e)[:2]) == tuple(map(int, os.environ.get('MAP','21,0').split(','))) and abs(p['x'] - x) < 0.5 and abs(p['z'] - z) < 0.5 and abs(p['y'] - float(os.environ.get('PY','-57')) + 3) < 2
        row += '.' if ok else '#'
    print('%4d %s' % (z, row), flush=True)
