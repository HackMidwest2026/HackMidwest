"""Lightning phases (p130, p220) of a t6_render.py / t6_collect.py log: the pair whose bolt frames (relative to the T6
Charge confirm: (f + p130) % 130 in {78, 83, 113, 118}, (f + p220) % 220 in {18, 78, 88, 178}) reproduce every logged
bolt draw. usage: bolt_phase.py LOG.json [...]"""
import sys, json
P130 = (78, 83, 113, 118); P220 = (18, 78, 88, 178)
def nb(f, p1, p2): return ((f + p1) % 130 in P130) + ((f + p2) % 220 in P220)
def phases(rows):
    seen = {}
    for r in rows: seen[r['f']] = sum(1 for nm, mx in r['d'] if nm == 'bolt')
    F = sorted(seen)
    return [(p1, p2) for p2 in range(220) for p1 in range(130) if all(nb(f, p1, p2) == seen[f] for f in F)]
if __name__ == '__main__':
    for p in sys.argv[1:]:
        L = json.load(open(p)); print(p, L.get('seed'), phases(L['frames']))
