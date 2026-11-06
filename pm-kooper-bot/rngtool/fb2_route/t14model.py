"""FB2 phase-2 route T1-T4 RNG model (JP, emulator-checked with t14_log.py): every gRandSeed draw from a seed in a menu
to Bowser's dodge test of the turn, and on through the next menu when Bowser missed. The page's model
(charge_live/fb14_live.js) is a port of this file.

Per frame f, in this order (t14_log.py logs; the effect slots: Bowser's star aura sits before the Charge rays):
  1. the lightning: one rand_int(359) per bolt (phases p130, p220 as t6model.py);
  2. script draws: the Charge's two energy_in_out(6) creations (Mario confirm M + 13 and + 16), the Jelly's sparkles
     (10 x (359, 10, 10), M + JELLY), Cloud Nine's puffs (evt RandInt(40), RandInt(30) on P + 200 .. P + 209, P = the
     Cloud Nine confirm), Bowser's AI (P + 13 after Do Nothing, P + 332 after Cloud Nine; RandInt(100) and maybe
     RandInt(110) on T4 for the Draining Shockwave, then RandInt(80) / RandInt(60) for Body Slam / Claw / Fire Breath),
     the dodge test rand_int(100) on AI + DELTA[attack] (< 50: the Cloud Nine dodge);
  3. the status-bar coin rand_int(100) on its frame (next + 24, or + 48 after a value >= 70);
  4. the aura: c[f mod 20] x rand_int(359) (16 per 20 frames; the pattern is the fight's, fixed);
  5. the Charge rays' respawns (readouts/charge_model.py; A's parts then B's);
  6. the per-frame step rand_int(1).
After a miss nothing else draws until the next menu (Fire Breath / Claw / Body Slam / the wave alike). After a hit,
Mario's HP drops and Peach's wish heals him (other effects; not modelled: the route has failed there).
usage: t14model.py check LOG.json [...]   (model vs the log, frame by frame)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'powerbounce'))
from fb2model import adv, internal

P130 = (78, 83, 113, 118); P220 = (18, 78, 88, 178)
DELTA = {'slam': 52, 'claw': 62, 'fire': 55, 'wave': 72}
AI_AFTER = {'nothing': 13, 'cloud_nine': 332}
PUFFS = (200, 210)
JELLY = 118           # the Jelly's sparkles: Mario's Jelly confirm + 118
# T4's Draining Shockwave when it misses Mario (Lakilester takes it): the same draws in every run (t14_log.py, 6 seeds),
# frames after Bowser's AI. PRE: script draws (before the coin): the effect's rand_int(7), Lakilester's hit stars.
# POST: the shockwave's particles (5 draws each: 359, 359, 10, 15, 15) after the aura and the rays.
WAVE_PRE = {29: [7], 76: [359] * 8}
WAVE_POST = {66: 1, 68: 2, 70: 3, 72: 4, 74: 5, 76: 6, 78: 7, 80: 8, 126: 8, 128: 7, 130: 6, 132: 5, 134: 4, 136: 3, 138: 2, 140: 1}
WAVE_POST.update({d: 9 for d in range(82, 125, 2)})


def rand_int(s, mx):
    if mx == 1: s, v = internal(s, 1000); return s, int(v >= 501)
    if mx == 100: s, v = internal(s, 1009); return s, v // 10
    return internal(s, mx)


def nbolts(f, p1, p2): return ((f + p1) % 130 in P130) + ((f + p2) % 220 in P220)


class Turn:
    """the scripted events of one turn: Mario's confirm M (kind 'charge' / 'jelly'), the partner confirm P (kind
    'cloud_nine' / 'nothing'), Bowser's flags (slam_ok, claw_ok) and whether it is T4 (the wave check)"""
    def __init__(self, M, mkind, P, pkind, slam_ok=True, claw_ok=True, t4=False, jelly=None):
        self.M, self.mkind, self.P, self.pkind, self.slam_ok, self.claw_ok, self.t4 = M, mkind, P, pkind, slam_ok, claw_ok, t4
        self.jelly = jelly
        self.ai = P + AI_AFTER[pkind] if P is not None else None


