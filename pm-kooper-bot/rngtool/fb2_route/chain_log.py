"""v87: one continuous Final Bowser phase-2 T1 -> T4 log (JP, debug core): every rand_int of every frame from T1's menu
to 60 frames after T4's next Mario menu, for the page's model carried across the turns (fb14_live.js fbStep;
test_fb14_chain.js). From BUILD/t1_menu.st (route_build.py, MARIO_HP=10). DIAGNOSTIC: gRandSeed written at the T1 menu
(setup only); nothing else is written.
Per turn (route_build.TURNS menus): PRE idle frames (random 30-90) in Mario's menu, Mario's action with confirm delay C
(random 0-20); Charge turns: the "+3" popup A on confirm + K (random 78-130, or none); 20 frames after the partner menu
opens, its inputs; the lever (Cloud Nine's / Do Nothing's confirm) on the first frame from there (wait 1..60) that makes
Bowser miss (T4: the wave, missed, Lakilester KO'd), found by playing each wait from a savestate; Cloud Nine's three A
presses on P + 132 / 152 / 172. GUARD=1: one A on P + 400 (T1) / P + 87 (T2-T4) during Bowser's turn.
Writes OUT.json: rows (f, s0, b, bs, d = [(caller name, max)]), per turn the marks (M = Mario's confirm, K, P = the lever,
next = the next menu), the test (caller testtgt) values, Mario's HP / Lakilester's KO after each turn.
Run from /tmp/claude-0/pm/bot1:  M64P_DBG=1 PYTHONPATH=. python3 chain_log.py BUILD SEEDHEX OUT.json [RNGSEED]"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
from route_build import TURNS

MHP = int(os.environ.get('MARIO_HP', '10')); GUARD = os.environ.get('GUARD') == '1'


def partner_items(pa):
    if pa == 'cloud_nine': return [(A, 0, 20), (0, DOWN, 10), (0, DOWN, 10), (A, 0, 15)]
    return [(0, UP, 10), (A, 0, 20), (0, DOWN, 10)]


def items(e): return [e.s16(PLAYER_DATA + 0x1B4 + 2 * i) for i in range(10) if e.s16(PLAYER_DATA + 0x1B4 + 2 * i) > 0]


class Chain(Run):
    def relog(self):
        self.e.bp_add(RAND_INT); self.e.dbg_log(1); self.e.dbg_events()

    def bowser_turn(self, pa, rec=True, cap=4000):
        """the lever A (this step), Cloud Nine's presses, the guard, Bowser's turn to the next Mario menu"""
        e = self.e; n = 0; k = 0
        def st(b):
            if rec: self.step(b, 0)
            else: e.step(b, 0, 0, 2); e.dbg_events()
        st(A)
        while True:
            k += 1
            b = A if (pa == 'cloud_nine' and k in (132, 152, 172)) else 0
            if GUARD and k == (400 if pa == 'cloud_nine' else 87): b = A
            if k > 260 and bstate(e) == 13: break
            if k > cap: break
            st(b)
        return k


if __name__ == '__main__':
    build, seed, out = sys.argv[1], int(sys.argv[2], 16), sys.argv[3]
    rnd = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else seed)
    r = Chain('chl', log=True); e = r.e
    r.load(build + '/t1_menu.st'); r.seed(seed)                        # DIAGNOSTIC: gRandSeed at the T1 menu (setup only)
    tmp = '/dev/shm/pmbot/chl%d_x.st' % os.getpid(); turns = []
    for t in range(1, 5):
        ma, mv, pa = TURNS[t - 1]
        r.idle(rnd.randint(30, 90))
        C = rnd.randint(0, 20); getattr(r, ma)(C, **mv); M = r.marks[ma]
        K = rnd.choice([None, rnd.randint(78, 130)]) if ma == 'charge' else None
        n = 0
        while bstate(e) != 14 and n < 600: r.step(A if (K is not None and r.f - M == K) else 0); n += 1
        r.idle(20)
        its = partner_items(pa)
        for b, y, k in its:
            r.step(b, y); r.idle(k - 1)
        e.save(tmp); f0 = r.f; pick = None; tried = []
        for w in range(1, 61):                          # the lever: the first wait that makes Bowser miss
            e.load(tmp); e.dbg_events()
            for i in range(w): e.step(0, 0, 0, 2); e.dbg_events()
            r.bowser_turn(pa, rec=False)
            a4 = e.u32(BSTATUS + 0xE0); wave = bool(a4) and e.s32(a4 + 0x88 + 8) == 0      # T4: TurnsSinceShockwave 0 = the wave came (a guard may block Lakilester's KO)
            ok = e.s8(PLAYER_DATA + 2) == MHP and 149 in items(e) and (t != 4 or wave)
            tried.append(int(ok))
            if ok: pick = w; break
        e.load(tmp); r.relog()
        if pick is None: print('T%d: no wait in 1..60 makes Bowser miss' % t, flush=True); pick = 30
        r.idle(pick); P = r.f; r.bowser_turn(pa); nxt = r.f
        tests = [(x['f'], m) for x in r.rows[P:] for nm, m in x['d'] if nm == 'testtgt']
        turns.append(dict(turn=t, M=M, mkind=ma, C=C, K=K, P=P, pkind=pa, wait=pick, tried=''.join(map(str, tried)), next=nxt,
                          hp=e.s8(PLAYER_DATA + 2), ko=r.partner_ko(), charges=e.s8(BSTATUS + 0x97), test_frames=[f for f, m in tests]))
        print(json.dumps(turns[-1]), flush=True)
    r.idle(60)
    rows = [dict(f=x['f'], s0='%08x' % x['s0'], b=x['b'], bs=x['bs'], d=x['d']) for x in r.rows]
    json.dump(dict(seed='%08x' % seed, guard=GUARD, build=build, turns=turns, rows=rows), open(out, 'w'))
    print('frames', len(rows))
