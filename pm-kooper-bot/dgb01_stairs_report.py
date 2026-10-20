"""Summarise dgb01_stairs_explore.py output: for spots on the east (Tubba) side of the plank's wall, list every move
that ends somewhere other than the walkway/slab: 1F (fell), railing top, plank top, broken-railing chunk top, or the
west side of the plank wall.  usage: dgb01_stairs_report.py IN.jsonl"""
import json, sys
from collections import Counter, defaultdict

def east(x, y, z): return 0.92 * x + 0.08 * y + 0.38 * z > 84.2     # in front of the plank wall (c45)
def where(x, y, z):
    if y < 150: return 'fell to 1F'
    if abs(y - 285) < 1: return 'railing top'
    if 320 <= y <= 330 and z > 90: return 'chunk top'
    if y > 288: return 'plank top'
    if not east(x, y, z): return 'west of plank wall'
    return None
L = [json.loads(l) for l in open(sys.argv[1])]
print(len(L), 'runs,', len({tuple(l['spot']) for l in L}), 'spots')
hits = defaultdict(list)
for l in L:
    if not east(*l['spot']) or l['spot'][1] > 260: continue
    w = where(*l['end'])
    if w is None:
        for p in l['traj']:
            if where(*p) in ('plank top', 'chunk top', 'west of plank wall', 'railing top'): w = 'passed ' + where(*p); break
    if w: hits[w].append(l)
for w, ls in hits.items():
    print('==', w, len(ls), 'runs from', len({tuple(l['spot']) for l in ls}), 'spots')
    for l in sorted(ls, key=lambda l: (len(l['dir']), l['t'] or 0))[:25]:
        print('  spot', l['spot'], 'dir', l['dir'], 'walk', l['k'], 'tornado', l['t'], 'peak %.1f' % l['maxy'], 'end', l['end'])
print('peak y over east spots:', max(l['maxy'] for l in L if east(*l['spot']) and l['spot'][1] <= 260))
