"""Check dc_model.py against dc_turns.py logs: from the seed at the Charge confirm, the first coin frame after it
(q, what the rays give) and the confirm frames alone (Charge, Do Nothing; the popup A is NOT given to the model),
every frame's gRandSeed up to the 4th copy roll's aftermath (+40, or Mario's T2 menu), and every copy roll value.
Stops at a 3rd failed copy (the tackle then lands at 2 HP: Close Call, not modelled) and says so.
usage: python3 dc_check.py LOG.json [...]   -> one line per log, and a summary"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dc_model as DM
COIN, ROLL_RA = 0x80146D54, 0x802D46E0
def check(r):
    L = r['log']; C = {n: f for f, n in r['confirms']}
    cc, cn = C['Charge'], C['Do Nothing']
    q = next(f for f in range(cc, len(L)) if any(x[0] == COIN for x in L[f]['c']))
    m = DM.DSim(L[cc]['s0'], q).add(cc, 'charge').nothing(cn)
    game = [(f, x[2]) for f in range(cn, len(L)) for x in L[f]['c'] if x[0] == ROLL_RA][:4]
    fails = [f for f, v in game if v >= 600]
    end = game[-1][0] + 40 if len(game) == 4 else len(L)
    t2 = next((f for f in range(cn, len(L)) if L[f]['bs'] == 13), len(L))
    why = '4th roll +40' if end <= t2 else 'Mario T2 menu'
    if len(fails) >= 3: end = fails[2] + 1; why = '3rd failed copy (Close Call at 2 HP not modelled)'
    end = min(end, t2, len(L))
    for f in range(cc, end):
        if m.s != L[f]['s0']:
            prev = [x for x in L[f - 1]['c'] if x[0] != 0x800269AC]
            return False, 'MISMATCH at Charge+%d (Nothing%+d): game draws %s' % (f - cc, f - cn, [(hex(a), mx) for a, mx, v in prev][:12])
        m.frame(f)
    ok_rolls = [(f, v) for f, v in m.copy_rolls] == game[:len(m.copy_rolls)]
    return ok_rolls, 'frames Charge..+%d match (%s); rolls at Nothing+%s values %s model %s; copies %d; popup %s; menu +%s' % (
        end - cc, why, [f - cn for f, v in game], [v for f, v in game], [v for f, v in m.copy_rolls], sum(1 for f, v in game if v < 600),
        [f - cc for f, n in r['confirms'] if n == 'popup A'], r.get('partner_menu'))
if __name__ == '__main__':
    n = ok = 0
    for fn in sys.argv[1:]:
        r = json.load(open(fn))
        if r.get('error'): print(os.path.basename(fn), 'ERROR', r['error']); continue
        res, msg = check(r); n += 1; ok += res
        print(os.path.basename(fn), '%08x' % r['seed'], r['mode'], 'OK' if res else 'FAIL', msg)
    print('summary: %d/%d logs match' % (ok, n))
