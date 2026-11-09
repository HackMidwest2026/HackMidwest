"""v85: the Normal Boots Jr. Troopa route played in the emulator (JP, debug core), every random draw logged per frame, for
the page's model of Goombario's Charge (nb_gch / the cancel A), Maple Syrup and Headbonk (pmrng_core.js TURNS) and the
test that checks it frame by frame (../test_nb_cc_model.js, fixtures/nb_cc_logs.json).
Route: T1 Super Charge; Charge - T2 Super Charge; Charge (Close Call) - T3 Maple Syrup; Charge (Close Call) - T4 Super
Charge; Charge (Close Call) - T5 Super Charge; Headbonk (Close Call) - T6 Whacka; Do Nothing - T7 Power Bounce (to the end of the bounces).
Every confirm after a random 2-40 frame wait; the Super Charge "+3" popup closed with A at a random frame (or not);
Goombario's Charge cancelled with A at confirm + K (K random in 73..132, or none). MODE=plan: on the Close Call turns the
deciding input (K, or the Headbonk confirm's wait) is the first one in a random order that dodges (tried from a saved state:
what a lock knows); MODE=random: random (the run stops at a death). Mario starts at 10 HP (Jr. Troopa's T1 hit takes him
under 6: Danger). Headbonk's action command pressed on each window's first frame (env ACLATE=n: n frames later).
DIAGNOSTIC RAM writes: gRandSeed (both copies) = SEEDHEX and the item list (Whacka's Bump, Maple Syrup, 2 Life Shrooms)
right after the state load.
Run from /tmp/claude-0/pm/bot1 with M64P_DBG=1:  python3 .../jr_route_log.py SEEDHEX DSEED OUT.json  (env MODE, ST)"""
import sys, os, json, random
sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import SEED, SEED2, RAND_INT, rand_int
SB = 0x8010F118
seed, dseed, OUT = int(sys.argv[1], 16), int(sys.argv[2]), sys.argv[3]
MODE = os.environ.get('MODE', 'plan'); rnd = random.Random(dseed); ACLATE = int(os.environ.get('ACLATE', '0'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nbr%d' % os.getpid()); TMP = '/dev/shm/pmbot/nbr%d_trial.st' % os.getpid()
e.load(os.environ.get('ST', 'states/boss_0207_nbg_menu.st')); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
for i, it in enumerate([0x93, 0xA3, 0x95, 0x95]): e.w16(PLAYER_DATA + 0x1B4 + 2 * i, it)   # DIAGNOSTIC: items Whacka's Bump, Maple Syrup, 2 Life Shrooms
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; ev = []
jrhp = lambda: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)
def step(b=0, x=0, y=0):
    s0 = e.u32(SEED); e.step(b, x, y, 2); calls = []
    for v in e.dbg_events():
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        if v['ra'] == 0x800269AC: continue
        calls.append(['%08x' % v['ra'], mx])
    log.append({'s0': '%08x' % s0, 's1': '%08x' % e.u32(SEED), 'c': calls, 'bs': bstate(e), 'hp': e.s8(PLAYER_DATA + 2), 'fp': e.s8(PLAYER_DATA + 5), 'jr': jrhp(), 'dis': e.s8(SB + 0x47), 'b': b})
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x if i == 0 else 0, y if i == 0 else 0)
def until(states, cap=4000):
    for f in range(cap):
        if bstate(e) in states: return f
        step()
    raise RuntimeError('state %d' % bstate(e))
def mark(name, **kw): d = dict(f=len(log), name=name); d.update(kw); ev.append(d)
def confirm(name, delay=None):
    w(rnd.randint(2, 40) if delay is None else delay); mark(name); step(A)
def roll_at(k_from, cap=400):
    """steps until the Close Call draw (caller 0x80277518); returns its value or None (from the logged seeds)"""
    for f in range(cap):
        n = len(log); step()
        s = int(log[n]['s0'], 16)
        for ra, mx in log[n]['c']:
            s, v = rand_int(s, mx)
            if ra == '80277518': return v
    return None
def trial(cands, play):
    """MODE=plan: the first candidate (in the given order) whose Close Call dodges; play(c) plays it from the saved state"""
    if MODE != 'plan': return cands[0]
    n0 = len(log); e.save(TMP)
    for c in cands:
        play(c); v = roll_at(0)
        e.load(TMP); del log[n0:]; e.dbg_events()
        if v is not None and v < 30: return c
    return cands[0]
