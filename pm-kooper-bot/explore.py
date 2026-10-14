"""Go-Explore style search for the Kooper skip in nok_14.

Every state in the archive is a "ready" LZS state: Mario just landed with the
nok_13 exit stored, and the next frame is the frame-perfect A press.  The
explorer picks a cell, tries a random jump from it, and keeps any landing that
reaches a new cell.  The search succeeds when the floor below Mario is the
nok_15 exit (collider 21, deili2) while the nok_13 exit is still stored.

usage: python3 explore.py <run_dir> [hours]
"""
import gzip, math, multiprocessing as mp, os, pickle, random, sys, time, zlib
import numpy as np

ROM = os.environ.get('PM_ROM', 'pm-jp.z64')
START = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'states', 'nok14_start.st')
GOAL_COLLIDER = 21
SHM = os.environ.get('PM_TMP', '/dev/shm/pmbot')

STICK_MAGS = [80, 40, 20]
ANGLES = [i * 360 / 32 for i in range(32)]
A_HOLDS = [1, 2, 3, 5, 7, 10]


def random_action(rng):
    if rng.random() < 0.04:
        return (0, 0, rng.choice(A_HOLDS))
    a = math.radians(rng.choice(ANGLES))
    m = rng.choice(STICK_MAGS)
    return (int(round(m * math.cos(a))), int(round(m * math.sin(a))), rng.choice(A_HOLDS))


def cell_of(s):
    return (s['floor'], int(s['x'] // 12), int(s['z'] // 12), int(s['y'] // 30))


# ---- state blobs: xor against the base state, zlib compressed ----
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


def worker_init(base_path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from emu import Emu
    from lzs import Lzs
    pid = os.getpid()
    d = os.path.join(SHM, 'w%d' % pid)
    os.makedirs(d, exist_ok=True)
    e = Emu(ROM, d)
    W['lzs'] = Lzs(e, d)
    W['dir'] = d
    W['base'] = read_state(base_path)


def worker_jump(job):
    blob, action = job
    d = W['dir']
    src, dst = os.path.join(d, 'src.st'), os.path.join(d, 'dst.st')
    write_state(src, from_blob(blob, W['base']))
    trace = []
    res, s = W['lzs'].jump(src, dst, action[0], action[1], action[2], max_air=45, trace=trace)
    goal = any(t['below'] == GOAL_COLLIDER or t['floor'] == GOAL_COLLIDER for t in trace if not t['changing'])
    out = {'res': res, 'state': {k: s[k] for k in ('x', 'y', 'z', 'floor', 'below', 'action')}, 'goal': goal,
           'min_x': min(t['x'] for t in trace), 'max_x': max(t['x'] for t in trace)}
    if res == 'ready':
        out['blob'] = to_blob(read_state(dst), W['base'])
    return out


# ---- master ----
def make_base(run_dir):
    """make the first ready state (mario on deili1 with the exit stored) and use it as the xor base."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from emu import Emu
    from lzs import Lzs
    d = os.path.join(SHM, 'base')
    os.makedirs(d, exist_ok=True)
    e = Emu(ROM, d)
    L = Lzs(e, d)
    base_path = os.path.join(run_dir, 'base.st')
    res, s = L.jump(START, base_path, -80, 0, 7)
    assert res == 'ready', (res, s)
    return base_path, s


def main():
    run_dir = sys.argv[1]
    hours = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    os.makedirs(run_dir, exist_ok=True)
    arch_path = os.path.join(run_dir, 'archive.pkl')
    rng = random.Random(int(time.time()))

    if os.path.exists(arch_path):
        with open(arch_path, 'rb') as f:
            A = pickle.load(f)
        base_path = os.path.join(run_dir, 'base.st')
        print('resumed', len(A['cells']), 'cells', A['tries'], 'tries', flush=True)
    else:
        with mp.get_context('spawn').Pool(1) as p1:
            base_path, s = p1.apply(make_base, (run_dir,))
        base = read_state(base_path)
        c = cell_of(s)
        A = {'cells': {c: {'blob': to_blob(base, base), 'path': [], 'chosen': 0, 'pos': s}}, 'tries': 0, 'goals': [],
             'results': {}}
    pool = mp.get_context('spawn').Pool(4, initializer=worker_init, initargs=(base_path,))

    deadline = time.time() + hours * 3600
    last_save = last_print = time.time()
    t0, tries0 = time.time(), A['tries']
    pending = []
    while time.time() < deadline:
        # keep the pool busy
        while len(pending) < 16:
            keys = list(A['cells'].keys())
            weights = [1.0 / math.sqrt(1 + A['cells'][k]['chosen']) for k in keys]
            k = rng.choices(keys, weights)[0]
            cell = A['cells'][k]
            cell['chosen'] += 1
            act = random_action(rng)
            pending.append((k, act, pool.apply_async(worker_jump, ((cell['blob'], act),))))
        done = [p for p in pending if p[2].ready()]
        if not done:
            time.sleep(0.005)
            continue
        for p in done:
            pending.remove(p)
            k, act, r = p[0], p[1], p[2].get()
            A['tries'] += 1
            A['results'][r['res']] = A['results'].get(r['res'], 0) + 1
            parent = A['cells'][k]
            if r['goal']:
                path = parent['path'] + [act]
                A['goals'].append({'path': path, 'state': r['state'], 'res': r['res']})
                print('GOAL reached deili2 floor below!', path, r['state'], flush=True)
            if r['res'] != 'ready':
                continue
            nc = cell_of(r['state'])
            path = parent['path'] + [act]
            old = A['cells'].get(nc)
            if old is None or len(path) < len(old['path']):
                A['cells'][nc] = {'blob': r['blob'], 'path': path, 'chosen': old['chosen'] if old else 0, 'pos': r['state']}
        now = time.time()
        if now - last_print > 30:
            last_print = now
            xs = [c['pos']['x'] for c in A['cells'].values()]
            floors = sorted(set(k[0] for k in A['cells']))
            print('%.0fs tries %d (%.1f/s) cells %d x %.0f..%.0f floors %s results %s goals %d' % (
                now - t0, A['tries'], (A['tries'] - tries0) / (now - t0), len(A['cells']), min(xs), max(xs), floors,
                A['results'], len(A['goals'])), flush=True)
        if now - last_save > 300 or A['goals'] and now - last_save > 30:
            last_save = now
            with open(arch_path + '.tmp', 'wb') as f:
                pickle.dump(A, f)
            os.replace(arch_path + '.tmp', arch_path)
        if len(A['goals']) >= 5:
            break
    with open(arch_path + '.tmp', 'wb') as f:
        pickle.dump(A, f)
    os.replace(arch_path + '.tmp', arch_path)
    pool.terminate()


if __name__ == '__main__':
    main()
