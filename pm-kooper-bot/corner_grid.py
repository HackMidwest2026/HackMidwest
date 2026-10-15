"""Fine grid of spin-jump landings at the nok_14 north corner.

Takes one real pre-landing state (airborne, curSpeed 8.0 from a spin) from the spin-land sweep, then
for every (x, z) on a grid around the corner rewrites only Mario's x and z and plays the landing frame
with each stick angle in a window around the direction to the corner. Records where Mario ends up
after the boosted landing frame, and flags any clip (crossing a wall, standing on the gap floor,
or being east of x = -100 beside the gap).

usage: python3 corner_grid.py <out_dir> [step]
"""
import json, math, multiprocessing as mp, os, sys, time
os.environ.setdefault('ROOM', 'nok14')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spin_land_sweep as S
from corner_sweep import stick_for

CORNER = (-100.0, -100.0)
X0, X1, Z0, Z1 = -122.0, -104.0, -114.0, -94.0
# stick directions toward the wall only: from straight up (away from the camera, -z) clockwise through
# right (+x, toward the bridge wall) to straight down (+z). world angle atan2(dz, dx): -90 .. 0 .. +90
ANGLES = list(range(-90, 91, 2))
MAGS, AFTER = (80, 40), 6
PRE_JSON = '/tmp/claude-0/pm/runs/spinland_north/prelanding.json'


def init():
    S.worker_init()
    pres = json.load(open(PRE_JSON))
    near = [p for p in pres if -112 < p['pos'][2] < -95 and -120 < p['pos'][0] < -104]
    pre = sorted(near, key=lambda p: p['dist'])[0]
    path, pos = S.rebuild(pre)
    S.W['pre_path'], S.W['pre_pos'], S.W['pre'] = path, pos, pre


def run_point(pt):
    from pm import player, PLAYER, PS_POS, GAME_MODE, GM_WORLD
    x, z = pt
    e = S.W['e']
    out = {'x': x, 'z': z, 'hits': [], 'land': []}
    for a in ANGLES:
        deg = a % 360
        for mag in MAGS:
            sx, sy = stick_for(deg, mag)
            e.load(S.W['pre_path'])
            e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 8, z)
            p0 = {'x': x, 'y': S.W['pre_pos'][1], 'z': z}
            landed = False
            for f in range(AFTER):
                e.step(0, sx, sy, 2)
                if e.s16(GAME_MODE) != GM_WORLD:
                    break
                p1 = player(e)
                why = S.check(p0, p1, e)
                if not landed and p1['action'] not in (3, 4, 5, 8):
                    landed = True
                    out['land'].append((deg, mag, round(p1['x'], 3), round(p1['z'], 3)))
                if why:
                    out['hits'].append({'deg': deg, 'mag': mag, 'frame': f, 'why': why, 'pos': (p1['x'], p1['y'], p1['z'])})
                    break
                p0 = p1
    return out


def main():
    out_dir = sys.argv[1]
    step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    os.makedirs(out_dir, exist_ok=True)
    pts = []
    x = X0
    while x <= X1 + 1e-9:
        z = Z0
        while z <= Z1 + 1e-9:
            pts.append((round(x, 3), round(z, 3)))
            z += step
        x += step
    print('%d grid points, %d angles x %d strengths each' % (len(pts), len(ANGLES), len(MAGS)), flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, res, nh = time.time(), [], 0
    for i, r in enumerate(pool.imap_unordered(run_point, pts, chunksize=4)):
        res.append(r)
        nh += len(r['hits'])
        for h in r['hits'][:2]:
            print('HIT at grid (%.2f, %.2f):' % (r['x'], r['z']), json.dumps(h), flush=True)
        if (i + 1) % 200 == 0:
            print('%d/%d points, %d hits  [%.0fs]' % (i + 1, len(pts), nh, time.time() - t0), flush=True)
            json.dump(res, open(os.path.join(out_dir, 'grid.json'), 'w'))
    json.dump(res, open(os.path.join(out_dir, 'grid.json'), 'w'))
    print('done: %d points, %d hits' % (len(pts), nh), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
