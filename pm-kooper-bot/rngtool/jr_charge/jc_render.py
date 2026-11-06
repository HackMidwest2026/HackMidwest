"""Play the Jr. Troopa route (the jc_turns.py inputs: T1 Charge; Bomb - T2 Bomb; Whacka - T3 Charge; Bomb - T4 Bomb;
Maple Syrup - T5 Charge; Do Nothing - T6 Power Bounce) with GIVEN confirm frames, logging every gRandSeed draw per frame
(the jc_turns.py log format) and optionally a Glide64 screenshot per frame, for the page's frame-fed end-to-end test
(../test_jr_page.js) and its emulator press check.
usage: M64P_DBG=1 python3 jc_render.py SEEDHEX SPEC.json OUT.json [SHOTDIR]
  SPEC: {"delay": {name: frames idle on that confirm's screen before A (default 25)},
         "at": {name: log frame of that confirm's A (a planned press; the screen must be up by then)},
         "popup": {"T1": K or null, "T3": ..., "T5": ...} (the Charge's "+3" popup A at confirm + K; null: none),
         "stop": name (stop STOPWAIT frames after that confirm's target screen opens, without pressing it), "stopwait": 150}
  names: T1 Charge, T1 Bomb, T2 Bomb, T2 Whacka, T3 Charge, T3 Bomb, T4 Bomb, T4 Syrup, T5 Charge, T5 Nothing, T6 Bounce
Screenshots (env SHOTFROM / SHOTTO: only those log frames): SHOTDIR/s%04d.png after log frame i's step (so it shows frame i's picture); needs DISPLAY (Xvfb) and
M64P_GFX = the glide64mk2 plugin. Starts from states/boss_0207_route_menu.st (T1 menu), log frame 0 = the first step.
DIAGNOSTIC RAM write: gRandSeed (both copies) = SEEDHEX right after the state load (stands for an unknown run)."""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc_model as JM
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import SEED, SEED2, RAND_INT
seed, SPEC, OUT = int(sys.argv[1], 16), json.load(open(sys.argv[2])), sys.argv[3]
SHOT = sys.argv[4] if len(sys.argv) > 4 else None
SHOTFROM, SHOTTO = int(os.environ.get('SHOTFROM', 0)), int(os.environ.get('SHOTTO', 10 ** 9))   # screenshots only for these log frames
if SHOT: os.makedirs(SHOT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jcr%d' % os.getpid())
if SHOT:
    for i in range(30): e.step(0, 0, 0, 2)             # the video plugin up before the state load
e.load('states/boss_0207_route_menu.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
log = []; confirms = []; screens = {}
jrhp = lambda: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)
class Stop(Exception): pass
def step(b=0, x=0, y=0):
    s0 = e.u32(SEED); e.step(b, x, y, 2); s1 = e.u32(SEED); f = len(log); calls = []; s = s0
    for v in e.dbg_events():
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        s, val = JM.rand_int(s, mx); calls.append([v['ra'], mx, val])
    log.append({'s0': s0, 's1': s1, 'c': calls, 'bs': bstate(e), 'hp': e.s8(PLAYER_DATA + 2), 'jr': jrhp(), 'b': b})
    if SHOT and SHOTFROM <= f <= SHOTTO: subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/s%04d.png' % (SHOT, f)], check=True)
def w(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x if i == 0 else 0, y if i == 0 else 0)
def until(states, cap=4000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
def press(name, turn):
    screens[name] = len(log)
    if SPEC.get('stop') == name:
        w(SPEC.get('stopwait', 150)); raise Stop()
    if name in SPEC.get('at', {}):
        d = SPEC['at'][name] - len(log)
        if d < 2: raise RuntimeError('%s planned at %d but its screen is up only at %d' % (name, SPEC['at'][name], len(log)))
    else: d = SPEC.get('delay', {}).get(name, 25)
    w(d); confirms.append((len(log), name, turn)); step(A)
def charge(tn, first_down=True):
    if first_down: w(12, 0, 0, -70)
    w(22, A); w(15, 0, 0, -70); w(15, 0, 0, -70); w(20, A)        # Jump, down 2 = Super Charge, target on Mario
    until([17], cap=60); press(tn + ' Charge', 'charge')
    c = confirms[-1][0]; K = SPEC.get('popup', {}).get(tn)
    if K is not None:
        while len(log) < c + K: step()
        confirms.append((len(log), tn + ' popup A', None)); step(A)
    until([14])
out = {'seed': seed, 'spec': SPEC, 'start': 't1'}
try:
    w(20)
    charge('T1', first_down=False)
    w(10); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T1 Bomb', 'bomb_t1')
    until([13], mash=True); w(20)
    w(30, Z); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T2 Bomb', 'bomb'); until([13], mash=True); w(15)
    w(15, 0, 0, 70); w(25, A); w(25, A); until([17], cap=60); press('T2 Whacka', 'whacka')
    until([13], cap=4000); w(20)
    charge('T3')
    w(10); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T3 Bomb', 'bomb_cc')
    until([13, 27, 32], mash=True); until([13]); w(20); out['t4'] = [log[-1]['hp'], jrhp()]
    w(30, Z); w(25, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60); press('T4 Bomb', 'bomb'); until([13], mash=True); w(15)
    w(15, 0, 0, 70); w(25, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
    press('T4 Syrup', 'syrup_cc' if out['t4'][0] < 6 else 'syrup_hit')
    until([13, 27, 32]); until([13]); w(20); out['t5'] = [log[-1]['hp'], jrhp()]
    charge('T5')
    w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70)
    hp5 = log[-1]['hp']
    press('T5 Nothing', 'nothing_cc' if hp5 < 6 else 'nothing_hit')
    until([13, 27, 32]); until([13]); w(20); out['t6'] = [log[-1]['hp'], jrhp()]
    w(22, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
    press('T6 Bounce', 'pb')
    p = confirms[-1][0]
    for k in range(1, 240): step(A if (len(log) - p) in {47, 74, 102, 130, 158, 186, 214} else 0)
    w(60); out['end'] = [log[-1]['hp'], jrhp()]
except Stop:
    out['stopped'] = SPEC.get('stop')
except Exception as ex:
    out['error'] = str(ex)
out['confirms'] = [[f, n, t] for f, n, t in confirms]; out['screens'] = screens; out['log'] = log
json.dump(out, open(OUT, 'w'))
print('%08x | t4 %s t5 %s t6 %s end %s | %d frames | stopped %s err %s | confirms %s' % (seed, out.get('t4'), out.get('t5'), out.get('t6'), out.get('end'), len(log), out.get('stopped'), out.get('error'), [(f, n) for f, n, t in confirms]))
