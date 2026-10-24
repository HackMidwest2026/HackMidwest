"""omo_10 -> omo_11 east entrance with optional actions in omo_10 first (inputs only). Mario holds the stick at
world yaw 225 into the loading zone. Env PRE (same action syntax as omo11_superblock_probe.pre) runs first;
env MARK=1 is a labeled diagnostic only: on the last omo_10 frame, every free general-heap block payload is
filled with 0x5A000000|addr so the APG menu fields show which omo_10 address they came from.
usage: omo10_to_omo11.py OUT.st   (env START10: omo_10 state, e.g. after loading the save; WAIT10: idle steps)"""
import os, sys
from emu import *
from pm import *
from nav import stick_world
from omo11_heapwalk import walk
import omo11_superblock_probe as P
e = P.e
e.load(os.environ.get('START10', 'states/omo10_e0_goompa.st')); e.step(0, 0, 0, 2)
for i in range(int(os.environ.get('WAIT10', '0'))): e.step(0, 0, 0, 2)
if os.environ.get('START10'):                       # from the save block: walk back to the room's entry spot first
    from nav import go_to
    go_to(e, -330, 330, maxf=900, tol=4)
w0 = where(e)
P.pre(os.environ.get('PRE', ''))
for f in range(600):
    st = stick_world(e, 225)
    if os.environ.get('MARK'):
        # look one step ahead: snapshot, step, and if the map changed, go back and mark first
        e.save('/dev/shm/pmbot/o10_look_%d.st' % os.getpid())
        e.step(0, *st, 2)
        if where(e) != w0:
            e.load('/dev/shm/pmbot/o10_look_%d.st' % os.getpid())
            n = 0
            for nd, bk, ln, al, mid in walk(e):
                if al: continue
                for a in range(bk, bk + min(ln, 0x40000), 4): e.w32(a, 0x5A000000 | (a & 0xFFFFFF)); n += 1
            print('marked', n, 'words', file=sys.stderr)
            os.environ.pop('MARK')
            e.step(0, *st, 2)
            break
        continue
    e.step(0, *st, 2)
    if where(e) != w0: break
for i in range(200): e.step(0, 0, 0, 2)
print('now', where(e), player(e), file=sys.stderr)
e.save(sys.argv[1])
