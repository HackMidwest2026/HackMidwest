"""Wait on the rail: rta_end2 base with T=4 (x 893.7 on step 3), hold up Uh frames (onto the rail behind the stairs),
stand until X, then dir1 n1 frames, dir2 m2 frames, C-down with dir2 at frame c = X+n1+m2 in 117..124.
usage: rta_end4.py out.json"""
import json, os, sys
from multiprocessing import Pool
from rta_end2 import *
def job(Uh):
    w = '/dev/shm/pmbot/re4_%d' % Uh; e = Emu(os.environ['PM_ROM'], w)
    fr = base(e, int(os.environ.get('T', 4)), w)
    for i in range(Uh): e.step(0, *U_, 2); fr += 1
    p = player(e); stand = (round(p['x'], 2), round(p['y'], 2), round(p['z'], 2))
    out = []
    while fr < 104: e.step(0, 0, 0, 2); fr += 1
    for X in range(104, 122):
        e.save(w + '/s.st')
        for d1 in 'LDR':
            for n1 in range(1, 10):
                for d2 in 'LDUN':
                    for m2 in range(0, 4):
                        c = X + n1 + m2
                        if not 117 <= c <= 124 or (d2 == d1 and m2 > 0): continue
                        e.load(w + '/s.st')
                        for i in range(n1): e.step(0, *SD[d1], 2)
                        for i in range(m2): e.step(0, *SD[d2], 2)
                        pb = player(e); e.step(CD, *SD[d2], 2); spd = laki(e)['speed']
                        r = dict(Uh=Uh, stand=stand, X=X, d1=d1, n1=n1, d2=d2, m2=m2, c=c, spd=round(spd, 3), m=(round(pb['x'], 2), round(pb['y'], 2), round(pb['z'], 2)), act=pb['action'])
                        if spd >= 115.6 and pb['action'] in (0, 1, 2):
                            for i in range(60): e.step(0, 0, 0, 2)
                            r['clip'] = player(e)['z'] > 1
                        if spd > 112: out.append(r)
        e.load(w + '/s.st'); e.step(0, 0, 0, 2); fr += 1
    return out
if __name__ == '__main__':
    with Pool(4, maxtasksperchild=1) as p: res = sum(p.map(job, range(12, 24), chunksize=1), [])
    json.dump(res, open(sys.argv[1], 'w'))
    for r in sorted([r for r in res if r['act'] in (0, 1, 2)], key=lambda r: -r['spd'])[:12]: print(r)
    cl = [r for r in res if r.get('clip')]
    print('clips:', len(cl)); [print(r) for r in cl[:30]]
