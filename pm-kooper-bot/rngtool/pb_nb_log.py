"""v84: Power Bounce with Normal Boots vs Ultra Boots (JP, emulator, debug core): the frames of every random draw from the
confirm, for the page's Power Bounce profiles (pmrng_core.js jrpb5n / hwpb6n; test_pb_nb.js).
From a state on Power Bounce's target screen (TARGET=1) or on Mario's menu with the wheel on Jump (the route's
menu moves: A, down SUB, A to the target screen). DIAGNOSTIC writes (setup only, labelled): gBattleStatus.moveArgument
(+0x17A, the boots level the menu stored: 0 Normal, 2 Ultra), Mario's jump charge (+0x97), the enemy's HP (so that every
cap roll is seen), gRandSeed. The confirm is frame 0; each action command is pressed on the first frame of its window
(gBattleStatus.actionQuality turns -1 when the window opens; A on the next frame), as a perfect runner would.
Logged per frame: every rand_int (caller, max, value). Run from /tmp/claude-0/pm/bot1 with M64P_DBG=1:
  PYTHONPATH=. python3 .../pb_nb_log.py STATE BOOTS CHARGE HP N SEEDHEX OUT.json   (env TARGET=1, SUB=1)"""
import sys, os, json, random
from emu import *
from pm import *
from btl import *
from rngsim import *

if __name__ == '__main__':
    st, boots, chg, hp, N, seed0, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6], 16), sys.argv[7]
    rnd = random.Random(seed0); res = []
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/pbnb%d' % os.getpid())
    for k in range(N):
        e.load(st); e.step(0, 0, 0, 2)
        if os.environ.get('AC'): e.w8(PLAYER_DATA + 0xA, 1); e.w8(BSTATUS + 0x83, 1)   # DIAGNOSTIC: action commands learned (as in a real run; the generated state lacks it)
        if not os.environ.get('TARGET'):
            for b, y, n in [(A, 0, 20)] + [(0, -70, 10)] * int(os.environ.get('SUB', '1')) + [(A, 0, 25)]:
                e.step(b, 0, y, 2)
                for i in range(n - 1): e.step(0, 0, 0, 2)
        e.w16(BSTATUS + 0x17A, boots)                       # DIAGNOSTIC: the boots level the menu stored (moveArgument)
        e.w8(BSTATUS + 0x97, chg)                            # DIAGNOSTIC: Mario's jump charge
        a = e.u32(BSTATUS + 0xE0); e.w8(a + 0x1B8, hp)       # DIAGNOSTIC: enemy HP (every cap roll seen)
        sd = rnd.getrandbits(32); e.w32(SEED, sd); e.w32(SEED2, sd)   # DIAGNOSTIC: gRandSeed
        e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
        s = sd; log = []; presses = [0]; armed = True
        for f in range(900):
            q = e.s8(BSTATUS + 0x81)
            press = f == 0 or (f > 5 and q == -1 and armed)
            if f > 5 and q == -1 and armed: presses.append(f); armed = False
            if q != -1: armed = True
            e.step(A if press else 0, 0, 0, 2)
            for x in e.dbg_events():
                mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
                s, v = rand_int(s, mx)
                log.append([f, '%08x' % x['ra'], mx, v])
            if bstate(e) not in (17, 18, 19) and f > 30: break
        rolls = [[f_, v] for f_, ra, mx, v in log if ra == '802a1168']
        res.append(dict(seed='%08x' % sd, presses=presses, rolls=rolls, log=[x for x in log if x[1] != '800269ac'], hp_after=e.s8(a + 0x1B8), end=f))
        print(k, 'presses', presses[:8], 'rolls', rolls, 'hp', e.s8(a + 0x1B8), flush=True)
    json.dump(dict(state=os.path.basename(st), boots=boots, charge=chg, hp=hp, cases=res), open(out, 'w'))
