"""RTA setup search for the low Blue House entry (mac_02).

From the left loading zone entrance (states/mac02_start.st, Mario at (-600, 0, 0)), chain human-friendly moves:
  ('run', d)   hold notch d at full tilt until a wall stops Mario (position unchanged for 3 frames; must stop
               within 150 frames, else the move is rejected as timing-dependent), then let go
  ('spin', d)  press Z holding notch d, keep holding until the spin ends, then let go until Mario stands still
d is up, down, left or right (full tilt). SPEEDY=1 equips Speedy Spin. States are merged by position (0.01). After every move the final inputs
(up with a slight left tilt, walking or running) are tried; a final input that ends with Mario inside the house
while staying low (max y < 95) is a setup. Breadth-first, up to MAX_DEPTH moves.

usage: python3 house_rta.py <out.json> [max_depth]"""
import json, math, os, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from pm import *
A_, Z_ = 0x80, 0x20
NOTCHES = {'up': (0, 80), 'right': (80, 0), 'down': (0, -80), 'left': (-80, 0)}
MOVES = [(k, d) for k in ('run', 'spin') for d in NOTCHES]
FINALS = [(0, 80), (0, 40), (0, 20), (-5, 20), (-4, 20), (-6, 20), (-6, 40), (-7, 60), (-8, 80), (-9, 80)]
START = 'states/mac02_start.st'


def init():
    H.init()


def settle(e, n=40):
    """let go of the stick until Mario is idle and not moving"""
    last = None
    for f in range(n):
        e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] == 0 and last and abs(p['x'] - last[0]) < 1e-4 and abs(p['z'] - last[1]) < 1e-4:
            return True
        last = (p['x'], p['z'])
    return False


def do_move(e, move):
    kind, d = move
    sx, sy = NOTCHES[d]
    if kind == 'run':
        still, last = 0, None
        for f in range(150):
            e.step(0, sx, sy, 2)
            if e.s16(GAME_MODE) != GM_WORLD:
                return False
            p = player(e)
            if last and math.hypot(p['x'] - last[0], p['z'] - last[1]) < 0.01:
                still += 1
                if still >= 3:
                    return settle(e)
            else:
                still = 0
            last = (p['x'], p['z'])
        return False
    # spin
    e.step(Z_, sx, sy, 2)
    for f in range(40):
        p = player(e)
        if p['action'] != 26:
            break
        e.step(0, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            return False
    return settle(e)


def replay(e, seq):
    e.load(START)
    if os.environ.get('SPEEDY') == '1':
        e.w16(PLAYER_DATA + 0x208, 0x11F)
    e.step(0, 0, 0, 2)
    for m in seq:
        if not do_move(e, tuple(m)):
            return False
    return True


def final_check(e, sp):
    ok = []
    for sx, sy in FINALS:
        e.load(sp)
        maxy = 0
        for f in range(40):
            e.step(0, sx, sy, 2)
            p = player(e)
            maxy = max(maxy, p['y'])
            if H.inside(p):
                if maxy < 95:
                    ok.append((sx, sy))
                break
    return ok


def expand(seq):
    e = H.W['e']
    if not replay(e, seq):
        return []
    base = os.path.join(H.W['d'], 'rta_base.st')
    e.step(0, 0, 0, 2)
    e.save(base)
    out = []
    for m in MOVES:
        e.load(base)
        if not do_move(e, m):
            continue
        if e.s16(GAME_MODE) != GM_WORLD:
            continue
        p = player(e)
        if H.inside(p):
            continue
        sp = os.path.join(H.W['d'], 'rta_child.st')
        e.step(0, 0, 0, 2)
        e.save(sp)
        out.append({'seq': seq + [list(m)], 'pos': (round(p['x'], 3), round(p['y'], 2), round(p['z'], 3)),
                    'finals': final_check(e, sp)})
    return out


def main():
    out_path = sys.argv[1]
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    seen, frontier, found, allpos = set(), [[]], [], []
    t0 = time.time()
    for depth in range(1, max_depth + 1):
        nxt = []
        for res in pool.imap_unordered(expand, frontier, chunksize=1):
            for c in res:
                key = (round(c['pos'][0], 2), round(c['pos'][2], 2), round(c['pos'][1]))
                if key in seen:
                    continue
                seen.add(key)
                nxt.append(c['seq'])
                allpos.append({'seq': c['seq'], 'pos': c['pos']})
                if c['finals']:
                    found.append(c)
                    print('SETUP', json.dumps(c), flush=True)
                    json.dump(found, open(out_path, 'w'))
        print('depth %d: %d new positions (%d total), %d setups [%.0fs]' % (depth, len(nxt), len(seen), len(found), time.time() - t0), flush=True)
        frontier = nxt
        if not frontier:
            break
    json.dump(found, open(out_path, 'w'))
    json.dump(allpos, open(out_path.replace('.json', '_positions.json'), 'w'))
    print('done: %d setups' % len(found), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
