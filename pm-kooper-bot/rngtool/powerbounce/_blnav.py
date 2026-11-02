"""(run from bot1/) (run from bot1/) from states/blooper_menu.st: inputs 'f:btn:x:y' list in argv[1]; screenshot at the end; save to argv[2]"""
import os, sys, subprocess
from emu import *
from pm import *
from btl import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bn%d' % os.getpid())
for i in range(3): e.step(0, 0, 0, 2)
e.load(os.environ.get('ST', 'states/blooper_menu.st')); e.step(0, 0, 0, 2)
seq = {}
for it in sys.argv[1].split(','):
    f, b, x, y = it.split(':'); seq[int(f)] = (int(b, 16), int(x), int(y))
N = max(seq) + int(os.environ.get('TAIL', '30'))
for f in range(N):
    b, x, y = seq.get(f, (0, 0, 0)); e.step(b, x, y, 2)
print('bstate', bstate(e))
subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', '+repage', '/dev/shm/nav.png'], check=True)
if len(sys.argv) > 2: e.save(sys.argv[2])
