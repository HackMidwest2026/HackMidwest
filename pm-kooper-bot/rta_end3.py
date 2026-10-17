"""Delayed up: rta_end2 base with T left frames, then stand still on step 3 and start holding up at frame X (Mario walks
up to the z -145 wall and slides down the riser late, near Laki's arrival). C-down at frame c with stick D on that frame
(optionally P frames of D before it). usage: rta_end3.py T out.json"""
import json, os, sys, itertools
from multiprocessing import Pool
from rta_end2 import *
def job(a):
    T, X = a
    w = '/dev/shm/pmbot/re3_%d_%d' % (T, X); e = Emu(os.environ['PM_ROM'], w)
    fr = base(e, T, w)
    while fr < X: e.step(0, 0, 0, 2); fr += 1
    e.save(w + '/s.st'); out = []
    for c in range(max(X, 110), 126):
        for D in 'ULDN':
            for P in (0, 1, 2):
                if c - P < X: continue
                e.load(w + '/s.st'); g = X
                while g < c - P: e.step(0, *U_, 2); g += 1
                for i in range(P): e.step(0, *SD[D], 2)
                pb = player(e); e.step(CD, *SD[D], 2); spd = laki(e)['speed']
                r = dict(T=T, X=X, c=c, D=D, P=P, spd=round(spd, 3), m=(round(pb['x'], 2), round(pb['y'], 2), round(pb['z'], 2)))
                if spd >= 115.5:
                    for i in range(60): e.step(0, 0, 0, 2)
                    r['clip'] = player(e)['z'] > 1
                if spd > 110: out.append(r)
    return out
if __name__ == '__main__':
    T = int(sys.argv[1])
    with Pool(4, maxtasksperchild=1) as p: res = sum(p.map(job, [(T, x) for x in range(90, 122)], chunksize=1), [])
    json.dump(res, open(sys.argv[2], 'w'))
    for r in sorted(res, key=lambda r: -r['spd'])[:12]: print(r)
    print('clips:', [r for r in res if r.get('clip')])
