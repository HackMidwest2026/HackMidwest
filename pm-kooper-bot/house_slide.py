"""low Blue House entry from a wall slide (mac_02): Mario against the house front at (-402, -134), hold up + slight
right (sx1, 80) to creep right along the wall, then on frame k switch to (sx2, sy2) and hold it. For each slide
strength, which switch frames k work? (the number of consecutive k is the timing window in frames)"""
import json, os, sys, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_stepgrid as S
from pm import *


def run(job):
    sx1, sx2, sy2 = job
    e = H.W['e']
    e.load(H.W['ref'])
    e.wf32(PLAYER + PS_POS, -402.0); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, -134.0)
    for i in range(4): e.step(0, 0, 0, 2)
    sp = os.path.join(H.W['d'], 'sl.st'); e.save(sp)
    ok = []
    for k in range(0, 90):
        e.load(sp)
        maxy, xs = 0, None
        for f in range(k + 30):
            st = (sx1, 80) if f < k else (sx2, sy2)
            e.step(0, st[0], st[1], 2)
            p = player(e)
            if f == k - 1: xs = round(p['x'], 3)
            maxy = max(maxy, p['y'])
            if H.inside(p):
                if maxy < 95: ok.append((k, xs))
                break
            if f >= k and p['z'] > -125: break
    return job, ok


if __name__ == '__main__':
    jobs = [(sx1, sx2, sy2) for sx1 in (6, 8, 10, 12, 16, 20) for sx2 in range(-16, 1) for sy2 in (80, 70, 60)]
    pool = mp.get_context('spawn').Pool(4, initializer=S.init)
    res = [r for r in pool.map(run, jobs, chunksize=2) if r[1]]
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d of %d (slide, switch-stick) combinations have a working switch frame' % (len(res), len(jobs)))
    for job, ok in sorted(res, key=lambda r: -len(r[1]))[:25]:
        print('slide sx %d, then stick (%d,%d): switch frames %s' % (job + ([k for k, x in ok],)), 'x at switch', [x for k, x in ok])
    pool.terminate()
