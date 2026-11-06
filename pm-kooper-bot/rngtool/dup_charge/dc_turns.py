"""Play the runner's Duplighost T1 (and optionally T2) in the emulator and log every gRandSeed draw per frame.
  T1: Mario (acts first, no Z): Jump menu -> Super Charge -> target Mario -> A (the Charge confirm, random delay);
      Charge popup A at confirm+K (random K in 77..136, or none); Bombette: Strategies -> Do Nothing (random delay, or
      planned); enemy turn (4 copy rolls) up to Mario's T2 menu.
  T2 (T2=1): Z, Bombette Power Bomb (mash A every 2nd frame), then if any enemy is left Mario Jump (A, A, first
      target; with one Duplighost left that is it) with the action command pressed at +56; then to the next menu / end.
usage (from anywhere): M64P_DBG=1 [T2=1] python3 dc_turns.py SEEDHEX DSEED MODE OUT.json
  MODE blind: random delays (2-40 frames) before each confirm, random popup policy.
       plan:  the Do Nothing confirm goes on the first frame >= (earliest + 0..20 random) where dc_model predicts all 4
              copies, computed from gRandSeed and the coin phase AT THE CHARGE CONFIRM (what a lock knows) and the
              Charge confirm frame; no further reads.
DIAGNOSTIC RAM write: gRandSeed (both copies) = SEEDHEX right after the state load (stands for an unknown run).
State: states/boss_2402_dchg_menu.st (DIAGNOSTIC SETUP: AC=1 PARTNER=3 BRANK=1 BADGES=10c,e4,112,11f BOOTS=2 FP=10
NOFS=1 SUF=_dchg boss_battle_start_setup.py 2402; Bombette Super, Super Jump Charge, Power Bounce, Close Call, Speedy
Spin, Ultra Boots, 10 HP / 10 FP, the Jr. Troopa route state's setup)."""
import sys, os, json, random, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dc_model as DM
JM = DM.JM
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import SEED, SEED2, RAND_INT
seed, dseed, MODE, OUT = int(sys.argv[1], 16), int(sys.argv[2]), sys.argv[3], sys.argv[4]
rnd = random.Random(dseed * 7919 + seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/dct%d' % os.getpid())
e.load('states/boss_2402_dchg_menu.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; confirms = []; S = {'nc': None}; out = {'seed': seed, 'dseed': dseed, 'mode': MODE}
def actors():
    r = []
    for i in range(24):
        p = e.u32(BSTATUS + 0xE0 + 4 * i)
        if 0x80000000 < p < 0x80800000: r.append([i, e.u8(p + 0x136), e.s8(p + 0x1B8)])
    return r
def step(b=0, x=0, y=0):
    s0 = e.u32(SEED); e.step(b, x, y, 2); s1 = e.u32(SEED); f = len(log); calls = []; s = s0
    for v in e.dbg_events():
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        s, val = JM.rand_int(s, mx); calls.append([v['ra'], mx, val])
        if v['ra'] == 0x80146D54: S['nc'] = f + (48 if val >= 70 else 24)
    log.append({'s0': s0, 's1': s1, 'c': calls, 'bs': bstate(e), 'hp': e.s8(PLAYER_DATA + 2), 'b': b})
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x if i == 0 else 0, y if i == 0 else 0)
def until(states, cap=4000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
try:
    w(20); w(22, A); w(15, 0, 0, -70); w(15, 0, 0, -70); w(20, A); until([17], cap=60)   # Jump -> Super Charge -> Mario
    w(rnd.randint(2, 40)); cc = len(log)
    lock = {'s': e.u32(SEED), 'nc': S['nc'] if S['nc'] is not None and S['nc'] >= cc else None}   # what the rays give
    confirms.append([cc, 'Charge']); step(A)
    pol = rnd.choice(['none', 'early', 'mid', 'late']); K = {'none': None, 'early': rnd.randint(77, 82), 'mid': rnd.randint(83, 110), 'late': rnd.randint(111, 136)}[pol]
    if K is not None:
        while len(log) < cc + K: step()
        confirms.append([len(log), 'popup A']); step(A)
    until([14]); out['partner_menu'] = len(log) - cc
    w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70)                                   # Strategies -> Do Nothing
    earliest = len(log) + 2
    if MODE == 'plan':
        if lock['nc'] is None: raise RuntimeError('no coin seen before the Charge confirm (q unknown here)')
        m = JM.Sim(lock['s'], lock['nc']).add(cc, 'charge'); m.run(cc, earliest)
        start = earliest + rnd.randint(0, 20)
        m.run(earliest, start); T = DM.table(m.s, m.nc, start, 90)
        pick = next((start + i for i, c in enumerate(T) if c == 4), None)
        out['plan'] = {'start': start - cc, 'pick': None if pick is None else pick - cc, 'table': T}
        delay = (pick if pick is not None else start) - len(log)
    else:
        delay = rnd.randint(2, 40)
    w(delay); confirms.append([len(log), 'Do Nothing']); step(A)
    until([13, 33, 27, 32], cap=3000); w(20)
    out['t1'] = {'hp': log[-1]['hp'], 'actors': actors()}
    if os.environ.get('T2') and bstate(e) == 13:
        w(30, Z); w(15, 0, 0, -70); w(25, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
        w(rnd.randint(2, 20)); confirms.append([len(log), 'Power Bomb']); step(A)
        until([13, 33], mash=True); w(30); out['after_pb'] = {'bs': bstate(e), 'actors': actors()}
        if bstate(e) == 13:
            w(22, A); w(20, A); until([17], cap=60); w(rnd.randint(2, 20))
            # the Jump action command: Mario runs up, then a fixed 18-frame jump arc; the window is jump start +16..+19
            # (measured: start +17 -> both hits). Press on the 17th frame after his y first leaves the floor.
            mp = e.u32(BSTATUS + 0xD8); fy = lambda: struct.unpack('<f', struct.pack('<I', e.u32(mp + 0x148)))[0]
            p = len(log); confirms.append([p, 'Jump']); step(A); k0 = None
            for k in range(1, 300):
                if k0 is None and fy() > 0.5: k0 = k - 1
                step(A if (k0 is not None and k == k0 + 17) else 0)
                if bstate(e) in (33,): break
            out['jump_start'] = k0
            out['after_jump'] = {'bs': bstate(e), 'actors': actors(), 'hp': log[-1]['hp']}
except Exception as ex:
    out['error'] = str(ex)
out['lock'] = lock if 'lock' in dir() else None
out['confirms'] = confirms; out['log'] = log
json.dump(out, open(OUT, 'w'))
rolls = [(f, x[2]) for f, fr in enumerate(log) for x in fr['c'] if x[0] == 0x802D46E0]
nd = [f for f, n in confirms if n == 'Do Nothing']
print('%08x d%d %s | menu +%s | rolls %s | copies %d | plan %s | t2 %s %s | err %s' % (
    seed, dseed, MODE, out.get('partner_menu'), [(f - nd[0], v) for f, v in rolls][:6] if nd else rolls,
    sum(1 for f, v in rolls[:4] if v < 600), {k: v for k, v in out.get('plan', {}).items() if k != 'table'},
    out.get('after_pb', {}).get('bs'), out.get('after_jump', {}).get('bs'), out.get('error')))
