# Coin detector error rates from the runner's logs (v72, charge_live/README.md): every shine-locked stretch's seed predicts
# every coin draw; the detections (shine + rejected) inside the stretch are compared with the predicted shines.
# usage: python3 charge_live/tools/detector_rates.py   (the logs in the session's upload folder, U below)
import json, glob, sys
MUL = 0x5D588B65; M = 2**32
D1009 = 4294967295 // 1010
def adv(s): return (s * MUL + 1) % M
def coin(s):  # rand_int(100) on the coin: internal(1009)//10
    d = 4294967295 // 1010
    while True:
        s = adv(s); v = s // d
        if v <= 1009: return s, v // 10
def shines(seed, n):
    x, nc, out = seed, 0, []
    for t in range(n):
        if t == nc:
            x, v = coin(x); nc = t + (48 if v >= 70 else 24)
            if v >= 70: out.append(t)
        x = adv(x)
    return out
U = '/root/.claude/uploads/4de37507-9387-5f1e-bab5-10167305f887'
tot = dict(pred=0, miss=0, det=0, extra=0, vis_s=0.0, segs=0)
seen = set(); rows = []
for f in sorted(glob.glob(U + '/*log*.json')):
    d = json.load(open(f)); ev = d['events']; key = f.split('-log-')[-1]
    det = sorted([e['at'] for e in ev if e['ev'] in ('shine', 'rejected') and e.get('auto', True)])
    hides = sorted([e['at'] for e in ev if e['ev'] == 'barHide'])
    backs = sorted([e['t'] for e in ev if e['ev'] == 'coinBack'])
    for L in [e for e in ev if e['ev'] == 'lock']:
        sg = L['segs']; H = [e for e in ev if e['ev'] == 'barHide' and e['at'] > L['t']]
        if H: b = H[0]['at']; a = b - H[0]['upMs'] + 1000
        else:
            b = max(e['t'] for e in ev) ; a = max([e['at'] - 0 for e in ev if e['ev'] == 'barHide' and e['at'] < L['t']] or [0]) + 1000
            bk = [e['t'] for e in ev if e['ev'] == 'coinBack' and e['t'] < L['t']]; a = max(a, (bk[-1] + 1000) if bk else 0)
        k = (L['seed'], b)
        if k in seen: continue
        seen.add(k)
        taps = [e['at'] for e in ev if e['ev'] == 'shine' and e.get('seg') == sg and a <= e['at'] <= L['t'] + 1]
        if len(taps) < 8: continue
        P = shines(L['seed'], 60000)
        best = None
        for j0 in range(0, 3):
            for rate in [33.40 + 0.002 * i for i in range(30)]:
                t0 = taps[0] - P[j0] * rate
                pf = [(x - t0) / rate for x in taps]
                m = sum(1 for x in pf if min(abs(x - p) for p in P[:2000]) <= 2)
                if best is None or m > best[0]: best = (m, j0, rate, t0)
        m, j0, rate, t0 = best
        # least squares refit on matched taps
        pairs = []
        for x in taps:
            fx = (x - t0) / rate; p = min(P, key=lambda p: abs(p - fx))
            if abs(p - fx) <= 2: pairs.append((p, x))
        n = len(pairs); mp = sum(p for p, _ in pairs) / n; mx = sum(x for _, x in pairs) / n
        rate = sum((p - mp) * (x - mx) for p, x in pairs) / sum((p - mp) ** 2 for p, _ in pairs); t0 = mx - rate * mp
        fa, fb = (a - t0) / rate + 6, (b - t0) / rate - 6       # flash ~6 frames after the draw; a shine drawn near the hide never shows
        D = [(x - t0) / rate for x in det if a <= x <= b]
        pred = [p for p in P if fa <= p <= fb]
        miss = [p for p in pred if not any(-2.5 <= x - p <= 4.5 for x in D)]
        extra = [x for x in D if not any(-2.5 <= x - p <= 4.5 for p in P)]
        post = [p for p in pred if p * rate + t0 > L['t']]
        missPost = [p for p in miss if p * rate + t0 > L['t']]
        extraPost = [x for x in extra if x * rate + t0 > L['t']]
        resid = sorted(round(min((x - p for p in P), key=abs), 1) for x in D if x not in extra)
        rows.append(dict(log=key[:13], seed=hex(L['seed']), taps=len(taps), rate=round(rate, 4), vis=round((b - a) / 1000, 1), pred=len(pred), miss=len(miss), det=len(D), extra=len(extra),
                         post=len(post), missPost=len(missPost), extraPost=len(extraPost), missAt=[round(p * rate + t0 - a) for p in miss][:6], extraAt=[round(x * rate + t0 - a) for x in extra][:6], res=(resid[0], resid[len(resid)//2], resid[-1])))
        for k, v in (('pred', len(post)), ('miss', len(missPost)), ('det', len([x for x in D if x * rate + t0 > L['t']])), ('extra', len(extraPost)), ('vis_s', (b - max(a, L['t'])) / 1000), ('segs', 1)): tot[k] += v
for r in rows: print(json.dumps(r))
print('post-lock totals', json.dumps(tot))
