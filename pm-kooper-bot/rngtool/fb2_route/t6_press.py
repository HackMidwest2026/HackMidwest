"""Press check for the page's FB2 plans in the emulator: the same T6 as t6_render.py (PRE idle menu frames, the Charge
inputs, confirm delay C), the popup A on confirm+K, Bowser's turn; Close Call = Mario still at 5 HP when the T7 menu
opens. With D >= 0 also the Power Bounce (t6_render.py's inputs and target-A delay D), Bowser's HP after it and the
bounces that took it there (route_build.py sets Bowser to 80 HP; 15 + 14 + ... per hit).
DIAGNOSTIC: gRandSeed written at the T6 menu (setup only). Run from /tmp/claude-0/pm/bot1:
  PYTHONPATH=. python3 t6_press.py BUILD SEEDHEX C PRE K[,K...] [D[,D...]]   -> one JSON line per (K, D)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
build, seed, C, PRE = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), int(sys.argv[4])
Ks = [int(x) for x in sys.argv[5].split(',')]; Ds = [int(x) for x in sys.argv[6].split(',')] if len(sys.argv) > 6 else [-1]
r = Run('tp', log=False)
for K in Ks:
    r.load(build + '/t6_menu.st'); r.seed(seed)                     # DIAGNOSTIC: gRandSeed at the T6 menu (setup only)
    r.idle(PRE)
    for b, y, n in r.moves(-2) + [(A, 0, 20)] + r.moves(2) + [(A, 0, 15)]: r.step(b, y); r.idle(n - 1)
    r.idle(C); c0 = r.f; t7 = None
    for i in range(1500):
        r.step(A if (i == 0 or i == K) else 0)
        if i > 80 and bstate(r.e) == 13: t7 = i; break
    hp = r.e.s8(PLAYER_DATA + 2); tmp = '/dev/shm/fb2r/tp_%d.st' % os.getpid(); r.e.save(tmp)
    for D in Ds:
        out = dict(seed='%08x' % seed, K=K, closecall=hp == 5, hp=hp, t7menu=t7)
        if D >= 0 and t7 is not None:
            r.load(tmp); r.idle(20)
            for b, y, n in r.moves(0) + [(A, 0, 20)] + r.moves(1) + [(A, 0, 15)]: r.step(b, y); r.idle(n - 1)
            r.idle(D); dc = r.f; r.step(A)
            for i in range(27 * 14 + 100):
                k = r.f - dc; r.step(A if k >= 44 and (k - 44) % 27 == 0 else 0)
            bh = r.bowser_hp(); lost = 80 - (bh[0] if bh else 0); cum = [sum(max(1, 15 - j) for j in range(n)) for n in range(1, 12)]
            hits = next((n + 1 for n, c in enumerate(cum) if c >= lost), None) if lost > 0 else 0
            out.update(D=D, pb_confirm=t7 + 1 + dc, bowser_hp=bh, bounces=hits if lost < 84 else '7+ (dead)')   # tmp holds the state after frame t7
        print(json.dumps(out), flush=True)
