"""climb the blue house's leaning east wall in stages (mac_02).

stage 0 is the wall-face landing found by house_explore (frame 46 of top.json). From every landing state,
try every jump (stick angle, strength, A hold, air stick); a new landing on the wall face (collider 45) that is
higher than the one it came from becomes a state for the next stage. Any frame inside the house is a goal.
States are kept as input lists and rebuilt by replay."""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from house_explore import BASES
from corner_sweep import stick_for
A_, Z_ = 0x80, 0x20
V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/house_wallface_approach.json')))
LAND_F = 46


def base_inputs():
    out, f = [], 0
    for b, deg, mag, n in V['seq']:
        sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
        for i in range(n):
            if f > LAND_F:
                return out
            out.append(({'tap': A_ if i == 0 else 0, 'spin': Z_ if i == 0 else 0, 'hold': A_}.get(b, 0), sx, sy))
            f += 1
    return out


def jump_inputs(job, n):
    d, deg, mag, hold, deg2 = job
    s1 = stick_for(deg, mag)
    s2 = stick_for(deg2, 80) if deg2 is not None else s1
    out = []
    for f in range(n):
        g = f - d
        out.append((A_ if 0 <= g < hold else 0,) + (s1 if g < 6 else s2))
    return out


def run(task):
    """task: (prefix inputs, list of jump jobs). returns goals and new wall-face landings"""
    from pm import player, GAME_MODE, GM_WORLD, COLLISION
    prefix, jobs = task
    e = H.W['e']
    e.load(H.base(*BASES[V['bi']]))
    for b, sx, sy in prefix:
        e.step(b, sx, sy, 2)
    y0 = player(e)['y']
    sp = os.path.join(H.W['d'], 'climb.st')
    e.save(sp)
    goals, lands = [], []
    for job in jobs:
        e.load(sp)
        inp = jump_inputs(job, 45)
        air = False
        for f, (b, sx, sy) in enumerate(inp):
            e.step(b, sx, sy, 2)
            if e.s16(GAME_MODE) != GM_WORLD:
                break
            p = player(e)
            if H.inside(p):
                goals.append({'inputs': prefix + inp[:f + 1], 'pos': (p['x'], p['y'], p['z'], p['action'])})
                break
            if p['action'] in (3, 4, 5, 8, 13):
                air = True
            elif air:
                if e.s16(COLLISION + 2) == 45 and p['y'] > y0 + 1:
                    lands.append({'inputs': prefix + inp[:f + 1], 'pos': (p['x'], p['y'], p['z'])})
                break
    return goals, lands


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    jobs = [(d, deg, mag, hold, deg2) for d in (0, 1) for deg in range(0, 360, 10) for mag in (80, 40, 20)
            for hold in (1, 3, 6, 12) for deg2 in (None, 180, 225, 270, 315, 0, 90)]
    chunks = [jobs[i:i + 64] for i in range(0, len(jobs), 64)]
    frontier = [{'inputs': base_inputs(), 'pos': None}]
    t0, stage = time.time(), 0
    while frontier and stage < 8:
        tasks = [(s['inputs'], c) for s in frontier for c in chunks]
        goals, lands = [], []
        for g, l in pool.imap_unordered(run, tasks):
            goals += g; lands += l
            for x in g[:1]:
                print('GOAL', json.dumps(x['pos']), len(x['inputs']), 'frames', flush=True)
        if goals:
            json.dump(goals, open(os.path.join(out_dir, 'goals.json'), 'w'))
        # next frontier: distinct landings by (x, y, z) rounded, highest first
        seen, nxt = set(), []
        for l in sorted(lands, key=lambda l: -l['pos'][1]):
            k = tuple(round(v) for v in l['pos'])
            if k not in seen:
                seen.add(k); nxt.append(l)
        nxt = nxt[:12]
        print('stage %d: %d states x %d jumps, %d goals, %d wall landings (%d distinct), top y %s [%.0fs]' % (
            stage, len(frontier), len(jobs), len(goals), len(lands), len(seen),
            [round(l['pos'][1], 1) for l in nxt[:5]], time.time() - t0), flush=True)
        json.dump(nxt, open(os.path.join(out_dir, 'stage%d.json' % stage), 'w'))
        if goals:
            break
        frontier = nxt
        stage += 1
    pool.terminate()


if __name__ == '__main__':
    main()
