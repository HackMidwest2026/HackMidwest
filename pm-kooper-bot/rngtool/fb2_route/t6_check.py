"""Check t6model.py against t6_collect.py logs: attack, Close Call value, T7 menu frame and every Power Bounce roll,
starting from the logged seed at frame 61 (after the rays) with the logged bolt frames and coin phase.
Also fits the lightning phases from the logged bolts.  usage: t6_check.py LOG.json [...]"""
import sys, json, collections
from t6model import *
from fb2model import rand_int as ri


def replay(row):
    """values of the row's draws (name, max, value)"""
    s = row['s0']; out = []
    for nm, mx in row['d']:
        if nm == 'step': continue
        s, v = ri(s, mx) if mx != 1 else (s, None)
        out.append((nm, mx, v))
    return out


def fit_phases(bolt_frames_seen, f0, f1):
    best = []
    for p130 in range(130):
        for p220 in range(220):
            if bolt_frames(p130, p220, f0, f1) == bolt_frames_seen: best.append((p130, p220))
    return best


ok = collections.Counter(); bad = []
SLAM_OK = '--slam' in sys.argv; CLAW_OK = '--noclaw' not in sys.argv
for fn in [a for a in sys.argv[1:] if not a.startswith('--')]:
    for run in json.load(open(fn)):
        rows = run['rows']; K = run['K']
        byf = {x['f']: x for x in rows}
        bolts = collections.Counter()
        for x in rows:
            for nm, mx in x['d']:
                if nm == 'bolt': bolts[x['f']] += 1
        coins = [x['f'] for x in rows if any(nm == 'coin' for nm, mx in x['d']) and x['f'] >= 61]
        # observed AI / test
        ev = {}
        for x in rows:
            for nm, mx, v in replay(x):
                if nm == 'evt': ev.setdefault('E', x['f']); ev.setdefault('evt', []).append((mx, v))
                if nm.startswith('8027'): ev['T'] = x['f']; ev['cc'] = v
        m = sim(byf[61]['s0'], 61, K, None, dict(bolts), coins[0], SLAM_OK, CLAW_OK)
        obs_atk = None
        vals = dict(ev.get('evt', []))
        if 80 in vals: obs_atk = 'slam' if (vals[80] < 20 and 60 not in vals) else ('claw' if (vals.get(60, 99) < 20 and CLAW_OK) else 'fire')
        lucky = ev.get('cc', 99) < 30
        good = m['attack'] == obs_atk and m['cc'] == ev.get('cc') and (ev.get('T') - ev.get('E')) == DELTA.get(obs_atk) and (not lucky or run['menu'] - ev['T'] == MENU[obs_atk])
        line = '%s K %3d E %s atk %s/%s dT %s cc %s/%s lucky %s menu-T %s' % (run['seed'], K, ev.get('E'), obs_atk, m['attack'],
               ev.get('T', 0) - ev.get('E', 0), ev.get('cc'), m['cc'], lucky, run['menu'] - ev.get('T', 0))
        ok['ai+cc', good] += 1
        if not good: bad.append(line)
        for pb in (run['pb'] if lucky else []):
            # the Power Bounce runs start from the T7-menu state: their frame numbers count from the menu frame
            M = run.get('pbbase', run['menu']) + 1; d = pb['dconf'] + M      # Run.load steps one frame after the load
            prow = {x['f'] + M: x for x in pb['rows']}
            allb = collections.Counter(bolts)
            for f, x in prow.items():
                for nm, mx in x['d']:
                    if nm == 'bolt': allb[f] += 1
            rolls = []
            for f in sorted(prow):
                if f < d: continue
                for nm, mx, v in replay(prow[f]):
                    if nm == 'pbroll': rolls.append((f - d, v))
            mm = sim(byf[61]['s0'], 61, K, d, dict(allb), coins[0], SLAM_OK, CLAW_OK)
            g = mm['rolls'] == rolls
            ok['pb', g] += 1
            line += ' | d %d (menu+%d) rolls %s bounces %d model %d %s' % (d, pb['dconf'], [v for _, v in rolls], len(rolls) + 1, mm['bounces'], g)
        print(line)
print(dict(ok))
for b in bad: print('BAD', b)
