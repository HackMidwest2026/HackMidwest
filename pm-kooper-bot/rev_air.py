"""Does C-down while Mario is in the air during the jump down from the legend corner cross (forced speed)?
From START (states/pra01_topright_fast.st): running jump down (stick angle D, A at frame J held 8) and C-down on
frame f (0..34) of it with Lakilester's speed forced to S (40..250 step 10) until the mount; cross = riding on the
real side (z > 1). usage: rev_air.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
START = os.environ.get('START', 'states/pra01_topright_fast.st')
SPEEDS = list(range(40, 251, 10))
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/air%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    D, J = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    s = stick_for(D, 80)
    e.load(START); e.step(0, 0, 0, 2)
    out = []
    for f in range(35):
        e.save(chk)
        p = player(e)
        for S in SPEEDS:
            e.load(chk); e.step(0x80 if J <= f < J + 8 else 0, *s, 2)
            e.step(CD | (0x80 if J <= f + 1 < J + 8 else 0), *s, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            q = player(e)
            if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0):
                out.append((D, J, f, S, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), p['action'], round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)))
        e.load(chk); e.step(0x80 if J <= f < J + 8 else 0, *s, 2)
    return out
if __name__ == '__main__':
    tasks = list(itertools.product((70, 80, 90, 100, 110, 120, 135), (0, 2, 4, 6)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for o in pool.imap_unordered(run, tasks) for r in o]
    json.dump(res, open(sys.argv[1], 'w'))
    print(len(res), 'crossings')
    for r in res[:30]: print(r)
    pool.terminate()
