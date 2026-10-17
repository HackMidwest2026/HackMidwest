"""Early-route variants: wait W frames in the very top-right corner, down D1, A + down N, then the T=5 ending (left to
the forced drop, left 5, stand on step 3, hold up from X, C-down with D at c, P frames of D before it). The route
start changes Laki's flight phase and so where he turns around. Also tries a jump on step 3 instead of the up slide:
from the step-3 stand, hold up from X; at frame J press A (stick up) and land against the wall.
usage: rta_end5.py out.json"""
import json, os, sys
from multiprocessing import Pool
from rta_end2 import *
HIST, IDX, PTR = 0x8010CEF8, 0x8010D178, 0x8010D17C
def run_base(e, W, D1, N, T):
    e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); e.step(0, 0, 0, 2); fr = 0
    seq = [(0, U_)] * 10 + [(0, SD['R'])] * 10 + [(0, (0, 0))] * W + [(0, SD['D'])] * D1 + [(0x80 if i < 12 else 0, SD['D']) for i in range(N)] + [(0, (0, 0))] * 4
    for b, s in seq: e.step(b, *s, 2); fr += 1
    while player(e)['action'] != 9: e.step(0, *SD['L'], 2); fr += 1
    for i in range(8): e.step(0, 0, 0, 2); fr += 1
    for i in range(T): e.step(0, *SD['L'], 2); fr += 1
    for i in range(2): e.step(0, 0, 0, 2); fr += 1
    return fr
def job(a):
    W, D1, N = a
    w = '/dev/shm/pmbot/re5_%d_%d_%d' % a; e = Emu(os.environ['PM_ROM'], w)
    fr = run_base(e, W, D1, N, 5); p0 = player(e)
    e.save(w + '/b.st'); f0 = fr
    # find Laki's arrival (history index changes) while standing
    ta = None
    for i in range(200):
        ix = e.u32(IDX); e.step(0, 0, 0, 2); fr += 1
        if e.u32(IDX) != ix: ta = fr; break
    out = []
    if ta is None: return out
    for X in range(max(f0, ta - 22), ta + 2):
        for c in range(ta + 1, ta + 10):
            if c <= X: continue
            for D in 'UL':
                for P in (0, 1):
                    if c - P < X: continue
                    e.load(w + '/b.st'); g = f0
                    while g < X: e.step(0, 0, 0, 2); g += 1
                    while g < c - P: e.step(0, *U_, 2); g += 1
                    for i in range(P): e.step(0, *SD[D], 2)
                    pb = player(e); e.step(CD, *SD[D], 2); spd = laki(e)['speed']
                    r = dict(W=W, D1=D1, N=N, ta=ta, X=X, c=c, D=D, P=P, spd=round(spd, 3), m=(round(pb['x'], 2), round(pb['y'], 2), round(pb['z'], 2)), act=pb['action'], kind='up')
                    if spd >= 115.6 and pb['action'] in (0, 1, 2):
                        for i in range(60): e.step(0, 0, 0, 2)
                        r['clip'] = player(e)['z'] > 1
                    if spd > 113: out.append(r)
    return out
if __name__ == '__main__':
    args = [(W, D1, N) for W in range(int(os.environ.get('W0', 0)), int(os.environ.get('W1', 6))) for D1 in (4, 6, 8) for N in (22, 26, 30, 34)] if not os.environ.get('WONLY') else [(W, 4, 22) for W in range(int(os.environ['W0']), int(os.environ['W1']))]
    with Pool(4, maxtasksperchild=1) as p: res = sum(p.map(job, args, chunksize=1), [])
    json.dump(res, open(sys.argv[1], 'w'))
    g = [r for r in res if r['act'] in (0, 1, 2)]
    for r in sorted(g, key=lambda r: -r['spd'])[:15]: print(r)
    cl = [r for r in res if r.get('clip')]
    print('clips:', len(cl)); [print(r) for r in cl[:40]]
