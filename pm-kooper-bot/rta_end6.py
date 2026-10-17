"""Jump endings: route start W=2, D1=4, N=22, then left to the forced drop, left T, stand; hold up u frames; stand
until X; press A at X holding d1 for n1 frames then d2; at each frame c in Laki's spike window (Mario on the ground)
try C-down with d2. usage: rta_end6.py out.json"""
import json, os, sys
from multiprocessing import Pool
from rta_end5 import *
def job(a):
    T, u = a
    w = '/dev/shm/pmbot/re6_%d_%d' % a; e = Emu(os.environ['PM_ROM'], w)
    fr = run_base(e, 2, 4, 22, T)
    for i in range(u): e.step(0, *U_, 2); fr += 1
    e.save(w + '/b.st'); f0 = fr
    ta = None
    for i in range(200):
        ix = e.u32(IDX); e.step(0, 0, 0, 2); fr += 1
        if e.u32(IDX) != ix: ta = fr; break
    out = []
    for X in range(max(f0, ta - 24), ta + 3):
        for d1 in 'LUD':
            for n1 in (0, 1, 2, 3, 4, 6, 8, 10):
                for d2 in 'LUN':
                    if n1 == 0 and d1 != 'L': continue
                    e.load(w + '/b.st'); g = f0
                    while g < X: e.step(0, 0, 0, 2); g += 1
                    k = 0
                    while g < ta + 9:
                        s = SD[d1] if k < n1 else SD[d2]
                        if g >= X:
                            p = player(e)
                            if p['action'] in (0, 1, 2) and k > 3:
                                e.save(w + '/c.st')
                                e.step(CD, *s, 2); spd = laki(e)['speed']
                                r = dict(T=T, u=u, ta=ta, X=X, d1=d1, n1=n1, d2=d2, c=g, spd=round(spd, 3), m=(round(p['x'], 2), round(p['y'], 2), round(p['z'], 2)))
                                if spd >= 115.6:
                                    for i in range(60): e.step(0, 0, 0, 2)
                                    r['clip'] = player(e)['z'] > 1
                                if spd > 113: out.append(r)
                                e.load(w + '/c.st')
                        e.step(0x80 if k < 8 else 0, *s, 2); g += 1; k += 1
    return out
if __name__ == '__main__':
    args = [(T, u) for T in (4, 5, 6) for u in (0, 8, 16)]
    with Pool(4, maxtasksperchild=1) as p: res = sum(p.map(job, args, chunksize=1), [])
    json.dump(res, open(sys.argv[1], 'w'))
    for r in sorted(res, key=lambda r: -r['spd'])[:15]: print(r)
    cl = [r for r in res if r.get('clip')]
    print('clips:', len(cl)); [print(r) for r in cl[:40]]
