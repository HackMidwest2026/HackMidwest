"""T6 -> T7 of the FB2 route in the emulator: every gRandSeed draw from the T6 Super Charge confirm through Bowser's T6
turn (attack choice, Close Call roll) to the T7 Power Bounce rolls, and what changes it.

From BUILD/t6_menu.st (route_build.py). For each seed (DIAGNOSTIC: gRandSeed written at the T6 menu, setup only),
charge confirm delay c and Bowser-turn input policy, the turn is played to the T7 menu; then Power Bounce with confirm
delay d. Logged per run: draws by caller and frame (relative to the Charge confirm), LCG steps Charge confirm -> T7 menu,
Bowser's attack (from the evt draws), Close Call (rand_int(100) at the target test; < 30 = Lucky), Mario HP after,
the Power Bounce rolls (frame, value) and the bounce count, and fb2model's prediction from the T7 state.

Run from /tmp/claude-0/pm/bot1 with M64P_DBG=1:
  PYTHONPATH=. python3 t6_study.py BUILD SEEDS(hex,comma) CDELAYS(comma) DDELAYS(comma) [POLICIES] [--json OUT]
POLICIES: comma list of none|a25|a7 (A presses during Bowser's turn; a25 is A every 25 frames outside menus)."""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'powerbounce'))
from route import *
import fb2model

DMG0 = 15                                      # first Power Bounce hit on T7 (Ultra Boots, 4 Super Charges, Power Rush; measured)
RAY = lambda nm: nm.startswith('e00d6')          # energy_in_out (Charge rays; the aura was the same effect)


def classify(evts):
    """Bowser's attack from his evt draws: UseAttack = RandInt(80) [<20 & body slam ok -> slam] then RandInt(60)..."""
    return [mx for mx in evts]


def bowser_turn(r, policy, c0=None):
    """from the Charge confirm to the T7 menu. policy: none | a25 | a7 | at:K1/K2/.. (A on confirm+K only)"""
    n = 0
    at = set(int(x) for x in policy[3:].split('/')) if policy.startswith('at:') else set()
    while bstate(r.e) != 13 and n < 4000:
        b = A if (r.f - c0) in at else 0
        if policy == 'a25' and n % 25 == 24 and bstate(r.e) not in (13, 14, 17): b = A
        if policy == 'a7' and n % 7 == 6 and bstate(r.e) not in (13, 14, 17): b = A
        r.step(b); n += 1


def run_one(r, build, seed, c, ds, policy):
    r.load(build + '/t6_menu.st')
    r.seed(seed)                                                   # DIAGNOSTIC: gRandSeed at the T6 menu (setup only)
    r.charge(c, wheel=-2, sub=2)
    c0 = r.marks['charge']
    bowser_turn(r, policy, c0)
    t7 = r.f; r.idle(20)
    hp = r.e.s8(PLAYER_DATA + 2)
    draws = [(f - c0, nm, mx) for f, nm, mx in r.cnt(c0, t7)]
    steps = r.steps(c0, t7)
    tmp = '/dev/shm/fb2r/t7_%d.st' % os.getpid(); r.e.save(tmp)
    rows_t6 = r.rows
    out = dict(seed='%08x' % seed, c=c, policy=policy, t7_menu=t7 - c0, steps=steps, hp_after=hp,
               evt=[(f, mx) for f, nm, mx in draws if nm == 'evt'],
               closecall=[(f, mx) for f, nm, mx in draws if nm in ('testtgt',) or nm.startswith('80277')],
               counts=collections.Counter('%s/%d' % (nm, mx) if not RAY(nm) else 'rays' for f, nm, mx in draws),
               draw_sig=[(f, nm, mx) for f, nm, mx in draws if nm not in ('coin', 'bolt') and not RAY(nm)],
               pb=[])
    # Close Call value: replay the LCG over the logged draws on that frame
    for d in ds:
        r.load(tmp); r.power_bounce(d, wheel=0, sub=1); dconf = r.marks['pb']
        for i in range(27 * 14 + 120):
            k = r.f - dconf
            r.step(A if k >= 44 and (k - 44) % 27 == 0 else 0)      # A one frame before each landing
        rolls = []; s = None
        for row in r.rows[dconf:]:
            s = row['s0']
            for nm, mx in row['d']:
                if nm == 'step': continue
                s, v = rand_int(s, mx)
                if nm == 'pbroll': rolls.append((row['f'] - dconf, v))
        bh = r.bowser_hp()
        # fb2model from the confirm frame: seed at the start of the confirm frame, bolt frames and coin from the log
        sd = r.rows[dconf]['s0']
        light = sorted(row['f'] - dconf for row in r.rows[dconf:] for nm, mx in row['d'] if nm == 'bolt')
        coins = [row['f'] - dconf for row in r.rows[dconf:] for nm, mx in row['d'] if nm == 'coin']
        mrolls, mb = fb2model.model(sd, 0, dmg0=DMG0, coin0=coins[0] if coins else 999, light=light, kmax=14)
        out['pb'].append(dict(d=d, rolls=rolls, bounces=len(rolls) + 1 if rolls else 0, bowser_hp=bh,
                              model_rolls=mrolls, model_bounces=mb, model_match=[v for _, v in mrolls] == [v for _, v in rolls]))
    out['counts'] = dict(out['counts'])
    return out


if __name__ == '__main__':
    build = sys.argv[1]
    seeds = [int(x, 16) for x in sys.argv[2].split(',')]
    cs = [int(x) for x in sys.argv[3].split(',')]
    ds = [int(x) for x in sys.argv[4].split(',')] if sys.argv[4] != '-' else []
    pols = sys.argv[5].split(',') if len(sys.argv) > 5 and not sys.argv[5].startswith('--') else ['a25']
    r = Run('t6')
    res = []
    for sd in seeds:
        for c in cs:
            for p in pols:
                o = run_one(r, build, sd, c, ds, p); res.append(o)
                print(json.dumps({k: o[k] for k in ('seed', 'c', 'policy', 't7_menu', 'steps', 'hp_after', 'evt', 'closecall', 'counts')}))
                for pb in o['pb']:
                    print('   d %d rolls %s bounces %d bowserHP %s | model %s %d match %s' % (
                        pb['d'], pb['rolls'], pb['bounces'], pb['bowser_hp'], pb['model_rolls'], pb['model_bounces'], pb['model_match']), flush=True)
    if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'))
