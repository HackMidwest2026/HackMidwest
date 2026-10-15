"""how deep do spin-jump landings get into the bridge wall? replay the pre-landing states closest to the
north corner at every stick angle and record the largest x reached while 'beside' the bridge wall
(-100 < z < -20). x = -113 is the normal resting distance (Mario's radius is 13)."""
import json, math, os, sys, multiprocessing as mp
os.environ.setdefault('ROOM', 'nok14')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spin_land_sweep as S
from corner_sweep import stick_for


def depth(pre):
    from pm import player, GAME_MODE, GM_WORLD
    e = S.W['e']
    path, pos = S.rebuild(pre)
    best = (-1e9, None)
    for deg in range(0, 360, 1):
        sx, sy = stick_for(deg, 80)
        e.load(path)
        for f in range(S.AFTER_FRAMES):
            e.step(0, sx, sy, 2)
            if e.s16(GAME_MODE) != GM_WORLD:
                break
            p = player(e)
            if -100 < p['z'] < -20 and p['x'] > best[0]:
                best = (p['x'], {'deg': deg, 'frame': f, 'pos': (p['x'], p['y'], p['z'])})
    return best, pre


if __name__ == '__main__':
    pres = json.load(open(sys.argv[1]))[:int(sys.argv[2]) if len(sys.argv) > 2 else 120]
    pool = mp.get_context('spawn').Pool(4, initializer=S.worker_init)
    res = pool.map(depth, pres)
    res.sort(key=lambda r: -r[0][0])
    print('deepest x beside the bridge wall (wall at x = -100, normal resting x = -113):')
    for (x, info), pre in res[:10]:
        print('  x = %.3f  stick %s  from pre-landing %s  inputs %s' % (x, info and info['deg'], [round(v, 1) for v in pre['pos']], pre['inputs']))
    json.dump([{'x': r[0][0], 'info': r[0][1], 'pre': r[1]} for r in res], open(sys.argv[1].replace('prelanding', 'depth'), 'w'))
    pool.terminate()
