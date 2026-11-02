"""Planned confirms in the emulator: play the Surge, give the model what the readout would give (the seed before the
first throw, the coin's next draw frame, the throw frames, the damage class), plan the first all-4 confirm frame at
least READY frames after Mario's menu, press it, and count the copies (WANT=3: plan an exactly-3 frame instead).
DIAGNOSTIC RAM write: gRandSeed set once at Mario's turn-1 menu. The model inputs are taken from the emulator log
(standing in for a perfect readout).
usage (from /tmp/claude-0/pm/bot1): M64P_DBG=1 PYTHONPATH=. python3 .../plan_e2e.py N [READY] [WANT=4|3]"""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.getcwd())
from dsurge import *
import surge_model as SM

N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
READY = int(sys.argv[2]) if len(sys.argv) > 2 else 35
WANT = int(sys.argv[3]) if len(sys.argv) > 3 else 4
rnd = random.Random(424242 + WANT)
r = Run(0); ok = 0
for i in range(N):
    seed = rnd.getrandbits(32); pat = [(1, 1), (2, 2), (3, 3), (1, 2)][i % 4]
    r.reset(seed); r.surge(*pat); r.to_mario_menu()
    sp_abs = r.spinies(); F1 = sp_abs[0]; sp = [f - F1 for f in sp_abs]
    s1 = r.log[F1]['seed0']
    nc = next(row['f'] - F1 for row in r.log[F1:] if any(ra == COIN_RA for mx, ra, v in row['ev']))
    fw = r.fireworks()[0][1]                        # 8 at 100% (damage 3), 6 below
    M = r.marks['mario_menu'] - F1
    plan = next(c for c in range(M + READY, M + READY + 400)
                if (lambda k: k == 4 if WANT == 4 else k == 3)(SM.copies(SM.simulate(s1, nc, sp, c, fw, need=0))))
    after = plan - M
    gaps = [5, 2, 3, 4, 2]
    at = [after - sum(gaps)]
    for g in gaps: at.append(at[-1] + g)
    r.switch(at); r.enemy_turn()
    rolls = [v for f, v in r.copy_rolls()][:4]; k = sum(v < 600 for v in rolls)
    good = (k == WANT) and r.partner() == 3
    ok += good
    print('seed %08x mash %s: %d throws, planned confirm menu+%d (waited %d frames past ready), rolls %s -> %d copies %s'
          % (seed, pat, len(sp), after, after - READY, rolls, k, 'OK' if good else 'MISS'), flush=True)
print('%d/%d planned %d-copy confirms gave exactly %d' % (ok, N, WANT, WANT))
