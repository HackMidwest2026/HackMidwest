"""Jr. Troopa's end -> overworld: from states/jr_t6_pb_target.st, confirm the Power Bounce, press every bounce window,
then mash A every 20 frames (messages) for NF frames. Logs per frame: game mode, battle state, RNG steps, the non-step
non-coin draws. Prints, per seed, frames and steps from the killing hit's end to when the game mode leaves battle and to
NF. DIAGNOSTIC: random seed at the start; JRHP env sets Jr. Troopa's HP (so the bounce kills).
usage: M64P_DBG=1 python3 ls_exit.py OUT.json N [NF]"""
import os, sys, json, random
OUTF = os.path.abspath(sys.argv[1]); N = int(sys.argv[2]); NF = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from btl import *; from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/le%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
rnd = random.Random(11); res = []
PRESS = {0, 46, 73, 101, 129, 157, 185, 213, 241, 269, 297}
for n in range(N):
    e.load('states/jr_t6_pb_target.st'); e.step(0, 0, 0, 2); e.dbg_events()
    s = rnd.getrandbits(32); e.w32(SEED, s); e.w32(SEED2, s)                     # DIAGNOSTIC
    if os.environ.get('JRHP'): e.w8(e.u32(BSTATUS + 0xE0) + 0x1B8, int(os.environ['JRHP']))   # DIAGNOSTIC
    F = []
    for f in range(NF):
        b = A if (f in PRESS or (f > 320 and f % 20 == 0)) else 0
        prev = e.u32(SEED); e.step(b, 0, 0, 2); cur = e.u32(SEED)
        k = 0; t = prev
        while t != cur and k < 20000: t = adv(t); k += 1
        o = [(hex(x['ra']), x['a0']) for x in e.dbg_events() if x['ra'] not in (0x800269ac, 0x80146d54)]
        F.append([f, e.s16(GAME_MODE), bstate(e), k, o])
    modes = [x[1] for x in F]; leave = next((i for i in range(1, NF) if modes[i] != modes[i - 1]), None)
    r = {'seed': s, 'frames': F}
    res.append(r)
    ch = [(x[0], x[1], x[2]) for i, x in enumerate(F) if i == 0 or (x[1], x[2]) != (F[i - 1][1], F[i - 1][2])]
    print('where', where(e)); print('%08x' % s, 'mode/state changes', ch[:40], 'total steps', sum(x[3] for x in F), flush=True)
json.dump(res, open(OUTF, 'w'))
