# (run from the emulator working dir, bot1/) Hallway Bowser T1 at low HP (route: Charge; Lakilester Spiny Flip thrown with A; Bowser's turn).
# DIAGNOSTIC: Mario's HP written at the first menu (argv hp), chosen seed. Logs every rand_int per frame with its caller
# ('C' = coin) and the per-frame seed; writes data/hw3_<seed>_<d>_<hp>.json
# usage: python3 _hw3log.py SEED DSEED HP [THROW_K|timer] [GUARD 0/1]
import sys, os, json, random
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, dseed, HP = int(sys.argv[1], 16), int(sys.argv[2]), int(sys.argv[3]); rnd = random.Random(dseed)
TK = sys.argv[4] if len(sys.argv) > 4 else str(rnd.randint(55, 115)); GUARD = int(sys.argv[5]) if len(sys.argv) > 5 else rnd.randint(0, 1)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hw3%d' % os.getpid())
e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2)
e.w8(PLAYER_DATA + 2, HP)                                  # DIAGNOSTIC: Mario's HP
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; seeds = []; confirms = []; st_ = []; hps = []; press = set()
def step(b=0, x=0, y=0):
    if len(log) in press: b |= A
    seeds.append(e.u32(SEED)); e.step(b, x, y, 2); toks = []
    for ev in e.dbg_events():
        mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        if ev['ra'] == 0x800269AC: continue
        toks.append('C' if ev['ra'] == 0x80146D54 else [mx, hex(ev['ra'])])
    log.append(toks); st_.append(bstate(e)); hps.append(e.s8(PLAYER_DATA + 2))
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
def until(states, cap=4000):
    for f in range(cap):
        if bstate(e) in states: return f
        step()
    raise RuntimeError('state %d' % bstate(e))
def confirm(name):
    w(rnd.randint(0, 40)); confirms.append((len(log), name)); step(A)
out = {'seed': seed, 'dseed': dseed, 'hp': HP, 'tk': TK, 'guardTry': GUARD}
try:
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); confirm('T1 Charge'); until([14]); w(10)
    w(25, A); w(25, A); until([17], cap=80); confirm('T1 Spiny Flip'); c = len(log) - 1
    s0 = int(sys.argv[6]) if len(sys.argv) > 6 else rnd.randint(20, 40)
    for f in range(s0): step()
    for f in range(12 + rnd.randint(0, 4)): step(0, 70, 0)
    if TK != 'timer':
        k = c + int(TK)
        while len(log) < k: step()
        confirms.append((len(log), 'throw A')); step(A)
    # guard: find the HP drop later by replay is costly; instead press A every 2 frames from the AI on? No: a single try
    for f in range(4000):
        if bstate(e) == 13 or hps[-1] <= 0: break
        step()
    out['endState'] = bstate(e); out['hpEnd'] = hps[-1]
    if bstate(e) == 13: w(30); confirms.append((len(log), 'T2 menu'))
    else: w(600)
except Exception as ex: out['error'] = str(ex)
out.update(confirms=confirms, log=log, seeds=seeds, bstates=st_, hps=hps)
os.makedirs('data', exist_ok=True); json.dump(out, open('data/hw3_%08x_%d_%d.json' % (seed, dseed, HP), 'w'))
cc = [(f, t) for f, ts in enumerate(log) for t in ts if t != 'C' and t[1] == '0x80277518']
print('seed %08x d%d hp%d tk %s: end state %s hp %s, closecall draws at %s, err %s' % (seed, dseed, HP, TK, out.get('endState'), out.get('hpEnd'), [f for f, _ in cc], out.get('error')))
