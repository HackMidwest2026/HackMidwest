"""v86: Bowser's T4 Lightning Blast (final_bowser_2.c EVS_UseAttackOrShockwave: RandInt(100) >= 75, then RandInt(110) 20-29),
every random draw from Lakilester's Do Nothing to the next Mario menu, for the T1-T4 page model (charge_live/fb14_live.js).
From BUILD/t4_partner.st (route_build.py, MARIO_HP=10: the T4 Charge done, Lakilester's menu, Cloud Nine still up).
DIAGNOSTIC (setup only): gRandSeed written at that menu. Random seeds are tried until N runs whose AI picked the Lightning
Blast (the AI's draws read from the log); each is logged draw by draw (caller, max, value) per frame to the next menu + 30.
Run from /tmp/claude-0/pm/bot1 with the debug core: M64P_DBG=1 PYTHONPATH=. python3 .../lb_log.py BUILD N SEEDHEX OUT.json [W]
W: idle frames before the Do Nothing confirm (default 0); also logs some wave / normal-attack runs (KEEP_OTHER=k)."""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
from rngsim import rand_int

if __name__ == '__main__':
    build, N, seed0, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3], 16), sys.argv[4]
    W = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    other = int(os.environ.get('KEEP_OTHER', '0'))
    rnd = random.Random(seed0); res = []; kept_other = 0; tries = 0
    # screening with the plain core (fast): the seed before Bowser's AI frame (P + 13) gives his RandInt calls when no bolt
    # strikes on that frame (the AI's draws come first then); the debug core then logs only the Lightning Blast seeds
    # (the debug core hung on some seeds in a long loop of tries)
    if os.environ.get('SCREEN'):
        r = Run('lbs', log=False); found = []
        while len(found) < N and tries < 50000:
            tries += 1; r.load(build + '/t4_partner.st'); sd = rnd.getrandbits(32); r.seed(sd)   # DIAGNOSTIC: gRandSeed (setup only)
            r.do_nothing(W); p0 = r.marks['nothing']
            while r.f - p0 < 14: r.step()
            s = [x for x in r.rows if x['f'] - p0 == 13][0]['s0']; s, a = rand_int(s, 100); s, b = rand_int(s, 110)
            if a >= 75 and 20 <= b < 30: found.append('%08x' % sd); print('cand', found[-1], tries, flush=True)
        print(' '.join(found)); sys.exit(0)
    seeds = [int(x, 16) for x in os.environ.get('SEEDS', '').split()]
    r = Run('lb')
    while len(res) < N + other and tries < 20000:
        tries += 1
        r.load(build + '/t4_partner.st'); sd = seeds.pop(0) if seeds else rnd.getrandbits(32); r.seed(sd)       # DIAGNOSTIC: gRandSeed (setup only)
        r.do_nothing(W); p0 = r.marks['nothing']
        # Bowser's AI on P + 13: its draws decide the attack
        while r.f - p0 < 15: r.step()
        ai = [x for x in r.rows if x['f'] - p0 == 13][0]
        s = ai['s0']; vals = []
        for nm, mx in ai['d']:
            s, v = rand_int(s, mx); vals.append((nm, mx, v))
        ev = [(mx, v) for nm, mx, v in vals if nm == 'evt']                         # the AI script's RandInt calls
        lb = len(ev) >= 2 and ev[0][0] == 100 and ev[0][1] >= 75 and ev[1][0] == 110 and 20 <= ev[1][1] < 30
        if tries % 100 == 0: print('tries', tries, 'kept', len(res), flush=True)
        if not lb and kept_other >= other: continue
        if not lb: kept_other += 1
        n = 0
        while not (bstate(r.e) == 13 and n > 30) and n < 2500: r.step(); n += 1
        for i in range(30): r.step()
        rows = []
        for x in r.rows:
            if x['f'] < p0: continue
            s = x['s0']; d = []
            for nm, mx in x['d']:
                s, v = rand_int(s, mx); d.append([nm, mx, v])
            rows.append(dict(f=x['f'] - p0, s0='%08x' % x['s0'], bs=x['bs'], d=d))
        menu = next((x['f'] for x in rows if x['bs'] == 13 and x['f'] > 30), None)
        tests = [x['f'] for x in rows for nm, mx, v in x['d'] if nm == 'testtgt']
        res.append(dict(seed='%08x' % sd, lb=lb, ai=[list(v) for v in vals], tests=tests, menu=menu, hp=r.e.s8(PLAYER_DATA + 2), ko=r.partner_ko(), cloud9=r.e.s8(BSTATUS + 0xA4), W=W, rows=rows))
        print(len(res), 'try', tries, 'lb' if lb else 'other', '%08x' % sd, 'ai', ev, 'tests', tests, 'menu', menu, 'hp', res[-1]['hp'], 'ko', res[-1]['ko'], flush=True)
    json.dump(dict(build=os.path.basename(build), runs=res), open(out, 'w'))
