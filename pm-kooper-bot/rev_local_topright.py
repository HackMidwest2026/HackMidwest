"""pra_01 REVERSE mirror clip from the legend corner: states/pra01_topright.st (Lakilester idle at the palace wall,
(987, -212), 442 from his frozen target (592, -13)). Random sequences (stick any direction/strength, neutral,
occasional jump), up to 90 frames, C-down tried on every frame; hit = riding on the real side (z > 1) in pra_01.
Old header:

Starts: from states/pra01_pushstart.st run right RUN frames (push starts further right, up to the palace wall at
x 987), settle, then push left (go 1 / stop 2, stick (-80,0)) for C cycles, for C from the cycle where Mario
passes x 600 up to where he slides off the rock. A try is a random short input sequence (any stick direction and
strength or neutral, 1-6 frames per segment, up to 60 frames) with C-down pressed on every frame in turn.
Hit = Mario riding Lakilester behind the mirror (z < -1) in pra_01.
usage: python3 rev_local2.py <out.json> <minutes>"""
import json, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
RUNS = [30, 45, 60, 70, 80]
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/tr%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
    W['starts'] = [('topright', 'states/pra01_topright.st')]


def run(task):
    seed, seq = task
    e = W['e']
    random.seed(seed)
    key, sp = W['starts'][seed % len(W['starts'])]
    hits, top = [], 0
    chk = os.path.join(W['d'], 'chk.st')
    e.load(sp)
    e.step(0, 0, 0, 2)          # a save straight after a load writes nothing
    for f, (b, sx, sy) in enumerate(seq):
        e.save(chk)
        e.step(CD, sx, sy, 2)
        for i in range(25):
            if player(e)['action'] != 33:
                for n in npcs(e):
                    if n['id'] == -4: top = max(top, n['speed'])
            e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] == 33 and p['z'] > 1 and 400 < p['x'] < 1050 and p['y'] > -100 and tuple(where(e)[:2]) == (21, 0):
            hits.append({'start': key, 'cd_frame': f, 'end': (p['x'], p['y'], p['z'])})
        e.load(chk)
        e.step(b, sx, sy, 2)
    return key, seq, hits, top


def rand_seq():
    out = []
    while len(out) < 90:
        if random.random() < 0.3:
            st = (0, 0)
        else:
            st = stick_for(random.uniform(0, 360), random.choice((10, 16, 20, 30, 50, 80)))
        n = random.choice((1, 2, 4, 8, 15, 30))
        jump = random.random() < 0.1
        out += [((0x80 if jump and i < 8 else 0), st[0], st[1]) for i in range(n)]
    return out[:90]


if __name__ == '__main__':
    out_path, minutes = sys.argv[1], float(sys.argv[2])
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, hits, n, top = time.time(), [], 0, 0
    while time.time() - t0 < minutes * 60:
        tasks = [(random.randrange(10 ** 9), rand_seq()) for _ in range(64)]
        for key, seq, h, tp in pool.map(run, tasks, chunksize=4):
            n += 1
            top = max(top, tp)
            for x in h:
                x['seq'] = seq[:x['cd_frame'] + 1]
                hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('start', 'cd_frame', 'end')}), flush=True)
                json.dump(hits, open(out_path, 'w'))
        print('%d sequences, %d hits, top mount-delay speed %.1f [%.0fs]' % (n, len(hits), top, time.time() - t0), flush=True)
    pool.terminate()
