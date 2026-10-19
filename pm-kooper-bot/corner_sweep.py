"""Exhaustive input sweep at the two corners of the bridge wall (collider 12, x = -100) in nok_14.

For every start position (Mario settled into the corner, or standing on a ring
20/40/80 units out inside the wedge), try every stick angle at several stick
strengths, with walk / spin (Z) / jump (A) / hammer (B) pressed on the first
frame, and hold the stick until Mario has had time to reach the corner.

A hit is any frame where Mario
  - stands on collider 14 (the floor across the bridge gap), or
  - is east of x = -100 with z between -100 and -20, or
  - moves through a solid wall taller than a step (same test as explore_clip.py).

usage: python3 corner_sweep.py <out_dir> [corner ...]      corners: north south
"""
import json, math, multiprocessing as mp, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROM = os.environ.get('PM_ROM', os.path.join(HERE, 'pm-jp.z64'))
sys.path.insert(0, HERE)
from rooms import ROOM, NAME as ROOM_NAME, in_goal
START = os.path.join(HERE, ROOM['start'])
SHM = os.environ.get('PM_TMP', '/dev/shm/pmbot')

A, B, Z = 0x0080, 0x0040, 0x0020
GOAL_FLOORS = ROOM['goal_floors']
RING_STEP = float(os.environ.get('RING_STEP', '10'))      # degrees between run-up start positions
ACT_STEP = int(os.environ.get('ACT_STEP', '2'))           # degrees between stick angles for run-up starts
MAGS = tuple(int(m) for m in os.environ.get('MAGS', '80,40,20,10').split(','))

CORNERS = ROOM['corners']


def wedge_angles(c, step):
    """angles (deg) from the corner pointing into the play area, between its two walls"""
    p = c['p']
    if c.get('wedge'):
        lo, hi = c['wedge']
        out, a = [], lo + step
        while a < hi - step / 2:
            out.append(a % 360)
            a += step
        return out
    a1 = math.degrees(math.atan2(c['walls'][0][1] - p[1], c['walls'][0][0] - p[0]))
    a2 = math.degrees(math.atan2(c['walls'][1][1] - p[1], c['walls'][1][0] - p[0]))
    # the play area is west of x = -100, i.e. the wedge containing angle 180
    lo, hi = sorted((a1 % 360, a2 % 360))
    if not (lo <= 180 <= hi):
        lo, hi = hi, lo + 360
    out, a = [], lo + step
    while a < hi - step / 2:
        out.append(a % 360)
        a += step
    return out


def stick_for(world_deg, mag):
    """stick (x, y) that moves mario toward world angle atan2(dz, dx); stick +y moves toward -z"""
    r = math.radians(world_deg)
    return int(round(mag * math.cos(r))), int(round(-mag * math.sin(r)))


# ---- worker ----
W = {}


def worker_init():
    sys.path.insert(0, HERE)
    from emu import Emu
    from explore_clip import load_walls
    d = os.path.join(SHM, 's%d' % os.getpid())
    os.makedirs(d, exist_ok=True)
    W['e'] = Emu(ROM, d)
    W['walls'] = load_walls()
    W['dir'] = d


def make_start(job):
    """poke mario to (x, z) on the y=0 floor, optionally walk him into the corner, save a state."""
    from pm import PLAYER, PS_POS, player, GAME_MODE
    name, x, z, settle_deg, out = job
    e = W['e']
    e.load(START)
    e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, ROOM['floor_y'](x, z)); e.wf32(PLAYER + PS_POS + 8, z)
    # debug "can't touch": enemies can't start battles (they never push mario anyway), so the
    # spiked goomba chasing mario doesn't end every attempt
    from pm import game_status
    if ROOM['disable_enemy_contact']:
        e.w8(game_status(e) + 0x74, 1)
    if settle_deg is not None:
        sx, sy = stick_for(settle_deg, 50)
        for i in range(40):
            e.step(0, sx, sy, 2)
    for i in range(6):
        e.step(0, 0, 0, 2)
    e.save(out)
    p = player(e)
    return name, out, (p['x'], p['y'], p['z']), e.s16(GAME_MODE)


