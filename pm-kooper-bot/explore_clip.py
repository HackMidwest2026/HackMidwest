"""Go-Explore search for wall clips in nok_14 without loading zone storage.

Each try loads an archived state and plays a short random input segment
(stick direction, plus nothing / A jump / Z spin / B hammer) for a few frames.
Every frame, Mario's movement is tested against every solid wall triangle of
the room: if the segment from his previous position to his new one crosses a
wall whose height overlaps his body, that is a clip and is reported with the
full input path that produced it.

usage: python3 explore_clip.py <run_dir> [hours]
"""
import gzip, json, math, multiprocessing as mp, os, pickle, random, sys, time, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROM = os.environ.get('PM_ROM', os.path.join(HERE, 'pm-jp.z64'))
sys.path.insert(0, HERE)
from rooms import ROOM, in_goal
START = os.path.join(HERE, ROOM['start'])
COLL = os.path.join(HERE, ROOM['collision'])
SHM = os.environ.get('PM_TMP', '/dev/shm/pmbot')

A, B, Z = 0x0080, 0x0040, 0x0020
BUTTON_SETS = [0, 0, 0, A, Z, Z, B, A | Z]
SEG_LENS = [1, 2, 3, 4, 6, 8, 12]
MAGS = [80, 80, 60, 40, 20, 10]


def load_walls():
    d = json.load(open(COLL))
    walls = []
    for c in d['colliders']:
        if c['flags'] & 0x10000:            # not solid for the player
            continue
        for t in c['tris']:
            if abs(t['n'][1]) > 0.5:
                continue
            pts = [(v[0], v[2]) for v in t['v']]
            a, b = max(((p, q) for p in pts for q in pts), key=lambda pq: math.dist(*pq))
            if math.dist(a, b) < 0.5:
                continue
            ys = [v[1] for v in t['v']]
            walls.append((c['id'], a, b, min(ys), max(ys)))
    return walls


def seg_cross(p, q, a, b):
    def orient(o, s, t):
        return (s[0] - o[0]) * (t[1] - o[1]) - (s[1] - o[1]) * (t[0] - o[0])
    d1, d2 = orient(a, b, p), orient(a, b, q)
    d3, d4 = orient(p, q, a), orient(p, q, b)
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0) and d1 != 0 and d2 != 0


def crossed_wall(walls, p, q, y):
    if math.dist(p, q) < 1e-4:
        return None
    for cid, a, b, ymin, ymax in walls:
        # ignore steps mario can walk up: the wall has to reach well above his feet
        if ymin < y + 10 and ymax > y + 25 and seg_cross(p, q, a, b):
            return cid
    return None


def random_action(rng):
    a = math.radians(rng.uniform(0, 360))
    m = rng.choice(MAGS)
    if rng.random() < 0.08:
        m = 0
    return (int(round(m * math.cos(a))), int(round(m * math.sin(a))), rng.choice(BUTTON_SETS), rng.choice(SEG_LENS))


