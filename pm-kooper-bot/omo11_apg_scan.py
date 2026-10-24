"""Deliberate APG setups at the omo_11 Super Block from the real route state: PRE + 'wait:W' then the hit.
usage: omo11_apg_scan.py PRE W0 W1 OUT.jsonl   (caller wraps with timeout)"""
import json, os, sys
os.environ.setdefault('START', 'states/omo11_route_underblock.st')
import omo11_superblock_probe as P
pre, w0, w1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
fo = open(out, 'a')
for w in range(w0, w1):
    s = ';'.join(filter(None, [pre, 'wait:%d' % w]))
    P.setup(); P.pre(s); p, f = P.hit()
    r = {'pre': s, 'ok': bool(p), 'y': P.player(P.e)['y']}
    if p: r.update(P.dump(p))
    fo.write(json.dumps(r) + '\n'); fo.flush()
