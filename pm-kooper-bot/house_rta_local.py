"""deeper RTA search near the blue house corner: seeds are positions already reached from the left loading zone
by house_rta.py (only up/down/left/right runs-into-walls and spins). From each, breadth-first up to EXTRA more
moves, keeping only positions near the corner (x -470..-320, z -200..-90) and merging by (x, z) to 0.001 and
facing. Every new position gets the final-input check (up / up with a slight left tilt).
usage: [SPEEDY=1] python3 house_rta_local.py <positions.json> <out.json> [extra]"""
import json, os, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_rta as R
import house_probe as H
from pm import *


def region(p):
    return -470 < p[0] < -320 and -200 < p[2] < -90


def main():
    seeds = [s for s in json.load(open(sys.argv[1])) if region(s['pos'])]
    out_path, extra = sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 6
    pool = mp.get_context('spawn').Pool(4, initializer=R.init)
    seen = set((round(s['pos'][0], 3), round(s['pos'][2], 3)) for s in seeds)
    frontier = [s['seq'] for s in seeds]
    found, allpos, t0 = [], list(seeds), time.time()
    print(len(seeds), 'seeds near the corner', flush=True)
    for depth in range(1, extra + 1):
        nxt = []
        for res in pool.imap_unordered(R.expand, frontier, chunksize=1):
            for c in res:
                if not region(c['pos']):
                    continue
                key = (round(c['pos'][0], 3), round(c['pos'][2], 3))
                if key in seen:
                    continue
                seen.add(key)
                nxt.append(c['seq'])
                allpos.append({'seq': c['seq'], 'pos': c['pos']})
                if c['finals']:
                    found.append(c)
                    print('SETUP', json.dumps(c), flush=True)
                    json.dump(found, open(out_path, 'w'))
        print('extra depth %d: %d new positions (%d total), %d setups [%.0fs]' % (depth, len(nxt), len(seen), len(found), time.time() - t0), flush=True)
        json.dump(allpos, open(out_path.replace('.json', '_positions.json'), 'w'))
        frontier = nxt
        if not frontier:
            break
    json.dump(found, open(out_path, 'w'))
    print('done: %d setups' % len(found), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
