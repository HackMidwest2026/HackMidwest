"""v85: Goombario's Charge (and Headbonk) as the last action before the enemy's turn, Normal Boots route (JP, emulator,
debug core). From a state on Mario's T1 menu: Mario's Super Charge (no popup A unless MPOP), Goombario's move confirmed
GD frames after his menu opens (log frame G), then (Charge) A on G + K (K < 0: no A, the message box runs out), and the
enemy's turn to the next Mario menu (or Mario's death). Logged per frame: every rand_int (caller, max, value), gBattleState,
Mario's HP, gStatusBar hidden / drawPosY / disabled (0x8010F118 +0x3A / +0x36 / +0x47, JP, from close_status_bar), the partner's charge.
DIAGNOSTIC writes (setup only, labelled): gRandSeed (both copies) after the load; Mario's HP (argv HP) at the first menu;
optional the partner's charge (isGlowing, env GLOW) and the enemy's HP (env EHP) before the move.
Run from /tmp/claude-0/pm/bot1 with M64P_DBG=1:
  PYTHONPATH=. python3 .../gch_log.py STATE SEEDHEX HP MOVE K GD OUT.json   (MOVE charge | headbonk; env MPOP=k, TURNS=n)"""
import sys, os, json
sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import SEED, SEED2, RAND_INT, rand_int
SB = 0x8010F118
st, seed, HP, MOVE, K, GD, OUT = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/gch%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
if HP > 0: e.w8(PLAYER_DATA + 2, HP)                       # DIAGNOSTIC: Mario's HP
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; marks = {}; s = seed
part = lambda: e.u32(BSTATUS + 0xDC)
def step(b=0, x=0, y=0):
    global s
    e.step(b, x, y, 2); calls = []
    for v in e.dbg_events():
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        if v['ra'] == 0x800269AC: continue
        calls.append(['%08x' % v['ra'], mx])
    p = part()
    log.append({'c': calls, 'bs': bstate(e), 'hp': e.s8(PLAYER_DATA + 2), 'hid': e.u8(SB + 0x3A), 'y': e.s16(SB + 0x36), 'dis': e.s8(SB + 0x47),
                'glow': e.s8(p + 0x220) if 0x80000000 < p < 0x80800000 else None, 'b': b, 'seed': '%08x' % e.u32(SEED)})
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x if i == 0 else 0, y if i == 0 else 0)
def until(states, cap=3000):
    for f in range(cap):
        if bstate(e) in states: return f
        step()
    raise RuntimeError('state %d' % bstate(e))
out = dict(state=os.path.basename(st), seed='%08x' % seed, hp=HP, move=MOVE, K=K, GD=GD)
try:
    for turn in range(int(os.environ.get('TURNS', '1'))):
        until([13]); w(15)
        w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); marks.setdefault('mario', []).append(len(log)); step(A)   # Super Charge
        if os.environ.get('MPOP'):
            k = len(log) - 1 + int(os.environ['MPOP'])
            while len(log) < k: step()
            step(A)
        until([14]); marks.setdefault('pmenu', []).append(len(log))
        if os.environ.get('GLOW'): e.w8(part() + 0x220, int(os.environ['GLOW']))          # DIAGNOSTIC: the partner's charge
        if os.environ.get('EHP'): e.w8(e.u32(BSTATUS + 0xE0) + 0x1B8, int(os.environ['EHP']))   # DIAGNOSTIC: the enemy's HP
        w(10); w(25, A)                                             # Abilities
        if MOVE == 'charge':
            w(25, 0, 0, -70); w(25, 0, 0, -70); w(10, A); until([17], cap=60); w(GD)   # Charge, then its target screen (Goombario)
            marks.setdefault('G', []).append(len(log)); out.setdefault('moveID', []).append(e.s16(BSTATUS + 0x17C)); step(A)
            if K >= 0:
                k = marks['G'][-1] + K
                while len(log) < k: step()
                marks.setdefault('P', []).append(len(log)); step(A)
        else:
            w(25, A); until([17], cap=60); w(GD)
            marks.setdefault('G', []).append(len(log)); out.setdefault('moveID', []).append(e.s16(BSTATUS + 0x17C)); step(A)
            # Headbonk's action command: A on the first frame of each window (actionQuality -1), as in pb_nb_log.py
            armed = True
            for f in range(400):
                q = e.s8(BSTATUS + 0x81); pr = q == -1 and armed and f > 5
                if pr: armed = False; marks.setdefault('ac', []).append(len(log))
                if q != -1: armed = True
                step(A if pr else 0)
                if bstate(e) not in (17, 18, 19, 20, 21) and f > 30: break
        for f in range(2500):
            if bstate(e) == 13 or e.s8(PLAYER_DATA + 2) <= 0: break
            step()
        marks.setdefault('end', []).append(len(log))
except Exception as ex: out['error'] = str(ex)
out.update(marks=marks, log=log, ehp=e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8), hpEnd=e.s8(PLAYER_DATA + 2))
json.dump(out, open(OUT, 'w'))
G = marks.get('G', [None])[-1]
cc = [i for i, x in enumerate(log) for c in x['c'] if c[0] == '80277518']
print('seed %08x K %d GD %d: G %s cc %s (rel %s) hp %d ehp %d err %s' % (seed, K, GD, G, cc, [i - G for i in cc] if G else None, out['hpEnd'], out['ehp'], out.get('error')), flush=True)
