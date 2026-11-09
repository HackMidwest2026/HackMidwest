"""v84: Bowser's phase-2 attack choice, emulator ground truth for the page model (pmrng_core.js fbnbAi; test_fbnb_ai.js).
From boss_2304_peach_start.st (phase 2): Mario's first menu, Mario Charge (route.py), then at Lakilester's menu the
DIAGNOSTIC setup writes (labelled, setup only): gRandSeed; Bowser's actor vars AVAR 0 and 2..7 (TurnCount,
TurnsSinceShockwave / StarBeam / ClawSwipe / BodySlam / Recover, RecoversLeft: actor + 0x88 + 4 i); the Star Rod enchant
flag on Bowser's main part (eventFlags + 0x7C, 0x00080000); Mario's jump / hammer charge (gBattleStatus + 0x97 / 0x96);
Mario's and Bowser's HP (the Recover branch: Mario's HP % minus Bowser's > 25). Then Lakilester Do Nothing and Bowser's
turn with no input, to the next Mario menu. Every rand_int (caller, max) per frame with the seed before / after the frame.
Afterwards: the vars, the enchant flag, the frames of Bowser's EnemyTestTarget calls.
Run from /tmp/claude-0/pm/bot1 with the debug core:
  M64P_DBG=1 PYTHONPATH=. python3 .../p2ai_log.py N SEED OUT.json   (N random cases from SEED)"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *

START = '/tmp/claude-0/pm/bot1/states/boss_2304_peach_start.st'


def avar(e, i):
    return e.s32(e.u32(BSTATUS + 0xE0) + 0x88 + 4 * i)


def set_avar(e, i, v):
    e.w32(e.u32(BSTATUS + 0xE0) + 0x88 + 4 * i, v & 0xFFFFFFFF)          # DIAGNOSTIC: Bowser's actor var (setup only)


def enchant(e, on=None):
    part = e.u32(e.u32(BSTATUS + 0xE0) + 0x1F4); f = e.u32(part + 0x7C)
    if on is not None:
        e.w32(part + 0x7C, (f | 0x00080000) if on else (f & ~0x00080000) & 0xFFFFFFFF)   # DIAGNOSTIC: the Star Rod flag
    return int(bool(e.u32(part + 0x7C) & 0x00080000))


if __name__ == '__main__':
    N, seed0, out = int(sys.argv[1]), int(sys.argv[2], 16), sys.argv[3]
    rnd = random.Random(seed0)
    r = Run('p2ai')
    r.load(START); r.settle(MENU, 20)
    base = '/dev/shm/pmbot/p2ai_menu%d.st' % os.getpid(); r.e.save(base)
    res = []
    for k in range(N):
        r.load(base)
        r.charge(0, wheel=0, sub=2); s = r.settle((14,), 20)
        recov = rnd.random() < 0.2
        v = dict(turn=rnd.randint(0, 7), sinceShock=rnd.randint(0, 7), sinceStar=rnd.randint(0, 5), sinceClaw=rnd.randint(0, 3),
                 sinceSlam=rnd.randint(0, 3), sinceRecover=rnd.randint(0, 3), recovers=rnd.choice([0, 3]) if recov else 0,
                 enchanted=int(rnd.random() < 0.3), charged=int(rnd.random() < 0.7))
        e = r.e
        for i, kk in [(0, 'turn'), (2, 'sinceShock'), (3, 'sinceStar'), (4, 'sinceClaw'), (5, 'sinceSlam'), (6, 'sinceRecover'), (7, 'recovers')]:
            set_avar(e, i, v[kk])
        enchant(e, bool(v['enchanted']))
        e.w8(BSTATUS + 0x97, 2 if v['charged'] else 0); e.w8(BSTATUS + 0x96, 0)        # DIAGNOSTIC: Mario's charges
        mhp, bhp = (e.s8(PLAYER_DATA + 3), 20) if recov else (5, 80)
        e.w8(PLAYER_DATA + 2, mhp); r.set_bowser_hp(bhp)                              # DIAGNOSTIC: HP (the Recover branch)
        bmax = r.bowser_hp()[1]; v['hpGap'] = (mhp * 100) // e.s8(PLAYER_DATA + 3) - (bhp * 100) // bmax
        sd = rnd.getrandbits(32); r.seed(sd)                                          # DIAGNOSTIC: gRandSeed
        a0 = len(r.rows); r.do_nothing(0)
        n = 0
        while n < 1400:
            b = bstate(r.e); r.step(A if (b == 20 and n % 25 == 24) else 0); n += 1     # state 20: a text box before Bowser's turn
            if n > 30 and bstate(r.e) in MENU: break
        rows = [dict(f=x['f'] - r.marks['nothing'], s0=x['s0'], s1=x['s1'], d=x['d']) for x in r.rows[a0:] if x['f'] >= r.marks['nothing']]
        after = dict(turn=avar(e, 0), sinceShock=avar(e, 2), sinceStar=avar(e, 3), sinceClaw=avar(e, 4), sinceSlam=avar(e, 5),
                     sinceRecover=avar(e, 6), recovers=avar(e, 7), enchanted=enchant(e), mhp=e.s8(PLAYER_DATA + 2), bhp=r.bowser_hp()[0])
        tests = [x['f'] for x in rows for nm, mx in x['d'] if nm in ('testtgt', '80277518')]   # the hit test (Cloud Nine) / Close Call roll
        ai = next((i for i, x in enumerate(rows) if x['f'] > 0 and any(nm == 'evt' for nm, mx in x['d'])), len(rows) - 1)
        rows = rows[max(0, ai - 3):ai + 1]                                            # kept: the AI frame and the 3 before it
        res.append(dict(k=k, seed='%08x' % sd, v=v, mhp=mhp, bhp=bhp, bmax=bmax, rows=rows, after=after, tests=tests, end=bstate(r.e)))
        print(k, json.dumps(v), 'after', json.dumps(after), 'tests', tests[:3], flush=True)
    json.dump(dict(start=os.path.basename(START), cases=res), open(out, 'w'))
