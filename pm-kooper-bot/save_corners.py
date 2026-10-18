"""Save the end of every corner arc in a rev_aim_explore2 archive as a corner state (the arc is replayed from the
seed; the ledge searches load it and step one neutral frame). usage: save_corners.py <arch.json> <seed.st> <prefix>"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
arch, seed, pre = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/sc%d' % os.getpid())
cands = sorted((a for k, a in arch.items() if k != 'seed' and a['lx'] >= 690 and a['lz'] <= -200), key=lambda a: len(a['seq']))
for n, a in enumerate(cands):
    e.load(seed); e.step(0, 0, 0, 2)
    for g, th, sl in a['seq']:
        p, l = player(e), [x for x in npcs(e) if x['id'] == -4][0]
        sx, sy = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
        for i in range(g): e.step(0, sx, sy, 2)
        for i in range(sl): e.step(0, 0, 0, 2)
    e.save('%s%d.st' % (pre, n)); json.dump(a['seq'], open('%s%d_seq.json' % (pre, n), 'w'))
    print(n, 'L (%.0f, %.0f)' % (a['lx'], a['lz']), '%s%d.st' % (pre, n))
