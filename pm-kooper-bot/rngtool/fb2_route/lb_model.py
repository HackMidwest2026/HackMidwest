"""v86: the Lightning Blast's draws (lb_log.py logs) fitted and checked frame by frame, as t14model.py does for the other
attacks. usage: python3 lb_model.py LB.json"""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t14model import rand_int, nbolts

AI = 13       # Bowser's AI on the Do Nothing confirm + 13 (frame 0 of the log = the confirm)


def resid(run):
    rows = run['rows']; ai = AI
    aura = {r['f']: sum(1 for n, m, v in r['d'] if n == 'aura') for r in rows}
    quiet = [f for f in aura if not (ai + 19 <= f <= ai + 19 + 70)]
    c = [Counter(aura[f] for f in quiet if f % 20 == k).most_common(1)[0][0] for k in range(20)]
    ex = {f: aura[f] - c[f % 20] for f in aura if ai + 19 <= f <= ai + 19 + 70 and aura[f] != c[f % 20]}
    cr = [r for r in rows if r['f'] == ai + 19][0]
    vals = [(n, m, v) for n, m, v in cr['d'] if n.startswith('e00d6')]
    return c, ex, vals


def respawns(f0, vals, rule):
    out = Counter()
    ps = [v for n, m, v in vals if m == 20]
    for p in ps:
        k = f0 + rule[0] + p
        while k < f0 + rule[1]: out[k] += 1; k += rule[2]
    return out


if __name__ == '__main__' and sys.argv[1] != 'fixture':
    d = json.load(open(sys.argv[1]))
    for run in d['runs']:
        if not run['lb']: continue
        c, ex, vals = resid(run)
        print(run['seed'], 'menu', run['menu'], 'extra aura-slot draws by frame - AI:', {f - AI: n for f, n in sorted(ex.items())})
        print('   creation values (10, 20):', [v for n, m, v in vals][1:])


LB_E = 19            # the effect's creation: AI + 19 (1 x 360, 10 x (10, 20)); respawns on E + 19 + p, + 20, while < E + 50
LB_R7 = 69           # rand_int(7) on AI + 69 (script phase)
LB_TEST = 99         # the dodge test on AI + 99
LB_BOLTS = 3         # then the blast's bolt: 3 x rand_int(359) after the test, same frame (script phase)


def fit_bg(run):
    rows = run['rows']; c, ex, vals = resid(run)
    bolt = {r['f']: sum(1 for n, m, v in r['d'] if n == 'bolt') for r in rows}
    ph = None
    for p2 in range(220):
        for p1 in range(130):
            if all(nbolts(f, p1, p2) == b for f, b in bolt.items() if f != AI + LB_TEST): ph = (p1, p2); break
        if ph: break
    nc = next(r['f'] for r in rows if any(n == 'coin' for n, m, v in r['d']))
    return c, ph, nc


def model(run, c, ph, nc, upto):
    rows = run['rows']; s = int(rows[0]['s0'], 16); resp = Counter(); out = []; test = None
    for f in range(rows[0]['f'], upto):
        out.append(s)
        for i in range(nbolts(f, ph[0], ph[1])): s, _ = rand_int(s, 359)
        if f == AI:
            s, a = rand_int(s, 100); s, b = rand_int(s, 110)
        if f == AI + LB_E:
            s, _ = rand_int(s, 360)
            for i in range(10):
                s, _ = rand_int(s, 10); s, p = rand_int(s, 20); k = f + 19 + p
                while k < f + 50: resp[k] += 1; k += 20
        if f == AI + LB_R7: s, _ = rand_int(s, 7)
        if f == AI + LB_TEST:
            s, test = rand_int(s, 100)
            for i in range(LB_BOLTS): s, _ = rand_int(s, 359)
        if f == nc: s, v = rand_int(s, 100); nc += 48 if v >= 70 else 24
        for i in range(c[f % 20]): s, _ = rand_int(s, 359)
        for i in range(resp[f]): s, _ = rand_int(s, 359)
        s, _ = rand_int(s, 1)
    return out, test


def check_all(d):
    res = []
    for run in d['runs']:
        if not run['lb']: continue
        c, ph, nc = fit_bg(run); miss = run['menu'] < 400
        upto = (run['rows'][-1]['f'] + 1) if miss else AI + LB_TEST + 1
        out, test = model(run, c, ph, nc, upto)
        bad = [r['f'] for r, x in zip(run['rows'], out) if int(r['s0'], 16) != x]
        res.append(dict(seed=run['seed'], miss=miss, test=test, game_test=[v for r in run['rows'] for n, m, v in r['d'] if n == 'testtgt'][0], frames=len(out), first_bad=bad[0] if bad else None))
    return res


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] != 'fixture':
    for r in check_all(json.load(open(sys.argv[1]))): print(json.dumps(r))


def fixture(paths, out):
    """the page's fixture (fixtures/fb14_lb_logs.json, test_fb14_ai.js): per Lightning Blast run the nuisance, the seed before
    every frame from the Do Nothing confirm (to the test after a hit, to the log's end after a miss), the test value"""
    import base64, struct
    L = []
    for p in paths:
        for run in json.load(open(p))['runs']:
            if not run['lb']: continue
            c, ph, nc = fit_bg(run); miss = run['menu'] < 400
            rows = run['rows'] if miss else [r for r in run['rows'] if r['f'] <= AI + LB_TEST + 1]
            L.append(dict(seed=run['seed'], W=run['W'], aura=c, ph=ph, nc=nc, n=len(rows), miss=miss, menu=run['menu'],
                          test=[v for r in run['rows'] for n, m, v in r['d'] if n == 'testtgt'][0],
                          s0=base64.b64encode(b''.join(struct.pack('<I', int(r['s0'], 16)) for r in rows)).decode()))
    json.dump(dict(about='v86 Lightning Blast runs (fb2_route/lb_log.py, lb_model.py): T4, Mario 10 HP, frame 0 = the Do Nothing confirm, Bowser\'s AI on 13', runs=L), open(out, 'w'), separators=(',', ':'))
    print(len(L), 'runs', sum(r['miss'] for r in L), 'misses')
if __name__ == '__main__' and sys.argv[1] == 'fixture':
    fixture(sys.argv[3:], sys.argv[2])