def run_actions(job):
    from pm import player, GAME_MODE, GM_WORLD, COLLISION, where
    from explore_clip import crossed_wall
    state, actions, frames, expect = job
    e = W['e']
    hits, battles, maxx = [], 0, -1e9
    W['bad_loads'] = 0
    for act in actions:
        sx, sy, buttons = act
        e.load(state)
        p0 = player(e)
        if abs(p0['x'] - expect[0]) > 0.01 or abs(p0['z'] - expect[2]) > 0.01:
            e.load(state)
            p0 = player(e)
            if abs(p0['x'] - expect[0]) > 0.01 or abs(p0['z'] - expect[2]) > 0.01:
                W['bad_loads'] += 1
                continue
        for f in range(frames):
            e.step(buttons if f == 0 else 0, sx, sy, 2)
            if e.s16(GAME_MODE) != GM_WORLD:
                if e.s16(GAME_MODE) == 5 and tuple(where(e)[:2]) in [tuple(m) for m in ROOM.get('goal_maps', [])]:
                    p1 = player(e)
                    hits.append({'action': act, 'frame': f, 'why': 'map change', 'pos': (p1['x'], p1['y'], p1['z']),
                                 'floor': e.s16(COLLISION + 2)})
                else:
                    battles += 1
                break
            p1 = player(e)
            floor = e.s16(COLLISION + 2)
            maxx = max(maxx, p1['x'])
            why = None
            if floor in GOAL_FLOORS:
                why = 'on goal floor %d' % floor
            elif in_goal(p1['x'], p1['z']):
                why = 'inside goal area'
            else:
                w = crossed_wall(W['walls'], (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
                if w is not None:
                    why = 'crossed wall %d' % w
            if why:
                hits.append({'action': act, 'frame': f, 'why': why, 'pos': (p1['x'], p1['y'], p1['z']), 'floor': floor})
                break
            p0 = p1
    return hits, battles, maxx, len(actions) - W['bad_loads']


def main():
    out_dir = sys.argv[1]
    corners = sys.argv[2:] or list(CORNERS)
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=worker_init)

    # start positions
    jobs = []
    for cn in corners:
        c = CORNERS[cn]
        px, pz = c['p']
        angles = wedge_angles(c, RING_STEP)
        # settled into the corner, approaching from several directions
        for a in wedge_angles(c, 20):
            jobs.append(('%s settle from %.0f' % (cn, a), px + 30 * math.cos(math.radians(a)),
                         pz + 30 * math.sin(math.radians(a)), (a + 180) % 360, 'settle'))
        for r in (20, 40, 80):
            for a in angles:
                jobs.append(('%s r%d a%.0f' % (cn, r, a), px + r * math.cos(math.radians(a)),
                             pz + r * math.sin(math.radians(a)), None, 'ring%d' % r))
    starts = []
    for i, (name, x, z, settle, kind) in enumerate(jobs):
        starts.append((name, x, z, settle, os.path.join(out_dir, 'start%03d.st' % i), kind))
    made = pool.map(make_start, [(n, x, z, s, o) for n, x, z, s, o, k in starts])
    print('made %d start states' % len(made), flush=True)

    # actions: every angle, 4 stick strengths, 4 first-frame buttons
    res_path = os.path.join(out_dir, 'results.json')
    results = json.load(open(res_path)) if os.path.exists(res_path) else {'starts': [], 'hits': []}
    # keep starts that already ran cleanly; redo the ones that were mostly battles
    results['starts'] = [s for s in results['starts'] if s['battles'] <= 0.05 * s['tries']]
    done_names = {s['name'] for s in results['starts']}
    t0 = time.time()
    total = 0
    for (name, x, z, settle, path, kind), (_, _, pos, mode) in zip(starts, made):
        if mode != 4:
            print('skip', name, 'not in world mode', flush=True)
            continue
        if in_goal(pos[0], pos[2]):
            print('skip', name, 'starts past the wall already', flush=True)
            continue
        if name in done_names:
            continue
        step = 1 if kind == 'settle' else ACT_STEP
        acts = []
        for deg in range(0, 360, step):
            for mag in MAGS:
                sx, sy = stick_for(deg, mag)
                for b in (0, Z, A, B):
                    acts.append((sx, sy, b))
        frames = 25 if kind in ('settle', 'ring20') else (32 if kind == 'ring40' else 45)
        chunks = [acts[i::16] for i in range(16)]
        res = pool.map(run_actions, [(path, ch, frames, pos) for ch in chunks])
        hits = [h for r in res for h in r[0]]
        battles = sum(r[1] for r in res)
        maxx = max(r[2] for r in res)
        n = sum(r[3] for r in res)
        total += n
        for h in hits:
            h['start'] = name
        results['hits'] += hits
        results['starts'].append({'name': name, 'pos': pos, 'tries': n, 'battles': battles, 'maxx': maxx, 'hits': len(hits)})
        print('%-28s at (%.1f,%.1f) tries %d battles %d max x %.2f hits %d  [%d total, %.0fs]' % (
            name, pos[0], pos[2], n, battles, maxx, len(hits), total, time.time() - t0), flush=True)
        for h in hits[:5]:
            print('   HIT', h, flush=True)
        json.dump(results, open(os.path.join(out_dir, 'results.json'), 'w'))
    print('done: %d tries, %d hits' % (total, len(results['hits'])), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