def run(s, f0, f1, nc, c, ph, turns, out=None):
    """from seed s at the start of frame f0 to the start of frame f1. c: 20 aura counts by f mod 20; ph = (p130, p220).
    Returns (s, nc, info) with info: per turn attack, test value, miss. out: optional list to collect (f, s0)."""
    rays = []           # (first respawn frames) per effect: list of frames with a respawn
    resp = {}
    info = []
    tests = {}
    for f in range(f0, f1):
        if out is not None: out.append((f, s))
        for i in range(nbolts(f, ph[0], ph[1])): s, _ = rand_int(s, 359)
        for t in turns:
            if t.mkind == 'charge' and f in (t.M + 13, t.M + 16):
                s, b = rand_int(s, 360); n0 = f
                for i in range(10):
                    s, sp = rand_int(s, 10); s, p = rand_int(s, 10)
                    n = n0 + 9 + p
                    while n < n0 + 45: resp[n] = resp.get(n, 0) + 1; n += 10
            if t.mkind == 'jelly' and t.jelly is not None and f == t.M + t.jelly:
                for i in range(10): s, _ = rand_int(s, 359); s, _ = rand_int(s, 10); s, _ = rand_int(s, 10)
            if t.pkind == 'cloud_nine' and t.P is not None and t.P + PUFFS[0] <= f < t.P + PUFFS[1]:
                s, _ = rand_int(s, 40); s, _ = rand_int(s, 30)
            if t.ai is not None and f == t.ai:
                atk = None
                if t.t4:
                    s, v = rand_int(s, 100)
                    if v < 75: atk = 'wave'
                    else:
                        s, v = rand_int(s, 110)
                        if v < 20: atk = 'wave'
                if atk is None:
                    s, v = rand_int(s, 80)
                    if v < 20 and t.slam_ok: atk = 'slam'
                    else:
                        s, v = rand_int(s, 60); atk = 'claw' if (v < 20 and t.claw_ok) else 'fire'
                tests[t.ai + DELTA[atk]] = (t, atk)
            if t.ai is not None and tests.get(t.ai + DELTA['wave'], (None, None))[1] == 'wave' and tests[t.ai + DELTA['wave']][0] is t:
                for m in WAVE_PRE.get(f - t.ai, []): s, _ = rand_int(s, m)
            if f in tests and tests[f][0] is t:
                s, v = rand_int(s, 100); info.append(dict(ai=t.ai, attack=tests[f][1], test=f, value=v, miss=v < 50))
        if f == nc:
            s, v = rand_int(s, 100); nc += 48 if v >= 70 else 24
        for i in range(c[f % 20]): s, _ = rand_int(s, 359)
        for i in range(resp.get(f, 0)): s, _ = rand_int(s, 359)
        for t in turns:
            if t.ai is not None and tests.get(t.ai + DELTA['wave'], (None, None))[1] == 'wave' and tests[t.ai + DELTA['wave']][0] is t:
                for i in range(WAVE_POST.get(f - t.ai, 0)):
                    for m in (359, 359, 10, 15, 15): s, _ = rand_int(s, m)
        s, _ = rand_int(s, 1)
    return s, nc, info


def fit(L):
    """the nuisance of a log: aura pattern (counts by f mod 20 = aura draws minus predicted ray respawns), bolt phases,
    the first coin frame"""
    rows = L['rows']; resp = {}
    from collections import Counter
    for r in rows:
        s = int(r['s0'], 16); vals = []
        for n, m in r['d']: s, v = rand_int(s, m); vals.append((n, v))
        for i, (n, v) in enumerate(vals):
            if n == 'e00d6160':
                for j in range(10):
                    p = vals[i + 2 + 2 * j][1]; k = r['f'] + 9 + p
                    while k < r['f'] + 45: resp[k] = resp.get(k, 0) + 1; k += 10
    cnt = {r['f']: sum(1 for n, m in r['d'] if n == 'aura') - resp.get(r['f'], 0) for r in rows}
    c = [Counter(v for f, v in cnt.items() if f % 20 == k).most_common(1)[0][0] for k in range(20)]
    bolt = {r['f']: sum(1 for n, m in r['d'] if n == 'bolt') for r in rows}
    ph = None
    for p2 in range(220):
        for p1 in range(p2 % 5, 130, 5):
            if all(nbolts(f, p1, p2) == b for f, b in bolt.items()): ph = (p1, p2); break
        if ph: break
    nc = next(r['f'] for r in rows if any(n == 'coin' for n, m in r['d']))
    return c, ph, nc


def turn_of(L, slam_ok=True, claw_ok=True, jelly=None):
    t, m = L['turn'], L['marks']
    mk = 'jelly' if t == 3 else 'charge'; pk = 'cloud_nine' if t == 1 else 'nothing'
    return Turn(0, mk, m.get('pconfirm'), pk, slam_ok, claw_ok, t4=(t == 4), jelly=jelly)


def check(path):
    L = json.load(open(path)); rows = L['rows']
    c, ph, nc = fit(L)
    jelly = None
    if L['turn'] == 3:
        jelly = next(r['f'] for r in rows if any(n == 'e0044170' for n, m in r['d']) and r['f'] < 150)
    best = None
    for so, co in ((True, True), (False, True), (True, False)):
        out = []; T = turn_of(L, so, co, jelly)
        f0 = rows[0]['f']; s, nc2, info = run(int(rows[0]['s0'], 16), f0, rows[-1]['f'] + 1, nc, c, ph, [T], out)
        mism = [f for (f, x), r in zip(out, rows) if x != int(r['s0'], 16)]
        if best is None or (mism[:1] or [1e9])[0] > (best[0][:1] or [1e9])[0]: best = (mism, info, so, co)
    mism, info, so, co = best
    first_bad = mism[0] if mism else None
    test = info[0]['test'] if info else None
    return dict(log=os.path.basename(path), turn=L['turn'], seed=L['seed'], marks=L['marks'], hp=L['hp'], aura=''.join(map(str, c)), ph=ph,
                flags=(so, co), frames=len(rows), first_mismatch=first_bad, exact_to_test=(first_bad is None or (test is not None and first_bad > test)),
                exact_all=first_bad is None, info=info, jelly=jelly)


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        for p in sys.argv[2:]: print(json.dumps(check(p)))
