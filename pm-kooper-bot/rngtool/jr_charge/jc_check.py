"""Check jc_model.py against jc_turns.py logs: from the first Charge confirm's seed and coin phase and the confirm
frames alone, every frame's gRandSeed and every roll's value. Stops at the first frame the model does not cover
(a death / Life Shroom revive) and says so.
usage: python3 jc_check.py LOG.json [...]"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc_model as JM
CC_RA = 0x80277518
def check(r, k=0):
    """from the k-th Charge confirm of the run"""
    L = r['log']; C = [c for c in r['confirms'] if c[2]]
    c0 = [f for f, n, t in C if t == 'charge'][k]
    nc = next(f for f in range(c0, len(L)) if any(x[0] == 0x80146D54 for x in L[f]['c']))
    m = JM.Sim(L[c0]['s0'], nc)
    hp_at = lambda f: L[f - 1]['hp'] if f > 0 else L[0]['hp']
    for f, n, t in C:
        if f < c0: continue
        if t and t.endswith('_cc') and hp_at(f) >= 6: t = t[:-3] + '_hit'          # at 10 HP: no Close Call roll, the hit lands
        if t: m.add(f, t)
    rolls_game = [(f, x[2]) for f in range(len(L)) for x in L[f]['c'] if x[0] == CC_RA]
    last = len(L); why = 'end of log'
    for f in range(c0, len(L)):
        if L[f]['hp'] <= 0 and f > c0: last = f; why = 'death at +%d after %s' % (f - max(g for g, n, t in C if g <= f), [n for g, n, t in C if g <= f][-1]); break
    last = min(last, max(m.ev) + 1)
    ok = 0
    for f in range(c0, last):
        if m.s != L[f]['s0']:
            g, n = max((g, n) for g, n, t in C if g <= f)
            return {'ok': False, 'frames': ok, 'msg': 'seed mismatch at frame %d (+%d after %s); game draws there: %s' % (f, f - g, n, [(hex(a), mx) for a, mx, v in L[f - 1]['c'] if a != 0x800269ac][:30])}
        m.frame(f); ok += 1
    cc_model = [v for k, v in sorted(m.rolls.items()) if k == 'cc']
    return {'ok': True, 'frames': ok, 'msg': 'all %d frames match (%s); game Close Call rolls %s' % (ok, why, [(f - c0, v) for f, v in rolls_game if f < last + 200])}
def check_syrup10(r):
    """after a T3 death (no Charge to start from): from the T4 Bomb confirm's seed and coin phase, Maple Syrup at 10 HP"""
    L = r['log']; C = r['confirms']; d4 = [f for f, n, t in C if n == 'T4 Bomb']; s4 = [f for f, n, t in C if n == 'T4 Syrup']
    if not s4 or L[s4[0] - 1]['hp'] < 6: return None
    d4, s4 = d4[0], s4[0]
    lc = max(f for f in range(d4) if any(x[0] == 0x80146D54 for x in L[f]['c'])); v = [x[2] for x in L[lc]['c'] if x[0] == 0x80146D54][0]
    m = JM.Sim(L[d4]['s0'], lc + (48 if v >= 70 else 24)).add(d4, 'bomb').add(s4, 'syrup_hit')
    for f in range(d4, min(s4 + 230, len(L))):
        if m.s != L[f]['s0']: return 'T4 Bomb -> Maple Syrup at 10 HP: mismatch at Syrup+%d' % (f - s4)
        m.frame(f)
    return 'T4 Bomb -> Maple Syrup at 10 HP: OK to Syrup+230'
if __name__ == '__main__':
    for fn in sys.argv[1:]:
        x = check_syrup10(json.load(open(fn)))
        if x: print(os.path.basename(fn), x)
        r = json.load(open(fn))
        for k in range(sum(1 for c in r['confirms'] if c[2] == 'charge')):
            res = check(r, k)
            print(os.path.basename(fn), r['start'], r['mode'], 'from Charge #%d' % (k + 1), 'OK' if res['ok'] else 'FAIL', res['msg'])
