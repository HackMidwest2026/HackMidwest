"""Jr. Troopa T3 enemy turn from a fixed point (after the T3 Bomb confirm), many seeds: the Close Call roll and the outcome;
when Mario dies, the Life Shroom revive's length in frames and RNG steps (to the T4 menu).
DIAGNOSTIC: the seed is written at the start point (an unknown run); the start point is made by ls_jr.py's inputs.
usage: M64P_DBG=1 python3 ls_sweep.py OUTJSON N [SEED0hex]"""
import os, sys, json, random
OUTF = os.path.abspath(sys.argv[1]); N = int(sys.argv[2]); R0 = int(sys.argv[3], 16) if len(sys.argv) > 3 else 7; NSW = N; OUTSW = OUTF
sys.argv = [sys.argv[0], '/dev/shm/pmbot/lsw', '0']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ls_jr.py')).read().split('for n in range(N):')[0])
rnd.seed(R0); N = NSW
# reach the start point once (fixed seed), then save a state there
seed = 0x2265b1f5
e.load('states/boss_0207_route_menu.st'); e.step(0, 0, 0, 2); e.w32(SEED, seed); e.w32(SEED2, seed); S[0] = seed
until([13]); jw(40)
jw(15, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); conf()
until([14]); jw(10); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); conf()
until([13, 14, 27, 32], mash=True); until([13], cap=4000); jw(100)
jw(30, Z); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); conf()
until([13], cap=4000, mash=True); jw(15); jw(15, 0, 0, 70); jw(25, A); step(A)
for i in range(60):
    if bstate(e) == 17: break
    step()
conf(2); until([13], cap=4000); jw(20)
jw(12, 0, 0, -70); jw(22, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); conf()
until([14]); jw(10); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); jw(10); step(A)
ST = '/dev/shm/pmbot/ls_t3enemy.st'; e.save(ST); e.step(0, 0, 0, 2)
res = []
for n in range(N):
    e.load(ST); e.step(0, 0, 0, 2)
    s = rnd.getrandbits(32); e.w32(SEED, s); e.w32(SEED2, s); S[0] = s     # DIAGNOSTIC
    F.clear(); hp0 = e.s8(PLAYER_DATA + 2)
    cc = None; dead = None; rev = None; menu = None
    for i in range(1500):
        step(); f = F[-1]
        if isinstance(f[3], list):
            for c in f[3]:
                if c[2] == 0x80277518 and cc is None: cc = (len(F) - 1, c[1])
        if dead is None and f[4] <= 0: dead = len(F) - 1
        if dead is not None and rev is None and f[4] > 0: rev = len(F) - 1
        if cc and f[1] == 13 and f[4] > 0: menu = len(F) - 1; break
    stp = lambda a, b: sum(x[2] for x in F[a + 1:b + 1]) if a is not None and b is not None else None
    r = {'seed': s, 'cc': cc, 'hp_after': F[-1][4], 'dead': dead, 'rev': rev, 'menu': menu,
         'frames_dead_menu': menu - dead if dead is not None and menu else None, 'steps_dead_menu': stp(dead, menu),
         'frames_cc_menu': menu - cc[0] if cc and menu else None, 'steps_cc_menu': stp(cc[0] if cc else None, menu),
         'nondefault': [[x[0], [c for c in x[3] if c[2] not in (0x800269ac, 0x80146d54)]] for x in F if isinstance(x[3], list) and any(c[2] not in (0x800269ac, 0x80146d54) for c in x[3])]}
    res.append(r); print(n, '%08x' % s, 'cc', cc, 'hp', r['hp_after'], 'dead->menu', r['frames_dead_menu'], r['steps_dead_menu'], 'cc->menu', r['frames_cc_menu'], r['steps_cc_menu'], flush=True)
    json.dump(res, open(OUTSW, 'w'))
