"""Play the Jr. Troopa route's Charge turns in the emulator and log every gRandSeed draw per frame.
  T3: Super Charge -> (popup A at confirm+K or none) -> Bombette Bomb -> Jr. Troopa's hit (Close Call at 2 HP)
  T4: Bomb -> Maple Syrup -> hit;  T5: Super Charge -> (popup) -> Bombette do nothing -> hit;  T6: Power Bounce.
usage: M64P_DBG=1 python3 jc_turns.py START SEEDHEX DSEED MODE OUT.json
  START: t3 (states/jr_t3_menu.st), t5 (states/jr_t5_menu.st) or t1 (states/boss_0207_route_menu.st: T1 Charge + Bomb,
         T2 Bomb + Whacka, then T3 as above)
  MODE: blind = random delays (0-40 frames) on every confirm and a random popup policy;
        plan  = the confirms that decide a roll (T3 Bomb, T4 Syrup, T5 do nothing, T6 Power Bounce) are put on the
                earliest frame of a 30-frame window where jc_model.py predicts the route's outcome (Close Call /
                6+ bounces) from gRandSeed read at the start of the window (what a lock would know), the others random.
DIAGNOSTIC RAM write: gRandSeed (both copies) = SEEDHEX right after the state load (stands for an unknown run).
Nothing else is written. Log: per frame s0 (seed before), calls [ra, max, value], bs, Mario HP, Jr. HP; confirms."""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc_model as JM
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import SEED, SEED2, RAND_INT
START, seed, dseed, MODE, OUT = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), sys.argv[4], sys.argv[5]
rnd = random.Random(dseed * 7919 + seed)
ST = {'t1': 'states/boss_0207_route_menu.st', 't3': 'states/jr_t3_menu.st', 't5': 'states/jr_t5_menu.st'}[START]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jct%d' % os.getpid())
e.load(ST); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; confirms = []; S = {'nc': None, 's': seed}; plans = []
jrhp = lambda: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)
def step(b=0, x=0, y=0):
    s0 = e.u32(SEED); e.step(b, x, y, 2); s1 = e.u32(SEED); f = len(log); calls = []; s = s0
    for v in e.dbg_events():
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        s, val = JM.rand_int(s, mx); calls.append([v['ra'], mx, val])
        if v['ra'] == 0x80146D54: S['nc'] = f + (48 if val >= 70 else 24)
    log.append({'s0': s0, 's1': s1, 'c': calls, 'bs': bstate(e), 'hp': e.s8(PLAYER_DATA + 2), 'jr': jrhp(), 'b': b})
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x if i == 0 else 0, y if i == 0 else 0)
def until(states, cap=4000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
def model_at(f):
    """the model's state at the start of frame f (now), with every earlier confirm's events still to come"""
    m = JM.Sim(e.u32(SEED), S['nc'] if S['nc'] is not None and S['nc'] >= f else f + 10 ** 6)
    for g, name, turn in confirms:
        if turn: m.add(g, turn)
    return m
def press(name, turn, want=None, horizon=None):
    """A on a frame chosen by MODE; turn = jc_model TURNS key for this confirm's events (or None)"""
    f0 = len(log) + 2
    if MODE == 'plan' and want:
        base = model_at(len(log)); base.run(len(log), f0); pick = None
        for d in range(f0, f0 + 30):
            m = base.copy().add(d, turn); m.run(d, d + horizon)   # frames before d already simulated in base
            if want(m.rolls): pick = d; break
            base.frame(d)
        plans.append([name, f0, pick])
        delay = (pick - len(log)) if pick is not None else rnd.randint(2, 31)
    else:
        delay = rnd.randint(2, 40)
    w(delay); confirms.append((len(log), name, turn)); step(A)
def charge(first_down=True):
    if first_down: w(12, 0, 0, -70)
    w(22, A); w(15, 0, 0, -70); w(15, 0, 0, -70); w(20, A)        # Jump, down 2 = Super Charge, target on Mario
    until([17], cap=60); press('Charge', 'charge')
    c = confirms[-1][0]; pol = rnd.choice(['none', 'early', 'mid', 'late'])
    K = {'none': None, 'early': rnd.randint(77, 82), 'mid': rnd.randint(83, 110), 'late': rnd.randint(111, 136)}[pol]
    if K is not None:
        while len(log) < c + K: step()
        confirms.append((len(log), 'popup A', None)); step(A)
    until([14])
out = {'seed': seed, 'dseed': dseed, 'mode': MODE, 'start': START}
try:
    w(20)
    if START == 't1':
        charge(first_down=False)
        w(10); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T1 Bomb', 'bomb_t1')
        until([13], mash=True); w(20); out['t2'] = [log[-1]['hp'], jrhp()]
        w(30, Z); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T2 Bomb', 'bomb'); until([13], mash=True); w(15)
        w(15, 0, 0, 70); w(25, A); w(25, A); until([17], cap=60); press('T2 Whacka', 'whacka')
        until([13], cap=4000); w(20); out['t3'] = [log[-1]['hp'], jrhp()]
    if START in ('t1', 't3'):
        charge()
        w(10); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
        press('T3 Bomb', 'bomb_cc', lambda R: R.get('cc', 99) < 30, 180)
        until([13, 27, 32], mash=True); until([13]); w(20); out['t4'] = [log[-1]['hp'], jrhp()]
        w(30, Z); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T4 Bomb', 'bomb'); until([13], mash=True); w(15)
        w(15, 0, 0, 70); w(25, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
        press('T4 Syrup', 'syrup_cc' if out['t4'][0] < 6 else 'syrup_hit', (lambda R: R.get('cc', 99) < 30) if out['t4'][0] < 6 else None, 164)
        until([13, 27, 32]); until([13]); w(20); out['t5'] = [log[-1]['hp'], jrhp()]
    charge()
    w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70)
    hp5 = log[-1]['hp']
    press('T5 Nothing', 'nothing_cc' if hp5 < 6 else 'nothing_hit', (lambda R: R.get('cc', 99) < 30) if hp5 < 6 else None, 27)
    until([13, 27, 32]); until([13]); w(20); out['t6'] = [log[-1]['hp'], jrhp()]
    w(22, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
    press('T6 Bounce', 'pb', lambda R: JM.pb_hits(R) >= 6, 160)
    p = confirms[-1][0]
    for k in range(1, 240): step(A if (len(log) - p) in {47, 74, 102, 130, 158, 186, 214} else 0)
    w(60); out['end'] = [log[-1]['hp'], jrhp()]
except Exception as ex:
    out['error'] = str(ex)
out['confirms'] = [[f, n, t] for f, n, t in confirms]; out['plans'] = plans; out['log'] = log
json.dump(out, open(OUT, 'w'))
print('%08x d%d %s %s | t4 %s t5 %s t6 %s end %s | plans %s | err %s' % (seed, dseed, START, MODE, out.get('t4'), out.get('t5'), out.get('t6'), out.get('end'), plans, out.get('error')))