def cell_of(s):
    return (int(s['x'] // 10), int(s['z'] // 10), int(s['y'] // 25), s['action'])


# only keep spots in the right half of the path (east of the ledge) that are close to a solid wall
FOCUS_MIN_X = ROOM['focus_min_x']
FOCUS_BOX = ROOM.get('focus_box')          # optional (x0, x1, z0, z1): only keep cells inside it
FOCUS_WALL_DIST = 40
MAX_CELLS = 25000


# ---- state blobs ----
def read_state(path):
    with gzip.open(path, 'rb') as f:
        return np.frombuffer(f.read(), dtype=np.uint8)


def write_state(path, raw):
    with gzip.open(path, 'wb', compresslevel=0) as f:
        f.write(raw.tobytes())


def to_blob(raw, base):
    return zlib.compress(np.bitwise_xor(raw, base).tobytes(), 1)


def from_blob(blob, base):
    return np.bitwise_xor(np.frombuffer(zlib.decompress(blob), dtype=np.uint8), base)


# ---- worker ----
W = {}


def worker_init():
    sys.path.insert(0, HERE)
    from emu import Emu
    d = os.path.join(SHM, 'c%d' % os.getpid())
    os.makedirs(d, exist_ok=True)
    W['e'] = Emu(ROM, d)
    W['dir'] = d
    W['base'] = read_state(START)
    W['walls'] = load_walls()


def worker_try(job):
    from pm import player, GAME_MODE, GM_WORLD, COLLISION
    blob, action = job
    e = W['e']
    src, dst = os.path.join(W['dir'], 'src.st'), os.path.join(W['dir'], 'dst.st')
    write_state(src, from_blob(blob, W['base']))
    e.load(src)
    sx, sy, buttons, n = action
    p0 = player(e)
    clip = None
    trace = []
    for f in range(n):
        # buttons are pressed on the first frame of the segment only, so repeated tries can chain them
        e.step(buttons if f == 0 else (buttons & A), sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            if e.s16(GAME_MODE) == 5:     # took an exit: only exits listed as goals count
                from pm import where
                dest = where(e)
                if tuple(dest[:2]) in [tuple(m) for m in ROOM.get('goal_maps', [])]:
                    clip = {'wall': -1, 'frame': f, 'why': 'exit to %s' % (dest,), 'from': (p0['x'], p0['y'], p0['z']), 'action': -1}
                    return {'res': 'exit', 'clip_only': clip, 'trace': trace}
                return {'res': 'other_exit'}
            return {'res': 'battle'}
        p1 = player(e)
        trace.append((p1['x'], p1['y'], p1['z'], p1['action']))
        w = crossed_wall(W['walls'], (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
        if w is None and in_goal(p1['x'], p1['z']):
            w = -2
        if w is not None and clip is None:
            clip = {'wall': w, 'frame': f, 'from': (p0['x'], p0['y'], p0['z']), 'to': (p1['x'], p1['y'], p1['z']),
                    'action': p1['action']}
        p0 = p1
    e.save(dst)
    s = {k: p0[k] for k in ('x', 'y', 'z', 'action')}
    s['floor'] = e.s16(COLLISION + 2)
    return {'res': 'ok', 'state': s, 'clip': clip, 'trace': trace, 'blob': to_blob(read_state(dst), W['base'])}


def main():
    run_dir = sys.argv[1]
    hours = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    os.makedirs(run_dir, exist_ok=True)
    arch_path = os.path.join(run_dir, 'archive.pkl')
    rng = random.Random(int(time.time()))
    walls = load_walls()
    if os.path.exists(arch_path):
        A_ = pickle.load(open(arch_path, 'rb'))
    else:
        base = read_state(START)
        s0 = dict(ROOM['start_pos'])
        A_ = {'cells': {cell_of(s0): {'blob': to_blob(base, base), 'path': [], 'chosen': 0, 'pos': s0}},
              'tries': 0, 'clips': [], 'results': {}}

    def wall_dist(s):
        best = 1e9
        for _, a, b, ymin, ymax in walls:
            if not (ymin < s['y'] + 30 and ymax > s['y'] + 5):
                continue
            ax, az = a; bx, bz = b
            vx, vz = bx - ax, bz - az
            L = vx * vx + vz * vz
            t = max(0, min(1, ((s['x'] - ax) * vx + (s['z'] - az) * vz) / L))
            best = min(best, math.hypot(s['x'] - ax - t * vx, s['z'] - az - t * vz))
        return best

    pool = mp.get_context('spawn').Pool(4, initializer=worker_init)
    deadline = time.time() + hours * 3600
    t0, tries0, last_print, last_save = time.time(), A_['tries'], time.time(), time.time()
    pending = []
    while time.time() < deadline:
        while len(pending) < 16:
            keys = list(A_['cells'].keys())
            # prefer cells tried less often and cells close to a wall
            weights = [(1.0 / math.sqrt(1 + A_['cells'][k]['chosen'])) *
                       (3.0 if A_['cells'][k].get('wd', 99) < 20 else 1.0) for k in keys]
            k = rng.choices(keys, weights)[0]
            c = A_['cells'][k]
            c['chosen'] += 1
            act = random_action(rng)
            pending.append((k, act, pool.apply_async(worker_try, ((c['blob'], act),))))
        done = [p for p in pending if p[2].ready()]
        if not done:
            time.sleep(0.003)
            continue
        for p in done:
            pending.remove(p)
            k, act, r = p[0], p[1], p[2].get()
            A_['tries'] += 1
            A_['results'][r['res']] = A_['results'].get(r['res'], 0) + 1
            parent = A_['cells'][k]
            if r['res'] == 'exit':
                A_['clips'].append({'path': parent['path'] + [act], 'clip': r['clip_only'], 'trace': r['trace']})
                print('EXIT TAKEN (possible clip):', r['clip_only'], 'path len', len(parent['path']) + 1, flush=True)
                continue
            if r['res'] != 'ok':
                continue
            path = parent['path'] + [act]
            if r['clip']:
                A_['clips'].append({'path': path, 'clip': r['clip'], 'trace': r['trace'], 'blob': r['blob']})
                print('CLIP through wall %d:' % r['clip']['wall'], r['clip'], 'path len', len(path), flush=True)
            wd = wall_dist(r['state'])
            if r['state']['x'] < FOCUS_MIN_X or wd > FOCUS_WALL_DIST:
                continue
            if FOCUS_BOX and not (FOCUS_BOX[0] < r['state']['x'] < FOCUS_BOX[1] and FOCUS_BOX[2] < r['state']['z'] < FOCUS_BOX[3]):
                continue
            nc = cell_of(r['state'])
            old = A_['cells'].get(nc)
            if old is None and len(A_['cells']) >= MAX_CELLS:
                continue
            if old is None or len(path) < len(old['path']):
                A_['cells'][nc] = {'blob': r['blob'], 'path': path, 'chosen': old['chosen'] if old else 0,
                                   'pos': r['state'], 'wd': wd}
        now = time.time()
        if now - last_print > 60:
            last_print = now
            xs = [c['pos']['x'] for c in A_['cells'].values()]
            print('%.0fs tries %d (%.1f/s) cells %d x %.0f..%.0f results %s clips %d' % (
                now - t0, A_['tries'], (A_['tries'] - tries0) / (now - t0), len(A_['cells']), min(xs), max(xs),
                A_['results'], len(A_['clips'])), flush=True)
        if now - last_save > 300:
            last_save = now
            with open(arch_path + '.tmp', 'wb') as f:
                pickle.dump(A_, f)
            os.replace(arch_path + '.tmp', arch_path)
    with open(arch_path + '.tmp', 'wb') as f:
        pickle.dump(A_, f)
    os.replace(arch_path + '.tmp', arch_path)
    pool.terminate()


if __name__ == '__main__':
    main()
