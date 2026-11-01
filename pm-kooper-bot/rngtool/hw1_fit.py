# (run from the emulator working dir, bot1/) """Hallway T1 model check: Charge (Jr. model), Spiny Flip aim sparkle (energy_in_out, 10 parts, period 20, created +39,
updates until +RM), impact 8 x rand(359) at +IMP (per run), Bowser AI at impact+44: RandInt(80) < 20 Body Slam, else
RandInt(60) < 20 Claw Swipe (+116: rand(100), 10 x rand(359); +275: 6 x rand(359)), else Fire Breath (nothing)."""
import json, glob
from rngsim import *
runs = [json.load(open(f)) for f in sorted(glob.glob('data/hw1_*.json'))]
def check(r, RM, CREATE=39, PER=20):
    C = dict((n, f) for f, n in r['confirms']); fc, f0, f1 = C['T1 Charge'], C['T1 Spiny Flip'], C['T2 menu']
    imp = next(o for o in range(100, 300) if any(t != 'C' and t[1] == '0xe00861ec' for t in r['log'][f0 + o]))
    nc = next(f for f in range(fc, f1) if 'C' in r['log'][f])
    s = r['seeds'][fc]; inst = []; ev = {}; branch = None
    def add(f, k, xs): ev.setdefault(f, {}).setdefault(k, []).extend(xs)
    for c, rm in ((13, 58), (16, 61)): add(fc + c, 'eio', [(fc + rm, 10)])
    add(f0 + CREATE, 'eio', [(f0 + RM, PER)])
    add(f0 + imp, 'pre', [359] * 8)
    add(f0 + imp + 44, 'ai', [1])
    for f in range(fc, f1):
        if s != r['seeds'][f]: return 'MISMATCH +%d after %s (impact %d)' % (f - f0 if f >= f0 else f - fc, 'Spiny' if f >= f0 else 'Charge', imp)
        e = ev.get(f, {})
        for mx in e.get('pre', []): s, _ = rand_int(s, mx)
        if e.get('ai'):
            s, v = rand_int(s, 80)
            if v < 20: branch = 'body slam'; add(f + 71, 'pre', [359] * 10); add(f + 76, 'pre', [2, 2]); [add(f + o, 'pre', [359] * 6) for o in (133, 139, 145)]
            else:
                s, v2 = rand_int(s, 60)
                if v2 < 20: branch = 'claw'; add(f + 72, 'pre', [100] + [359] * 10); add(f + 231, 'pre', [359] * 6)
                else: branch = 'fire'
        for rm, per in e.get('eio', []):
            s, _ = rand_int(s, 360); p = []
            for i in range(10): s, _ = rand_int(s, 10); s, v = rand_int(s, per); p.append(-v)
            inst.append([f, rm, per, p])
        if f == nc: s, v = rand_int(s, 100); nc = f + (48 if v >= 70 else 24)
        for mx in e.get('post', []): s, _ = rand_int(s, mx)
        for c, rm, per, p in inst:
            if c <= f < rm:
                for i in range(10):
                    p[i] += 1
                    if p[i] >= per: p[i] = 0; s, _ = rand_int(s, 359)
        s = adv(s)
    return 'every frame matches (%s, impact +%d)' % (branch, imp)
for RM in range(112, 125):
    res = [check(r, RM) for r in runs]
    ok = sum(x.startswith('every') for x in res)
    if ok: print('remove +%d: %d/%d' % (RM, ok, len(runs)), res if ok == len(runs) else '')
print(check(runs[0], 119))
