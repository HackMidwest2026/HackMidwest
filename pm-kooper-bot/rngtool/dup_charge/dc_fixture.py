"""Cases for the page's Duplighost Charge-lock plan test (../test_dup_plan.js), from the emulator-checked model
(dc_model.py; dc_check.py: 60/60 runs, every frame from the Charge confirm to the 4th roll).
Per case: a random gRandSeed and next coin frame at the Charge confirm (log frame 0), stepped to the rays' frame 0
(confirm + 13: what the Charge lock gives the page, its tracker's clock frame 0 with first coin q), and the copies
(4, 3, or 2 = two or fewer) for Bombette's Do Nothing confirmed on every log frame D in [D0, D1) (clock frame D - 13).
usage: python3 dc_fixture.py N OUT.json [seed]"""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dc_model as DM
JM = DM.JM
N, OUT = int(sys.argv[1]), sys.argv[2]
rnd = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 71)
D0, D1 = 140, 330
cases = []
for i in range(N):
    s0 = rnd.getrandbits(32); nc0 = rnd.randrange(0, 48)
    m = JM.Sim(s0, nc0).add(0, 'charge'); m.run(0, 13)
    seed, q = m.s, m.nc - 13                      # the page's seed and first coin at clock frame 0
    m.run(13, D0)
    cls = [min(4, max(2, c)) for c in DM.table(m.s, m.nc, D0, D1 - D0)]
    cases.append({'s0': '%08x' % s0, 'nc0': nc0, 'seed': '%08x' % seed, 'q': q, 'D0': D0, 'copies': ''.join(map(str, cls))})
json.dump({'D0': D0, 'D1': D1, 'clock0': 13, 'cases': cases}, open(OUT, 'w'))
print(N, 'cases ->', OUT)
