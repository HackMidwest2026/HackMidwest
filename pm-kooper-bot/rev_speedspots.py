"""from states/pra01_topright.st: random movement sequences (as rev_local_topright), no C-down; record every frame
where Lakilester's speed >= 60 with Mario's position, to see WHERE Mario is when Lakilester is fast.
usage: rev_speedspots.py <out.json> <minutes>"""
import json, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ss%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'] = Emu(os.environ['PM_ROM'], d)
def rand_seq():
    out = []
    while len(out) < 90:
        st = (0, 0) if random.random() < 0.3 else stick_for(random.uniform(0, 360), random.choice((10, 16, 20, 30, 50, 80)))
        n = random.choice((1, 2, 4, 8, 15, 30)); jump = random.random() < 0.1
        out += [((0x80 if jump and i < 8 else 0), st[0], st[1]) for i in range(n)]
    return out[:90]
def run(seq):
    e = W['e']; e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    out = []
    for f, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        for n in npcs(e):
            if n['id'] == -4 and n['speed'] >= 60:
                p = player(e)
                out.append((round(n['speed'], 1), f, round(p['x']), round(p['y']), round(p['z']), round(n['x']), round(n['z'])))
    return seq, out
if __name__ == '__main__':
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, allp = time.time(), []
    while time.time() - t0 < float(sys.argv[2]) * 60:
        for seq, out in pool.map(run, [rand_seq() for _ in range(64)], chunksize=4):
            for o in out: allp.append(list(o) + [seq[:o[1] + 1]])
    json.dump(allp, open(sys.argv[1], 'w'))
    allp.sort(key=lambda o: -o[0])
    print(len(allp), 'fast frames')
    for o in allp[:25]: print(o[:7])
    import collections
    c = collections.Counter((o[2] // 25 * 25, o[4] // 25 * 25) for o in allp if o[0] >= 100)
    print('Mario cells (25u) when speed >= 100:', sorted(c.items(), key=lambda kv: -kv[1])[:20])
    pool.terminate()