def super_charge(tn, after_item):
    until([13]); w(20)
    if after_item: w(12, 0, 0, -70)                        # the wheel remembers Items after Maple Syrup
    w(22, A); w(15, 0, 0, -70); w(15, 0, 0, -70); w(20, A); until([17], cap=60); confirm(tn + ' Super Charge')
    c = ev[-1]['f']; K = rnd.choice([None, rnd.randint(77, 136)])
    if K is not None:
        while len(log) < c + K: step()
        mark(tn + ' popup A', K=K); step(A)
    until([14])
def maple(tn):
    until([13]); w(20)
    w(15, 0, 0, 70); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); confirm(tn + ' Maple Syrup'); until([14])
def gcharge(tn, cc):
    w(10); w(25, A); w(25, 0, 0, -70); w(25, 0, 0, -70); w(10, A); until([17], cap=60); confirm(tn + ' Goombario Charge'); G = ev[-1]['f']; ev[-1]['move'] = e.s16(BSTATUS + 0x17C)
    Ks = [None] + list(range(73, 133)); rnd.shuffle(Ks)
    def play(K):
        if K is None: return
        while len(log) < G + K: step()
        step(A)
    K = trial(Ks, play) if cc else Ks[0]
    if K is not None:
        while len(log) < G + K: step()
        mark(tn + ' cancel A', K=K); step(A)
    ev[-1]['K'] = K
def headbonk(tn):
    w(10); w(25, A); w(25, A); until([17], cap=60)
    n0 = len(log); e.save(TMP); Ds = list(range(2, 41)); rnd.shuffle(Ds)
    def play(d):
        w(d); step(A); ac()
    if MODE == 'plan':
        best = None
        for d in Ds:
            play(d); v = roll_at(0); e.load(TMP); del log[n0:]; e.dbg_events()
            if v is not None and v < 30: best = d; break
        d = best if best is not None else Ds[0]
    else: d = Ds[0]
    confirm(tn + ' Headbonk', d); ac()
def ac():
    armed = True
    for f in range(300):
        q = e.s8(BSTATUS + 0x81); pr = q == -1 and armed and f > 5
        if q == -1 and armed and f > 5:
            armed = False
            for i in range(ACLATE): step()
            mark('ac'); step(A); continue
        if q != -1: armed = True
        step()
        if bstate(e) in (20, 21, 23): break
def jr_turn(tn):
    for f in range(3000):
        if bstate(e) == 13 or e.s8(PLAYER_DATA + 2) <= 0: break
        step()
    mark(tn + ' end', hp=e.s8(PLAYER_DATA + 2), jr=jrhp())
    if e.s8(PLAYER_DATA + 2) <= 0: raise RuntimeError('Mario died on ' + tn)
out = dict(seed='%08x' % seed, dseed=dseed, mode=MODE, aclate=ACLATE)
try:
    super_charge('T1', False); gcharge('T1', False); jr_turn('T1')
    super_charge('T2', False); gcharge('T2', True); jr_turn('T2')
    maple('T3'); gcharge('T3', True); jr_turn('T3')
    super_charge('T4', True); gcharge('T4', True); jr_turn('T4')
    super_charge('T5', False); headbonk('T5'); jr_turn('T5')
    until([13]); w(20)
    w(15, 0, 0, 70); w(25, A); w(25, A); until([17], cap=60); confirm('T6 Whacka'); until([14])
    w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70); confirm('T6 Do Nothing'); jr_turn('T6')
    until([13]); w(20); w(12, 0, 0, -70); w(22, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); confirm('T7 Power Bounce'); ac()
    for f in range(400): step()
except Exception as ex: out['error'] = str(ex)
out.update(ev=ev, log=log)
json.dump(out, open(OUT, 'w'))
cc = [(i, rand_int(int(x['s0'], 16), 100)) for i, x in enumerate(log) for c in x['c'] if c[0] == '80277518']
print('%08x d%d: %d frames, err %s, events %s' % (seed, dseed, len(log), out.get('error'), [(x['name'], x['f'], x.get('K')) for x in ev if 'end' in x['name'] or 'cancel' in x['name'] or 'Headbonk' in x['name']]), flush=True)
