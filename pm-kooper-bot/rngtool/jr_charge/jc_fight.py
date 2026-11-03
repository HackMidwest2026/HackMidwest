"""Whole-fight odds (T3-T6) from the per-gate numbers of jc_odds.py (odds_w30.json), blind vs with Charge locks.
HP rules (emulator): Mario is at 2 HP at T3 (T1/T2 hits take 10 -> 2); a hit at 2 HP draws the Close Call
(rand(100) < 30 -> Lucky, else death -> Life Shroom -> 10 HP); a hit at 10 HP draws nothing and leaves 2 HP.
A death (revive: 933-939 LCG steps, not modelled) breaks a carried lock until the next Charge's rays.
Scenarios: blind; 'own' = each Charge (T3, T5) locks from its own rays with probability PL, a lock carries to the
following gates while nobody dies; 't1' = the T1 Charge locks (PL) and carries, T3/T5 rays as backup.
Waits (frames, 30/s): a planned press = LEAD + the plan's mean offset into the window; a gate whose lock comes from
the same turn's rays also waits for the search: LAT frames (rays end +61, search ~150, vs the earliest press ~+120).
usage: [ODDS=odds_w30.json] python3 jc_fight.py [PL=0.88] [LEAD=15] [LAT=91] [TRIALS=200000]"""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
PL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.88; LEAD = int(sys.argv[2]) if len(sys.argv) > 2 else 15
LAT = int(sys.argv[3]) if len(sys.argv) > 3 else 91; TR = int(sys.argv[4]) if len(sys.argv) > 4 else 200000
WINF = os.environ.get('ODDS', 'odds_w30.json'); O = json.load(open(os.path.join(HERE, WINF)))['res']
g3, g4, g5, g6 = (O[k] for k in ('T3 Bomb -> Close Call', 'T4 Maple Syrup -> Close Call', 'T5 do nothing -> Close Call', 'T6 Power Bounce'))
BL = (g3['blind'] + g4['blind'] + g5['blind']) / 3
rnd = random.Random(7)
def run(sc):
    deaths = 0; wait = 0; lock = False; hp = 2
    if sc == 't1': lock = rnd.random() < PL            # carried from T1 (exact model through T2)
    own = False
    def gate(g, k, own_turn):
        nonlocal deaths, lock, hp, wait
        if hp >= 6: hp = 2; return                     # 10 HP: no roll, the hit leaves 2 HP
        if lock:
            p = g['pm1']; wait += LEAD + g['wait_pm1'] + (LAT if own_turn else 0)
        else: p = BL
        if rnd.random() < p: return
        deaths += 1; hp = 10; lock = False            # revive breaks the carry
    # T3 Charge rays
    t3own = False
    if sc != 'blind' and not lock and rnd.random() < PL: lock = True; t3own = True
    gate(g3, 'T3', t3own)
    gate(g4, 'T4', False)
    t5own = False
    if sc != 'blind' and not lock and rnd.random() < PL: lock = True; t5own = True
    gate(g5, 'T5', t5own)
    if lock:
        r = rnd.random(); b5 = r < g6['pm1_5']; b6 = rnd.random() < g6['pm1_6'] / g6['pm1_5'] if b5 else False
        wait += LEAD + g6['wait_pm1']
    else:
        b5 = rnd.random() < g6['blind5']; b6 = b5 and rnd.random() < g6['blind6'] / g6['blind5']
    return deaths, b5, b6, wait
out = {}
for sc in ('blind', 'own', 't1'):
    D = [0, 0, 0]; B5 = B6 = 0; W = 0
    for t in range(TR):
        d, b5, b6, w = run(sc); D[d] += 1; B5 += b5; B6 += b6; W += w
    out[sc] = {'P(0 Life Shrooms)': D[0] / TR, 'P(1)': D[1] / TR, 'P(2)': D[2] / TR, 'E[Life Shrooms]': (D[1] + 2 * D[2]) / TR,
               'P(T6 5+)': B5 / TR, 'P(T6 6+)': B6 / TR, 'E[added wait s]': W / TR / 30}
    print(sc, {k: round(v, 3) for k, v in out[sc].items()})
json.dump({'PL': PL, 'LEAD': LEAD, 'LAT': LAT, 'res': out}, open(os.path.join(HERE, 'fight_PL%.2f_%s' % (PL, WINF.replace('odds_', ''))), 'w'), indent=1)
