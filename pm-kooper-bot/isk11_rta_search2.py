"""Two-phase RTA push search (inputs only): phase 1 = taps at ANG1 (tilt 80, 2 on / 8 off) x N1, phase 2 = taps at
ANG2 tilt MAG2 (2 on / 8 off) x N2. Reports how far right Laki gets with his target still frozen.
usage: isk11_rta_search2.py BASE OUT.jsonl  env ANG1S N1S ANG2S MAG2S N2"""
import json, os, sys
import isk11_rta_phases as P
L = lambda k, d, t=float: [t(v) for v in os.environ.get(k, d).split(',')]
fo = open(sys.argv[2], 'a')
for a1 in L('ANG1S', '45,60,75'):
    for n1 in L('N1S', '5,7,9,11', int):
        for a2 in L('ANG2S', '0,15,30,45'):
            for m2 in L('MAG2S', '60,80'):
                plan = [[a1, 80, 2, 8, n1], [a2, m2, 2, 8, int(os.environ.get('N2', '120'))]]
                r = P.run(plan, sys.argv[1])
                fo.write(json.dumps(r) + '\n'); fo.flush()
