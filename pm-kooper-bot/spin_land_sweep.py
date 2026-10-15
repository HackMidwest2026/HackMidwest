"""Spin-jump landing sweep at one corner (default: nok_14 north corner of the bridge wall).

Jumping out of a spin keeps the spin speed (8.0) in curSpeed while airborne, and the
landing frame then moves Mario 8.0 + 0.547 = 8.547 units in one frame (normal running
is 4.547). This script uses that frame against the corner:

  1. from start points in the corner's wedge, spin (Z) toward the corner, jump (A) after
     k frames, steer in the air, and save the state on the last airborne frame before
     landing. Keep the ones that land close to the corner.
  2. from every kept pre-landing state, try every stick angle (1 degree steps, several
     strengths) for the landing frame and the frames after it, checking each frame for a
     clip (crossing a solid wall, reaching the goal floor or goal area, or taking the goal exit).

usage: ROOM=nok14 python3 spin_land_sweep.py <out_dir> [corner]
"""
import json, math, multiprocessing as mp, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rooms import ROOM, in_goal
from corner_sweep import stick_for, wedge_angles
ROM = os.environ.get('PM_ROM', os.path.join(HERE, 'pm-jp.z64'))
START = os.path.join(HERE, ROOM['start'])
SHM = os.environ.get('PM_TMP', '/dev/shm/pmbot')
A, Z = 0x0080, 0x0020
KEEP_DIST = float(os.environ.get('KEEP_DIST', '22'))   # keep pre-landing states this close to the corner
LAND_MAGS = tuple(int(m) for m in os.environ.get('LAND_MAGS', '80,50,25').split(','))
AFTER_FRAMES = 8

W = {}


def worker_init():
    from emu import Emu
    from explore_clip import load_walls
    d = os.path.join(SHM, 'l%d' % os.getpid())
    os.makedirs(d, exist_ok=True)
    W['e'] = Emu(ROM, d)
    W['walls'] = load_walls()
    W['dir'] = d
    W['n'] = 0


