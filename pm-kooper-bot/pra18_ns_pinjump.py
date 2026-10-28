"""pra_18 N->S right side: spin to the mirror, pin in the mirror/pillar corner (hold DOWN-RIGHT), then n in-place
jumps (A held 6, chained on landing, first at frame j after Z) to slow Laki, then stand. Reports the dash frame /
speed / Mario position and whether C-down on the dash frame clips, for each (r, s, j, n).
usage: pra18_ns_pinjump.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
def play(r, s, j, n, cd=None, N=70):
    e.load(base); f = 0; log = []
    for i in range(r): e.step(0, *st(0, 80), 2); f += 1
    for i in range(3): e.step(0, 0, 0, 2); f += 1
    jumps = 0; jt = None
    for i in range(N):
        q = player(e); b = Z if i == 0 else 0
        a = s if i < 2 else 45
        if jumps < n and ((jumps == 0 and i == j) or (jumps > 0 and jt > 3 and q['action'] in (0, 1, 2))):
            jt = 0; jumps += 1
        if jt is not None:
            if jt < 6: b |= A
            jt += 1
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(a, 80), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
if __name__ == '__main__' and MYARGS[1] != 'lib':
    jobs = list(itertools.product(range(0, 13), (90, 45), range(8, 30, 2), (0, 1, 2, 3)))[part::nparts]
    fo = open(out, 'a')
    for job in jobs:
        log = play(*job)
        # dash = first frame where speed jumps above 30 with Mario grounded on the spot
        cands = [r for r in log if r[4] > 25 and 556 <= r[1] <= 578 and r[2] > -24 and r[3] in (0, 1, 2)]
        hits = []
        for c in cands[:6]:
            play(*job, cd=c[0])
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append(c)
        rec = {'job': job, 'cands': cands[:4], 'clips': hits}
        print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
        if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
    print('done')
