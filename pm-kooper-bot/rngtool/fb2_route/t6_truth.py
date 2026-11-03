"""Truth for a t6_render.py run, to compare with what the page locked: gRandSeed before the rays (confirm + 13) after
that frame's bolts (the page's seed: the state before effect A's base-angle draw), the lightning phases, the bolt and
coin frames in the rays window, and, from frame 61, the seed and the next coin frame (fb2_route/t6model.py's start).
usage: python3 t6_truth.py LOG.json"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'readouts'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from charge_model import rand_int
from bolt_phase import phases
L = json.load(open(sys.argv[1])); R = {r['f']: r for r in L['frames']}
s = int(R[13]['s0'], 16)
for nm, mx in R[13]['d']:
    if nm != 'bolt': break
    s, _ = rand_int(s, mx)
coin = [f for f in range(-200, 400) if f in R and any(nm == 'coin' for nm, mx in R[f]['d'])]
nxt = next(f for f in coin if f >= 61)
print(json.dumps(dict(seed=L['seed'], s0='%08x' % s, phases=phases([R[f] for f in sorted(R)]), bolts_rays=[f - 13 for f in range(13, 61) for nm, mx in R[f]['d'] if nm == 'bolt'],
                      coins_rays=[f - 13 for f in coin if 13 <= f < 61], s61=R[61]['s0'], nc61=nxt)))
