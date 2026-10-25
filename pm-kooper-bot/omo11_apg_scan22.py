"""Exhaustive scan of two short templates on top of block 22 (from states/omo11_apg_top22.st), then walk under the
Super Block, wait W, jump; logs like omo11_apg_random22.py (menu, effect at menu+0x100, landing-dust offsets).
T=hop: [wait a] [hop h] [wait b]    T=ham: [wait a] [hammer dir] [wait b]
usage: omo11_apg_scan22.py T A0 A1 OUT.jsonl"""
import json, os, sys
T, a0, a1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.argv = ['omo11_apg_random22.py', '0', '0', out]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'omo11_apg_random22.py')).read()
head, body = src.split('for n in range(N):')
exec(head)
body = body.replace('    seq = [act() for i in range(R.randint(1, MAXA))]; W = R.choice([0, 1, 2, 3, 4, 6, 8, 12])\n', '')
import textwrap
one = compile(textwrap.dedent(body), 'one', 'exec')
mids = [('hop', h) for h in (1, 2, 3)] if T == 'hop' else [('hammer', d) for d in ('left', 'right', 'back', 'front', 'none')]
BS = [int(x) for x in os.environ.get('BS', '0,10,20').split(',')]
WS = [int(x) for x in os.environ.get('WS', '0,1,2,3,4,5,6').split(',')]
for A0 in range(a0, a1):
    for m in mids:
        for B0 in BS:
            for W in WS:
                seq = [s for s in ([('wait', A0)] if A0 else []) + [m] + ([('wait', B0)] if B0 else [])]
                exec(one)