def check(p0, p1, e):
    """why this frame is a clip, or None"""
    from pm import COLLISION
    from explore_clip import crossed_wall
    floor = e.s16(COLLISION + 2)
    if floor in ROOM['goal_floors']:
        return 'on goal floor %d' % floor
    if in_goal(p1['x'], p1['z']):
        return 'inside goal area'
    w = crossed_wall(W['walls'], (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
    if w is not None:
        return 'crossed wall %d' % w
    return None


def gen(job):
    """poke mario to a start point, spin toward theta, jump at frame k, steer theta_air; save the last
    airborne state before landing if it ends near the corner."""
    from pm import PLAYER, PS_POS, player, GAME_MODE, GM_WORLD, game_status, ACTION_NAMES
    sx0, sz0, theta, k, theta_air, corner, out_dir = job
    e = W['e']
    base = base_state(sx0, sz0)
    out = []
    # pass 1: find the landing frame (skip start points that aren't on solid ground in bounds)
    e.load(base)
    from pm import COLLISION
    if e.s16(COLLISION + 2) < 0 or abs(player(e)['y'] - ROOM['floor_y'](sx0, sz0)) > 1:
        return out
    stick = stick_for(theta, 80)
    stick_air = stick_for(theta_air, 80) if theta_air is not None else (0, 0)
    airborne, land_f = False, None
    for f in range(40):
        b = Z if f == 0 else (A if f == k else 0)
        st = stick if f <= k else stick_air
        e.step(b, st[0], st[1], 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            return out
        p = player(e)
        if p['action'] in (3, 4, 5, 8):
            airborne = True
        elif airborne:
            land_f = f
            break
    if land_f is None or land_f < 2:
        return out
    # pass 2: replay to the frame before landing and save it if mario is near the corner
    e.load(base)
    for f in range(land_f):
        b = Z if f == 0 else (A if f == k else 0)
        st = stick if f <= k else stick_air
        e.step(b, st[0], st[1], 2)
    p = player(e)
    d = math.hypot(p['x'] - corner[0], p['z'] - corner[1])
    if d <= KEEP_DIST and p['action'] in (3, 4, 5, 8) and abs(p['speed'] - 8.0) < 0.01:
        out.append({'pos': (p['x'], p['y'], p['z']), 'dist': d, 'speed': p['speed'], 'land_f': land_f, 'corner': corner,
                    'inputs': {'start': (sx0, sz0), 'spin_deg': theta, 'jump_frame': k, 'air_deg': theta_air}})
    return out


def base_state(sx0, sz0):
    """start state with mario poked to (sx0, sz0), cached per worker"""
    from pm import PLAYER, PS_POS, game_status
    e = W['e']
    base = os.path.join(W['dir'], 'start_%d_%d.st' % (round(sx0), round(sz0)))
    if not os.path.exists(base):
        e.load(START)
        e.step(0, 0, 0, 2)
        if ROOM['disable_enemy_contact']:
            e.w8(game_status(e) + 0x74, 1)
        e.wf32(PLAYER + PS_POS, sx0); e.wf32(PLAYER + PS_POS + 4, ROOM['floor_y'](sx0, sz0)); e.wf32(PLAYER + PS_POS + 8, sz0)
        for i in range(6):
            e.step(0, 0, 0, 2)
        e.save(base)
    return base


def rebuild(pre):
    """replay a candidate's inputs to its last airborne frame and save it to the worker's scratch file"""
    from pm import player
    e = W['e']
    inp = pre['inputs']
    e.load(base_state(*inp['start']))
    stick = stick_for(inp['spin_deg'], 80)
    stick_air = stick_for(inp['air_deg'], 80) if inp['air_deg'] is not None else (0, 0)
    k = inp['jump_frame']
    for f in range(pre['land_f']):
        b = Z if f == 0 else (A if f == k else 0)
        st = stick if f <= k else stick_air
        e.step(b, st[0], st[1], 2)
    p = player(e)
    path = os.path.join(W['dir'], 'pre.st')
    e.save(path)
    return path, (p['x'], p['y'], p['z'])


def sweep(job):
    """from one pre-landing state, every landing-frame stick angle"""
    from pm import player, GAME_MODE, GM_WORLD, where
    pre, step = job
    e = W['e']
    hits, tries, max_land_move = [], 0, 0.0
    path, pos = rebuild(pre)
    if math.dist((pos[0], pos[2]), (pre['pos'][0], pre['pos'][2])) > 0.01:
        return [{'why': 'rebuild mismatch', 'pre': pre, 'got': pos}], 0, 0.0
    window = float(os.environ.get('LAND_WINDOW', '180'))
    to_corner = math.degrees(math.atan2(pre['corner'][1] - pos[2], pre['corner'][0] - pos[0]))
    degs = range(0, 360, step) if window >= 180 else \
        [round(to_corner + d) % 360 for d in range(-int(window), int(window) + 1, step)]
    after_modes = os.environ.get('AFTER_MODES', 'hold').split(',')
    for deg in degs:
      for mode in after_modes:
        for mag in LAND_MAGS:
            sx, sy = stick_for(deg, mag)
            e.load(path)
            p0 = player(e)
            landed = False
            for f in range(AFTER_FRAMES):
                if landed and mode == 'neutral':
                    e.step(0, 0, 0, 2)
                else:
                    e.step(0, sx, sy, 2)
                if e.s16(GAME_MODE) != GM_WORLD:
                    if e.s16(GAME_MODE) == 5 and tuple(where(e)[:2]) in [tuple(m) for m in ROOM.get('goal_maps', [])]:
                        hits.append({'deg': deg, 'mag': mag, 'mode': mode, 'frame': f, 'why': 'goal exit', 'pre': pre})
                    break
                p1 = player(e)
                if not landed and p1['action'] not in (3, 4, 5, 8):
                    landed = True
                    max_land_move = max(max_land_move, math.hypot(p1['x'] - p0['x'], p1['z'] - p0['z']))
                why = check(p0, p1, e)
                if why:
                    hits.append({'deg': deg, 'mag': mag, 'mode': mode, 'frame': f, 'why': why, 'pos': (p1['x'], p1['y'], p1['z']),
                                 'pre': pre})
                    break
                p0 = p1
            tries += 1
    return hits, tries, max_land_move


def env_list(name, default):
    return [float(v) for v in os.environ.get(name, default).split(',')]


def main():
    out_dir = sys.argv[1]
    cnames = sys.argv[2:] or ['north']
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=worker_init)
    t0 = time.time()
    radii = env_list('RADII', '20,30,40,55,70,90')
    angle_step = float(os.environ.get('ANGLE_STEP', '8'))
    offsets = env_list('OFFSETS', '-30,-20,-10,0,10,20,30')
    ks = [int(v) for v in env_list('JUMP_FRAMES', '1,2,3,4,6,8')]
    air_offsets = env_list('AIR_OFFSETS', '0,15,-15')

    # phase 1: spin-jump landings near each target point
    jobs = []
    for cname in cnames:
        c = ROOM['corners'][cname]
        corner = c['p']
        for r in radii:
            for a in wedge_angles(c, angle_step):
                sx0 = corner[0] + r * math.cos(math.radians(a))
                sz0 = corner[1] + r * math.sin(math.radians(a))
                toward = (a + 180) % 360
                for off in offsets:
                    theta = (toward + off) % 360
                    for k in ks:
                        airs = [(toward + ao) % 360 for ao in air_offsets] + [theta, None]
                        for air in airs:
                            jobs.append((sx0, sz0, theta, k, air, corner, out_dir))
    print('phase 1: %d spin-jump setups' % len(jobs), flush=True)
    pres = [p for r in pool.imap_unordered(gen, jobs, chunksize=8) for p in r]
    # one pre-landing state per 0.5-unit cell: near-duplicates add nothing
    seen, uniq = set(), []
    res = float(os.environ.get('DEDUP', '0.5'))
    for p in sorted(pres, key=lambda p: p['dist']):
        key = (round(p['pos'][0] / res), round(p['pos'][2] / res))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    print('phase 1 done in %.0fs: %d landings within %.0f units of a target point, %d distinct' % (
        time.time() - t0, len(pres), KEEP_DIST, len(uniq)), flush=True)
    json.dump(uniq, open(os.path.join(out_dir, 'prelanding.json'), 'w'))

    # phase 2: every landing-frame stick angle from each
    results = {'targets': cnames, 'prelanding': len(uniq), 'tries': 0, 'hits': [], 'max_land_move': 0}
    done = 0
    uniq = uniq[:int(os.environ.get('MAX_STATES', '1000000'))]
    results['prelanding'] = len(uniq)
    land_step = int(os.environ.get('LAND_STEP', '1'))
    for hits, tries, mlm in pool.imap_unordered(sweep, [(p, land_step) for p in uniq]):
        done += 1
        results['tries'] += tries
        results['hits'] += hits
        results['max_land_move'] = max(results['max_land_move'], mlm)
        for h in hits[:3]:
            print('HIT', json.dumps(h), flush=True)
        if done % 25 == 0 or done == len(uniq):
            print('phase 2: %d/%d states, %d tries, %d hits, biggest landing-frame move %.3f  [%.0fs]' % (
                done, len(uniq), results['tries'], len(results['hits']), results['max_land_move'], time.time() - t0),
                flush=True)
            json.dump(results, open(os.path.join(out_dir, 'results.json'), 'w'))
    print('done: %d tries, %d hits' % (results['tries'], len(results['hits'])), flush=True)
    json.dump(results, open(os.path.join(out_dir, 'results.json'), 'w'))
    pool.terminate()


if __name__ == '__main__':
    main()
