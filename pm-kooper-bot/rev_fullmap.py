"""Full map of the reflected side of pra_01 for the reverse mirror clip: for Mario standing at every (x, z) on a
5-unit grid (x 500..1000, z -215..-15), which forced Lakilester speeds S (20..300 step 5) make the C-down mount put
Mario on the real side? Mario is dropped at (x, 10, z) from states/pra01_top_start.st and must stay there; spots
where he can't stand are skipped. Appends one JSON line per x to the output (resumable after a restart).
usage: rev_fullmap.py <out.jsonl>"""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
SPEEDS = list(range(20, 301, 5))
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/fm%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(x):
    e = W['e']; out = {}
    for z in range(-215, -14, 5):
        e.load('states/pra01_top_start.st')
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 10.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(20): e.step(0, 0, 0, 2)
        p0 = player(e)
        if abs(p0['x'] - x) > 0.5 or abs(p0['z'] - z) > 0.5 or tuple(where(e)[:2]) != (21, 0): continue
        base = os.path.join(W['d'], 'b.st'); e.save(base)
        ok = []
        for S in SPEEDS:
            e.load(base); e.step(0, 0, 0, 2)
            e.step(CD, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            if tuple(where(e)[:2]) == (21, 0) and p['action'] == 33 and p['z'] > 1: ok.append(S)
        out[z] = {'y': round(p0['y'], 1), 'S': ok}
    return x, out
if __name__ == '__main__':
    path = sys.argv[1]
    done = set()
    if os.path.exists(path):
        for line in open(path): done.add(json.loads(line)['x'])
    xs = [x for x in range(500, 1001, 5) if x not in done]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    with open(path, 'a') as f:
        for x, out in pool.imap_unordered(run, xs):
            f.write(json.dumps({'x': x, 'z': out}) + '\n'); f.flush()
    print('done', len(done) + len(xs), 'columns')
    pool.terminate()
