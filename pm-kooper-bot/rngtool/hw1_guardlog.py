# (run from the emulator working dir, bot1/) """Hallway Bowser T1 (route: Charge; Lakilester Spiny Flip; Bowser's turn) with random delays before each confirm
(DIAGNOSTIC: chosen seed at Mario's first menu). Logs every rand_int per frame in order ('C' = coin) and the per-frame
seed; writes data/hw1_<seed>_<d>.json"""
import sys, os, json, random
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, dseed = int(sys.argv[1], 16), int(sys.argv[2]); rnd = random.Random(dseed)
import subprocess
r_ = subprocess.run(['python3', '_hwguard_drop.py', sys.argv[1], sys.argv[2]], capture_output=True, text=True, env=dict(os.environ, M64P_DBG='0'))
DROP = int([l for l in r_.stdout.split('\n') if l.startswith('DROP')][0].split()[1]); GUARD = DROP - 2
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hw1%d' % os.getpid())
e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; seeds = []; confirms = []; s = [seed]; st_ = []
def step(b=0, x=0, y=0):
    if len(log) == GUARD: b = A
    seeds.append(e.u32(SEED)); e.step(b, x, y, 2); toks = []
    for ev in e.dbg_events():
        mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        if ev['ra'] == 0x800269AC: continue
        toks.append('C' if ev['ra'] == 0x80146D54 else [mx, hex(ev['ra'])])
    log.append(toks); st_.append(bstate(e))
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
def until(states, cap=4000):
    for f in range(cap):
        if bstate(e) in states: return f
        step()
    raise RuntimeError('state %d' % bstate(e))
def confirm(name):
    w(rnd.randint(0, 40)); confirms.append((len(log), name)); step(A)
hp = lambda: (e.s8(PLAYER_DATA + 2), e.s8(PLAYER_DATA + 5), e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8))
out = {'seed': seed, 'dseed': dseed}
try:
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); confirm('T1 Charge'); until([14]); w(10); out['charge'] = hp()
    w(25, A); w(25, A); until([17], cap=80); confirm('T1 Spiny Flip')
    # aim: wait for the stick prompt (30 frames), hold right ~13 frames onto Bowser, no A (the throw comes when the
    # aim timer runs out, on a fixed frame)
    for f in range(40 + rnd.randint(0, 8)): step()
    for f in range(10 + rnd.randint(0, 4)): step(0, 70, 0)
    out['bowserHP_after_flip_wait'] = None
    until([13], cap=4000); out['bowser'] = e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8); out['t2'] = [hp(), bstate(e)]; w(30); confirms.append((len(log), 'T2 menu'))
except Exception as ex: out['error'] = str(ex)
out.update(confirms=confirms, log=log, seeds=seeds, bstates=st_)
os.makedirs('data', exist_ok=True); json.dump(out, open('data/hw1g_%08x_%d.json' % (seed, dseed), 'w'))
print('seed %08x d%d: Bowser HP %s, Mario HP/FP after T1 %s, err %s' % (seed, dseed, out.get('bowser'), out.get('t2'), out.get('error')))
