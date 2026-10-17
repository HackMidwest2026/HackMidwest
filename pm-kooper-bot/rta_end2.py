"""Search short cardinal-only endings around Lakilester's turnaround. Base: the rta_full route with T left frames after
the step-3 landing, then hold up (Mario at the z -145 wall). At frame t0 switch to dir1 for n1 frames, then dir2 for m2
frames, then C-down with dir2 held. Records Laki's frozen speed; candidates >= 115.5 are followed 60 frames to check
the clip. usage: rta_end2.py T t0_from t0_to out.json"""
import json, math, os, sys
from multiprocessing import Pool
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x0400
SD = {'L': stick_for(180, 80), 'D': stick_for(90, 80), 'R': stick_for(0, 80), 'U': stick_for(270, 80), 'N': (0, 0)}
U_ = SD['U']
def laki(e):
    return [n for n in npcs(e) if n['id'] == -4][0]
def base(e, T, w):
    e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); e.step(0, 0, 0, 2); fr = 0
    seq = [(0, U_)] * 10 + [(0, SD['R'])] * 10 + [(0, SD['D'])] * 6 + [(0x80 if i < 12 else 0, SD['D']) for i in range(26)] + [(0, (0, 0))] * 4
    for b, s in seq: e.step(b, *s, 2); fr += 1
    while player(e)['action'] != 9: e.step(0, *SD['L'], 2); fr += 1
    for i in range(8): e.step(0, 0, 0, 2); fr += 1
    for i in range(T): e.step(0, *SD['L'], 2); fr += 1
    for i in range(2): e.step(0, 0, 0, 2); fr += 1
    return fr
def job(a):
    T, t0 = a
    w = '/dev/shm/pmbot/re2_%d_%d' % (T, t0); e = Emu(os.environ['PM_ROM'], w)
    fr = base(e, T, w)
    while fr < t0: e.step(0, *U_, 2); fr += 1
    e.save(w + '/s.st'); out = []
    for d1 in 'LDRN':
        for n1 in range(1, 9):
            for d2 in 'LDURN':
                if d2 == d1 and n1 > 1: continue
                e.load(w + '/s.st'); e.step(0, *U_, 2)
                for i in range(n1): e.step(0, *SD[d1], 2)
                e.save(w + '/m.st')
                for m2 in range(0, 4):
                    e.load(w + '/m.st'); e.step(0, *SD[d1], 2) if False else None
                    for i in range(m2): e.step(0, *SD[d2], 2)
                    pb = player(e); e.step(CD, *SD[d2], 2); spd = laki(e)['speed']
                    r = dict(T=T, t0=t0, d1=d1, n1=n1, d2=d2, m2=m2, spd=round(spd, 3), m=(round(pb['x'], 2), round(pb['y'], 2), round(pb['z'], 2)))
                    if spd >= 115.5:
                        for i in range(60): e.step(0, 0, 0, 2)
                        r['clip'] = player(e)['z'] > 1
                    if spd > 100: out.append(r)
    return out
if __name__ == '__main__':
    T, a, b = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    with Pool(4, maxtasksperchild=1) as p: res = sum(p.map(job, [(T, t) for t in range(a, b + 1)], chunksize=1), [])
    json.dump(res, open(sys.argv[4], 'w'))
    best = sorted(res, key=lambda r: -r['spd'])[:15]
    for r in best: print(r)
    print('clips:', sum(1 for r in res if r.get('clip')))
