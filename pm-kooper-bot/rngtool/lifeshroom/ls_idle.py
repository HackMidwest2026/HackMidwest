"""After the T3 death + Life Shroom revive: idle in T4's menu, then on the Power Bounce target screen; log every rand_int
call that is not the per-frame step (0x800269ac) or the coin (0x80146d54). Clean = only those two.
DIAGNOSTIC: seed written at ls_sweep.py's start state. usage: M64P_DBG=1 python3 ls_idle.py SEEDhex [MENU_FRAMES] [TARGET_FRAMES]"""
import os, sys
SEED_ = int(sys.argv[1], 16); NM = int(sys.argv[2]) if len(sys.argv) > 2 else 900; NT = int(sys.argv[3]) if len(sys.argv) > 3 else 600
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from btl import *; from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/li%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
e.load('/dev/shm/pmbot/ls_t3enemy.st'); e.step(0, 0, 0, 2); e.dbg_events()
e.w32(SEED, SEED_); e.w32(SEED2, SEED_)                     # DIAGNOSTIC
def run(n, b=0, x=0, y=0, tag=''):
    other = []; ks = {}
    for i in range(n):
        prev = e.u32(SEED); e.step(b if i == 0 else 0, x, y if i == 0 else 0, 2); cur = e.u32(SEED)
        k = 0; t = prev
        while t != cur and k < 5000: t = adv(t); k += 1
        ev = e.dbg_events(); o = [hex(v['ra']) for v in ev if v['ra'] not in (0x800269ac, 0x80146d54)]
        if o: other.append((i, o))
        ks[k] = ks.get(k, 0) + 1
    return other, ks
for i in range(1500):
    e.step(0, 0, 0, 2); e.dbg_events()
    if bstate(e) == 13 and e.s8(PLAYER_DATA + 2) > 0: break
print('T4 menu at', i, 'hp', e.s8(PLAYER_DATA + 2))
o, ks = run(NM); print('menu idle', NM, 'frames: other draws', o[:10], 'steps/frame', ks)
run(22, A); run(10, 0, 0, -70); run(25, A)
for i in range(80):
    if bstate(e) == 17: break
    run(1)
print('state', bstate(e))
o, ks = run(NT); print('target screen idle', NT, 'frames: other draws', o[:10], 'steps/frame', ks)
