"""Random-walk search for a Lakilester freeze that survives Mario moving: Mario walks/jumps randomly for F frames; flag
any 90-frame window where Mario travels > 150 units, ends > 60 from Laki, and Laki stays within 3 units the whole window and is not idle
(state 5). Writes one jsonl line per hit (seed, frame, states, pointer/index, positions).
usage: laki_stuck_search.py STATE SEED0 NRUNS OUT.jsonl [F=900]"""
import json, math, os, random, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu, A
from pm import *
from corner_sweep import stick_for
IDX, PTR, STATE = 0x8010D178, 0x8010D17C, 0x8010D188
st0, s0, n, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
F = int(sys.argv[5]) if len(sys.argv) > 5 else 900
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lss%d' % os.getpid())
from laki_stuck_search_policy import policy as _policy
policy = lambda rng: _policy(rng, F)
fo = open(out, 'a')
for seed in range(s0, s0 + n):
    rng = random.Random(seed); seq = policy(rng)
    e.load(st0); e.step(0, 0, 0, 2)
    M, L, S = [], [], []
    for f, (b, x, y) in enumerate(seq):
        e.step(b, x, y, 2)
        p = player(e); ls = [q for q in npcs(e) if q['id'] == -4]
        if not ls: break
        l = ls[0]; M.append((p['x'], p['z'])); L.append((l['x'], l['y'], l['z'])); S.append(e.u32(STATE) >> 16)
        if f >= 90:
            path = sum(math.hypot(M[i][0] - M[i - 1][0], M[i][1] - M[i - 1][1]) for i in range(f - 89, f + 1))
            dl = max(math.hypot(L[f][0] - L[i][0], L[f][2] - L[i][2]) for i in range(f - 90, f))
            dm = math.hypot(M[f][0] - L[f][0], M[f][1] - L[f][2])
            if path > 150 and dm > 60 and 5 not in S[f - 90:f + 1] and dl < 3:
                fo.write(json.dumps({'state': st0, 'seed': seed, 'F': F, 'frame': f, 'st': S[f], 'ptr': e.u32(PTR), 'idx': e.u32(IDX),
                                     'mario': M[f], 'laki': L[f], 'dm': dm, 'flags': '%08x' % l.get('flags', 0)}) + '\n'); fo.flush()
                break
print('done', st0, s0, n)
