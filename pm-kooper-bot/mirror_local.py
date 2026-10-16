"""pra_02 mirror clip, local search at the right pillar.

Start: the stop-and-go push from the left-pillar setup, stopped at Mario x >= XSTOP (several), so Mario and
Lakilester are at the right pillar against the mirror. A try is a random short input sequence (gentle/medium
stick in any direction, or neutral, 1-6 frames per segment, up to 40 frames), and C-down is pressed on every frame
of it in turn. Hit = Mario riding Lakilester on the far side of the mirror (z < 0) within the room.
usage: python3 mirror_local.py <out.json> <minutes>"""
import json, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
XSTOPS = [700.0, 708.0, 712.0, 716.0, 718.0, 721.0, 724.0, 727.0]
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ml%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    e = Emu(os.environ['PM_ROM'], d)
    W['e'], W['d'], W['starts'] = e, d, []
    for xs in XSTOPS:
        e.load('states/pra02_leftpillar.st')
        for c in range(250):
            if player(e)['x'] >= xs: break
            e.step(0, 80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        sp = os.path.join(d, 'start_%d.st' % xs)
        e.save(sp)
        W['starts'].append(sp)


def run(task):
    si, seq = task
    e = W['e']
    hits = []
    chk = os.path.join(W['d'], 'chk.st')
    e.load(W['starts'][si])
    e.step(0, 0, 0, 2)          # a save straight after a load writes nothing
    for f, (sx, sy) in enumerate(seq):
        e.save(chk)
        e.step(CD, sx, sy, 2)
        for i in range(25): e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] == 33 and p['z'] < -1 and 0 < p['x'] < 1000 and p['y'] > -50:
            hits.append({'start': XSTOPS[si], 'cd_frame': f, 'end': (p['x'], p['y'], p['z'])})
        e.load(chk)
        e.step(0, sx, sy, 2)
    return task, hits


def rand_seq():
    out = []
    while len(out) < 40:
        if random.random() < 0.3:
            st = (0, 0)
        else:
            st = stick_for(random.uniform(0, 360), random.choice((8, 10, 12, 16, 20, 30, 50, 80)))
        out += [st] * random.choice((1, 1, 2, 3, 4, 6))
    return out[:40]


if __name__ == '__main__':
    out_path, minutes = sys.argv[1], float(sys.argv[2])
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, hits, n = time.time(), [], 0
    while time.time() - t0 < minutes * 60:
        tasks = [(random.randrange(len(XSTOPS)), rand_seq()) for _ in range(64)]
        for (si, seq), h in pool.map(run, tasks, chunksize=4):
            n += 1
            for x in h:
                x['seq'] = seq[:x['cd_frame'] + 1]
                hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('start', 'cd_frame', 'end')}), flush=True)
                json.dump(hits, open(out_path, 'w'))
        print('%d sequences, %d hits [%.0fs]' % (n, len(hits), time.time() - t0), flush=True)
    pool.terminate()
