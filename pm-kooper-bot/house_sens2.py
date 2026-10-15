"""for the distinct wall-face landings reachable from the Go-Explore spin (jump started, then varied air stick),
count how many second jumps get Mario inside (house_spinsetup.second_jumps: 414 combinations)."""
import json, os, sys, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_spinsetup as S
from house_explore import BASES
from corner_sweep import stick_for
from pm import *
A_, Z_ = 0x80, 0x20
V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/house_wallface_approach.json')))


def inputs():
    out = []
    for b, deg, mag, n in V['seq']:
        sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
        for i in range(n):
            out.append(({'tap': A_ if i == 0 else 0, 'spin': Z_ if i == 0 else 0, 'hold': A_}.get(b, 0), sx, sy))
    return out


def run(job):
    spin_end, sx, sy, hold = job
    e = H.W['e']
    e.load(H.base(*BASES[V['bi']]))
    for b, x, y in inputs()[:spin_end + 1]:
        e.step(b, x, y, 2)
    air = False
    for f in range(45):
        st = (sx, sy) if f < 12 else (0, 0)
        e.step(A_ if f < hold else 0, st[0], st[1], 2)
        q = player(e)
        if q['action'] in (3, 4, 5, 8, 13):
            air = True
        elif air:
            if e.s16(COLLISION + 2) == 45 and q['y'] > 25:
                lp = os.path.join(H.W['d'], 'land.st'); e.save(lp)
                return {'job': job, 'land': (q['x'], q['y'], q['z']), 'ok': len(S.second_jumps(e, lp))}
            return None
    return None


if __name__ == '__main__':
    jobs = [(se, sx, sy, 12) for se in (33, 34) for sx in range(-40, 1, 4) for sy in range(-30, 11, 4)]
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    res = [r for r in pool.map(run, jobs, chunksize=2) if r]
    json.dump(res, open(sys.argv[1] if len(sys.argv) > 1 else 'house_sens2.json', 'w'))
    import collections
    print(len(res), 'landings; second-jump successes:', collections.Counter(r['ok'] for r in res).most_common())
    for r in sorted(res, key=lambda r: -r['ok'])[:10]:
        print(r)
    pool.terminate()
