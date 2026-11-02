"""Check boot_search.c's coin model against the emulator in a clean room: from the seed just before the first status-bar
coin draw, the model (coin rand_int(100) + frame step; next draw 24 frames later, 48 after a shine) must predict every
later draw's frame and shine. DIAGNOSTIC RAM write: gRandSeed set after the state load (setup only).
run from /tmp/claude-0/pm/bot1 with M64P_DBG=1. usage: coin_model_check.py STATE FRAMES SEEDhex"""
import sys, os
sys.path.insert(0, os.getcwd())
from emu import *
from rngsim import *
st, N, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3], 16)
COIN = 0x80146d54
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cm%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
e.load('states/' + st); e.step(0, 0, 0, 2); e.dbg_events()
e.w32(SEED, seed); e.w32(SEED2, seed)                            # DIAGNOSTIC
draws = []; other = 0
for f in range(N):
    prev = e.u32(SEED); e.step(0, 0, 0, 2); s = prev
    for v in e.dbg_events():
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        if v['ra'] == COIN: draws.append((f, s, rand_int(s, mx)[1] >= 70))
        elif mx != 1: other += 1
        s = rand_int(s, mx)[0]
# model
f0, s, _ = draws[0]; pred = []; f = f0
for j in range(len(draws)):
    s, v = internal(s, 1009); sh = v // 10 >= 70; pred.append((f, sh))
    for k in range(48 if sh else 24): s, _ = internal(s, 1000)
    f += 48 if sh else 24
ok = all(p[0] == d[0] and p[1] == d[2] for p, d in zip(pred, draws))
print(st, 'draws', len(draws), 'shines', sum(d[2] for d in draws), 'other rand_int calls', other, '| model matches every draw frame and shine:', ok)
if not ok: print([(p, d[0], d[2]) for p, d in zip(pred, draws) if p[0] != d[0] or p[1] != d[2]][:5])
