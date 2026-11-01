"""Guided arc push: beam search over stop-and-go cycles (go G, aim offset TH, stop S), keeping only states where Laki
stays idle (follow state 5) with the frozen target intact, scored by progress along a reference Laki path minus
distance from it and a small per-frame cost. Stops when Laki is in the lower floor's top-right corner.
usage: lo_beam.py SEED.st REFPATH.json OUT_PREFIX [BEAM] [MAXSTEPS]"""
import json, math, os, sys, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
THETAS = [-60, -40, -25, -12, 0, 12, 25, 40, 60]; GO = (1, 2, 3, 4, 6, 8); STOPS = (1, 2, 4)
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/bm%d' % os.getpid(); os.makedirs(d, exist_ok=True); W['e'] = Emu(os.environ['PM_ROM'], d)
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def cycle(e, g, th, sl):
    ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
    p, l = player(e), laki(e)
    sx, sy = stick_for((math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th) % 360, 80)
    for i in range(g): e.step(0, sx, sy, 2)
    for i in range(sl):
        e.step(0, 0, 0, 2)
        if e.u32(PTR) != ptr0 or (e.u32(STATE) >> 16) != 5 or e.f32(HIST + 16 * ptr0 + 4) != tx or e.f32(HIST + 16 * ptr0 + 12) != tz: return False
    return tuple(where(e)[:2]) == (21, 0)
def expand(a):
    st, g, th, sl = a
    e = W['e']; e.load(st)
    if not cycle(e, g, th, sl): return None
    l = laki(e); return (l['x'], l['z'])
PATH = None; CUM = None
def prog(x, z):
    best = None
    for i in range(len(PATH) - 1):
        (ax, az), (bx, bz) = PATH[i], PATH[i + 1]
        dx, dz = bx - ax, bz - az; L2 = dx * dx + dz * dz or 1e-9
        u = max(0, min(1, ((x - ax) * dx + (z - az) * dz) / L2))
        px, pz = ax + u * dx, az + u * dz; d = math.hypot(x - px, z - pz)
        s = CUM[i] + u * math.sqrt(L2)
        if best is None or d < best[1]: best = (s, d)
    return best
if __name__ == '__main__':
    seed, refp, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    BEAM = int(sys.argv[4]) if len(sys.argv) > 4 else 6; MAXS = int(sys.argv[5]) if len(sys.argv) > 5 else 80
    PATH = [tuple(p) for p in json.load(open(refp))]
    from emu import Emu
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/bmmain')
    e.load(seed); e.step(0, 0, 0, 2); l = laki(e); PATH.insert(0, (l['x'], l['z']))
    CUM = [0]
    for i in range(1, len(PATH)): CUM.append(CUM[-1] + math.hypot(PATH[i][0] - PATH[i - 1][0], PATH[i][1] - PATH[i - 1][1]))
    os.makedirs('/dev/shm/pmbot/bmn', exist_ok=True)
    root = '/dev/shm/pmbot/bmn/root.st'; e.save(root)
    beam = [{'st': root, 'seq': [], 'frames': 0, 'score': 0}]
    opts = [(g, th, sl) for g in GO for th in THETAS for sl in STOPS]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    done = []
    for step in range(MAXS):
        tasks = [(n['st'], g, th, sl) for n in beam for (g, th, sl) in opts]
        res = pool.map(expand, tasks, chunksize=8)
        cands = []
        for (st, g, th, sl), r in zip(tasks, res):
            if r is None: continue
            n = next(b for b in beam if b['st'] == st)
            s, d = prog(*r); fr = n['frames'] + g + sl
            cands.append((s - 1.5 * d - 0.3 * fr, n, (g, th, sl), r, fr))
        cands.sort(key=lambda c: -c[0])
        newbeam, seen = [], set()
        for sc, n, mv, r, fr in cands:
            key = (round(r[0] / 3), round(r[1] / 3))
            if key in seen: continue
            seen.add(key)
            newbeam.append((sc, n, mv, r, fr))
            if len(newbeam) >= BEAM: break
        beam2 = []
        for k, (sc, n, mv, r, fr) in enumerate(newbeam):
            e.load(n['st']); cycle(e, *mv)
            st = '/dev/shm/pmbot/bmn/s%d_%d.st' % (step % 2, k); e.save(st)
            beam2.append({'st': st, 'seq': n['seq'] + [list(mv)], 'frames': fr, 'score': sc, 'L': r})
        beam = beam2
        b = beam[0]
        print('step %d: best L (%.1f, %.1f) frames %d score %.1f' % (step, b['L'][0], b['L'][1], b['frames'], b['score']), flush=True)
        for n in beam:
            if n['L'][0] >= float(os.environ.get('CX', 690)) and n['L'][1] <= -200: done.append(n)
        if done: break
    pool.terminate()
    done.sort(key=lambda n: n['frames'])
    json.dump([{'seq': n['seq'], 'frames': n['frames'], 'L': n['L']} for n in done], open(outp + '.json', 'w'))
    print('corner arcs', [(n['frames'], [round(v) for v in n['L']]) for n in done])
