# (run from the emulator working dir, bot1/) """Jr. Troopa T3 -> T6 with real inputs and random delays before each confirm (DIAGNOSTIC: chosen seed at the T3 Bomb
target screen). Logs every rand_int call per frame in order ('C' = coin, else the max), and the frame of each confirm.
Writes data/jrchain_<seed>_<delayseed>.json"""
import sys, os, json, random
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, dseed = int(sys.argv[1], 16), int(sys.argv[2])
rnd = random.Random(dseed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jc%d' % os.getpid())
e.load('states/jr_t3_bomb_target.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; seeds = []; confirms = []; s = [seed]
def step(b=0, x=0, y=0):
    seeds.append(e.u32(SEED)); e.step(b, x, y, 2); toks = []
    for ev in e.dbg_events():
        mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        s[0], v = rand_int(s[0], mx)
        if ev['ra'] == 0x800269AC: continue
        toks.append('C' if ev['ra'] == 0x80146D54 else [mx, hex(ev['ra'])])
    log.append(toks)
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
def until(states, cap=4000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
def confirm(name, mash=False, pb=False):
    w(rnd.randint(0, 40)); confirms.append((len(log), name)); step(A)
    if pb:
        for f in range(1, 240): step(A if f in {47, 74, 102, 130, 158, 186, 214} else 0)
def confirm_ok(name, run, ok):
    """DIAGNOSTIC: choose a seed (written just before the delay) so this press gives the route's outcome"""
    d = rnd.randint(0, 40); tmp = '/dev/shm/pmbot/jcs%d.st' % os.getpid(); e.save(tmp); n0 = len(log); c0 = len(confirms)
    for k in range(1, 200):
        e.load(tmp); e.step(0, 0, 0, 1); e.dbg_events(); del log[n0:]; del seeds[n0:]; del confirms[c0:]
        sd = (0x9E3779B9 * (k + 1000 * dseed)) & 0xFFFFFFFF; e.w32(SEED, sd); e.w32(SEED2, sd); s[0] = sd   # DIAGNOSTIC
        h0 = hp(); w(d); confirms.append((len(log), name)); step(A); run()
        if ok(h0): return sd
    raise RuntimeError('no seed for ' + name)
hp = lambda: (e.s8(PLAYER_DATA + 2), e.s8(PLAYER_DATA + 5), e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8))
out = {'seed': seed, 'dseed': dseed}
try:
    # T3: Bomb (K target screen already open) + enemy turn
    confirm_ok('T3 Bomb', lambda: until([13, 27, 32], mash=True), lambda h0: hp()[0] == h0[0] and bstate(e) == 13); out['t4'] = [hp(), bstate(e)]; until([13]); w(20)
    # T4 (as jr_jrbuild_a/b): Z to Bombette, Bomb; Mario items, down 2 = Maple Syrup
    w(30, Z); w(25, A); w(10, 0, 0, -70); w(25, A); confirm('T4 Bomb'); until([13], mash=True); w(15)
    out['t4b'] = [hp(), bstate(e)]
    w(15, 0, 0, 70); w(25, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
    confirm_ok('T4 Maple', lambda: until([13, 27, 32]), lambda h0: hp()[0] == h0[0] and bstate(e) == 13); out['t5'] = [hp(), bstate(e)]; until([13]); w(20)
    # T5 (as jr_jrbuild_b): wheel Items -> Jump, Super Charge; Bombette Strategies, do nothing
    w(12, 0, 0, -70); w(22, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); confirm('T5 Charge'); until([14]); out['t5c'] = [hp(), bstate(e)]
    w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70)
    confirm_ok('T5 Nothing', lambda: until([13, 27, 32]), lambda h0: hp()[0] == h0[0] and bstate(e) == 13); out['t6'] = [hp(), bstate(e)]; until([13]); w(20)
    # T6 (as jr_jrbuild_c): Power Bounce, A per bounce; outcome 6+ (Jr. Troopa at 0 HP)
    w(22, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
    confirm_ok('T6 Bounce', lambda: [step(A if f in {47, 74, 102, 130, 158, 186, 214} else 0) for f in range(1, 240)], lambda h0: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8) <= 0); w(300)
    out['end'] = [hp(), bstate(e)]
except Exception as ex:
    out['error'] = str(ex)
out['confirms'] = confirms; out['log'] = log; out['seeds'] = seeds
os.makedirs('data', exist_ok=True)
json.dump(out, open('data/jrs_%08x_%d.json' % (seed, dseed), 'w'))
print('seed %08x d%d confirms %s | after T3 %s, T4 bomb %s, T4 %s, T5 charge %s, T5 %s, end %s | err %s' % (seed, dseed, [c[1] for c in confirms], out.get('t4'), out.get('t4b'), out.get('t5'), out.get('t5c'), out.get('t6'), out.get('end'), out.get('error')))
