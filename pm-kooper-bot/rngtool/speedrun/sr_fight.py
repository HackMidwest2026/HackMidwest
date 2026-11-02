"""Emulator "speedrun" of the fights, closed loop with the Time Out Timer page (step 2: Duplighosts -> Jr. Troopa).
The emulator's video goes frame by frame into the page (sr_live.js, simulated 29.97 fps clock); the runner presses on
the page's final beep. Truth: every game frame's RNG, every rand_int call (debug core), the game's outcome (copies,
Mario's HP after Jr. Troopa's attack, Jr. Troopa's HP after the bounces).
DIAGNOSTIC: the starting seed of each fight is set to a random value (an unknown run); the Jr. Troopa fight starts from
a savestate (the overworld between the fights is not played: the page sees the coin gone and a new segment, as when
walking there with the bar closed).
Runner model: presses A on the game frame of the final beep + OFFSET (a calibrated runner) + jitter (JIT: 'none',
'1' = uniform -1/0/+1 frames). Fast Whacka: A on the item, then A again FAST frames later (the hand may not show).
usage: DISPLAY=:93 M64P_GFX=<glide64mk2 .so> M64P_DATA=<dir with Glide64mk2.ini> M64P_DBG=1 python3 sr_fight.py OUT SEED
env FIGHTS=dup,jr  JIT=none|1  OFFSET=0  FAST=2  SR_SET='{"pfix":"0"}' (page settings)"""
import subprocess, sys, os, io, json, random
import numpy as np
from PIL import Image, ImageFilter
SRDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from btl import *
from rngsim import *
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True); SEED0 = int(sys.argv[2], 16)
rnd = random.Random(SEED0)
FIGHTS = os.environ.get('FIGHTS', 'dup,jr').split(','); JIT = os.environ.get('JIT', 'none'); OFFSET = int(os.environ.get('OFFSET', '0'))
FAST = int(os.environ.get('FAST', '2')); FMS = 1001 / 30
e = Emu('pm-jp.z64', '/dev/shm/pmbot/srf%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
node = subprocess.Popen(['node', os.path.join(SRDIR, "sr_live.js")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
def page(o):
    node.stdin.write(json.dumps(o) + '\n'); node.stdin.flush(); l = node.stdout.readline()
    if not l: raise RuntimeError('page host died')
    return json.loads(l)
y4m = open(OUT + '/run.mjpeg', 'wb')   # the frames the page saw (JPEG stream; ffmpeg -f mjpeg -framerate 30000/1001)
VF = [0]; truth = []; R = [None]; events = []; LASTIM = [None]; rolls = []; S = [0]
def grab():
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '640x480!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    im = Image.frombytes('RGB', (640, 480), raw).filter(ImageFilter.GaussianBlur(0.5)); LASTIM[0] = im
    b = io.BytesIO(); im.save(b, 'JPEG', quality=85); jpg = b.getvalue(); y4m.write(jpg)
    return jpg
import base64
def step(b=0, x=0, y=0):
    prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    calls = []
    for ev in e.dbg_events():
        mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        S[0], v = rand_int(S[0], mx); calls.append([mx, v, ev['ra']])
    S[0] = cur
    VF[0] += 1
    r = page({'f': VF[0], 'jpg': base64.b64encode(grab()).decode()})
    R[0] = r
    if VF[0] % 300 == 0: print('   f%d %s lock=%s shines=%s step=%s plan=%s turns=%s' % (VF[0], CUR[0], r.get('lock'), r.get('shines'), r.get('step'), bool(r.get('plan')), r.get('turns')), flush=True)
    truth.append([VF[0], prev, k, bstate(e), b, calls if any(c[0] != 100 for c in calls) else len(calls)])
    return r
def wait(n):
    for i in range(n): step()
def until(states, cap=3000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
def oracle(seedBL):
    """step number whose RNG run contains seedBL (the coin draw that is the plan's frame 0)"""
    for n, prev, k, *_ in reversed(truth):
        t = prev
        for i in range(k):
            if t == seedBL: return n
            t = adv(t)
    return None
def press_on_beeps(label, cap=4000, also=None):
    """wait on the target screen for the page's beeps; press A on the final beep's frame (+ OFFSET + jitter)"""
    for i in range(cap):
        r = R[0]; P = r and r.get('plan')
        if P and P['tPress'] > r['t'] + FMS:
            fb = (P['tPress'] - T0[0]) / FMS
            j = 0 if JIT == 'none' else rnd.choice([-1, 0, 1])
            at = int(round(fb + OFFSET)) + j
            if at > VF[0] + 1:
                if also: also()
                while VF[0] + 1 < at:
                    step(); Q = R[0].get('plan')
                    if not Q or Q['tPress'] != P['tPress']: break      # the beeps were cancelled or moved: listen again
                if VF[0] + 1 < at: continue
                L = oracle(P['seedBL']); ideal = L + P['target'] if L else None
                r = step(A)
                ev = {'press': label, 'step': VF[0], 'beepFrame': round(fb, 2), 'jitter': j, 'ideal': ideal, 'off_vs_ideal': VF[0] - ideal if ideal else None,
                      'target': P['target'], 'window': P['w'], 'prof': P['prof']}
                events.append(ev); print('  PRESS', json.dumps(ev), flush=True); return ev
        step()
    events.append({'press': label, 'noplan': True}); print('  no plan for', label, flush=True); return None
T0 = [None]
def setT0():
    T0[0] = page({'cmd': 'eval', 'js': 'window.__t0'})['r']
setT0()
def snap(name): LASTIM[0].save(OUT + '/' + name + '.png')
def save_target(box, name):
    snap('target_' + name); r = page({'cmd': 'save', 'box': box, 'cat': name}); events.append({'saved': name, 'step': VF[0], 'r': r}); print('  saved target', name, r, flush=True)
SAVED = set()
BOX = {'S': {'x': 0.07, 'y': 0.22, 'w': 0.36, 'h': 0.30}, 'M': {'x': 0.14, 'y': 0.24, 'w': 0.16, 'h': 0.085}, 'K': {'x': 0.14, 'y': 0.24, 'w': 0.16, 'h': 0.085}}   # the Strategies panel; the name box (as the page asks)
if os.environ.get('BOXES'): BOX.update(json.loads(os.environ['BOXES']))
def maybe_save(cat):
    if cat in SAVED: return
    wait(8); save_target(BOX[cat], cat); SAVED.add(cat)
def bt(): return e.u32(BSTATUS + 0xE0)
def hp(): return {'mario': e.s8(PLAYER_DATA + 2), 'fp': e.s8(PLAYER_DATA + 5), 'jr': e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8) if 'jr' in CUR else None}
CUR = ['']
def fight_dup():
    CUR[0] = 'dup'; print('== Duplighosts', flush=True)
    e.load('states/boss_2402_bomb_start.st'); e.step(0, 0, 0, 2)
    s = rnd.getrandbits(32); e.w32(SEED, s); e.w32(SEED2, s); S[0] = s      # DIAGNOSTIC: unknown starting seed
    events.append({'fight': 'dup', 'seed': s, 'step': VF[0]})
    until([13])
    # Mario: Strategies > do nothing; Bombette: Strategies, hand on do nothing (then stand there until the beeps)
    for b, x, y in [(0, 0, 70), (0, 0, 70), (A, 0, 0), (0, 0, -70), (A, 0, 0)]:
        wait(rnd.randint(10, 20)); step(b, x, y)
    until([14]); wait(20)
    for b, x, y in [(0, 0, 70), (A, 0, 0), (0, 0, -70)]:
        wait(rnd.randint(10, 20)); step(b, x, y)
    maybe_save('S')
    ev = press_on_beeps('dup3')
    n0 = len(truth); copies = []
    for i in range(500):
        step()
        for c in (truth[-1][5] if isinstance(truth[-1][5], list) else []):
            if c[0] == 1000 and c[2] == 0x802D46E0: copies.append(c[1])
        if len(copies) >= 4: break
    res = {'vf': VF[0], 'dup_rolls': copies, 'copies': sum(1 for v in copies if v < 600)}
    events.append(res); print('  RESULT', res, flush=True)
    wait(200)
def main():
    e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
    if FIGHTS[0] == 'jr': page({'cmd': 'eval', 'js': 'window.__tot.setStep(1)'})     # after the Duplighosts
    for f in FIGHTS:
        if f == 'dup': fight_dup()
        if f == 'jr': fight_jr()
    y4m.close()
    lg = page({'cmd': 'log'})
    json.dump({'truth': truth, 'events': events, 'page': lg}, open(OUT + '/fight.json', 'w'))
    print('frames', VF[0], 'errs', lg.get('errs'), flush=True)
def gap(n):
    """between the fights (Peach room, walk to Jr. Troopa): the page sees no coin"""
    for i in range(n):
        VF[0] += 1; b = io.BytesIO(); Image.new('RGB', (640, 480)).save(b, 'JPEG', quality=85); y4m.write(b.getvalue())
        R[0] = page({'f': VF[0], 'jpg': base64.b64encode(b.getvalue()).decode()}); truth.append([VF[0], None, None, None, 0, 0])
def jw(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
def confirm_target(cat, label, planned=None, fast=None, after=None):
    """on a target screen: save it the first time; planned: wait for the beeps; else confirm after a human delay"""
    if fast is None: maybe_save(cat)
    if planned: return press_on_beeps(label, also=after)
    if fast is not None: jw(fast)
    else: jw(rnd.randint(6, 20))
    step(A); events.append({'confirm': label, 'step': VF[0], 'cat': cat}); return None
def wait_lock(cap=3000):
    for i in range(cap):
        if R[0] and R[0].get('lock') and not R[0].get('waited'): return i
        step()
    return None
def hpd(): return {'mario': e.s8(PLAYER_DATA + 2), 'jr': e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)}
def cc_result(label, h0):
    for i in range(200):
        if bstate(e) not in (13, 14): break
        step()
    until([13, 14, 27, 32], cap=4000); h1 = hpd(); ok = h1['mario'] == h0['mario']
    res = {'vf': VF[0], 'result': label, 'hp_before': h0, 'hp_after': h1, 'close_call': ok}; events.append(res); print('  RESULT', res, flush=True); return ok
def fight_jr():
    CUR[0] = 'jr'; print('== Jr. Troopa', flush=True)
    gap(int(os.environ.get('GAP', '300')))
    e.load('states/boss_0207_route_menu.st'); e.step(0, 0, 0, 2)
    if os.environ.get('JRX') and 'dup' in FIGHTS:
        # DIAGNOSTIC: the RNG carries on from the Duplighost fight: one step per frame of the gap plus JRX extra draws
        # (the battle's end, cutscenes, the walk: not played here; the real count is unknown)
        s = S[0]
        for i in range(int(os.environ.get('GAP', '300')) + int(os.environ['JRX'])): s = adv(s)
    else: s = rnd.getrandbits(32)                                            # DIAGNOSTIC: unknown starting seed
    e.w32(SEED, s); e.w32(SEED2, s); S[0] = s
    events.append({'fight': 'jr', 'seed': s, 'step': VF[0]})
    until([13]); jw(rnd.randint(20, 60))
    # T1: Super Charge (target on Mario), Bombette Bomb (target on Jr. Troopa)
    jw(15, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); confirm_target('M', 'T1 Charge')
    until([14]); jw(10)
    jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); confirm_target('K', 'T1 Bomb')
    until([13, 14, 27, 32], mash=True); until([13], cap=4000); snap('t2_menu')
    # T2: wait in the menu for the lock (the runner watches the page), Z to Bombette, Bomb; Mario: Whacka's Bump
    n = wait_lock(); events.append({'t2_lock_wait': n, 'step': VF[0]}); print('  T2 lock after', n, 'frames', flush=True)
    jw(30, Z); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); confirm_target('K', 'T2 Bomb')
    until([13], cap=4000, mash=True); jw(15)
    jw(15, 0, 0, 70); jw(25, A); step(A)                  # items, A on the first item (Whacka's Bump)
    for i in range(60):
        if bstate(e) == 17: break
        step()
    events.append({'whacka_item': VF[0]}); confirm_target('M', 'T2 Whacka', fast=FAST)
    until([13], cap=4000); jw(20); snap('t3_menu')
    # T3: Super Charge; Bombette Bomb -> Close Call (planned)
    jw(12, 0, 0, -70); jw(22, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); confirm_target('M', 'T3 Charge')
    until([14]); jw(10)
    jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); h0 = hpd()
    confirm_target('K', 'T3 Bomb CC', planned=True)
    until([13, 14, 27, 32], cap=600, mash=True); cc_result('T3', h0); until([13], cap=4000); jw(20)
    # T4: Z to Bombette, Bomb; Mario: Maple Syrup (items, down 2) -> Close Call (planned)
    jw(30, Z); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); confirm_target('K', 'T4 Bomb')
    until([13], cap=4000, mash=True); jw(15)
    jw(15, 0, 0, 70); jw(25, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); h0 = hpd()
    confirm_target('M', 'T4 Syrup CC', planned=True); cc_result('T4', h0); until([13], cap=4000); jw(20)
    # T5: Super Charge; Bombette Strategies, do nothing -> Close Call (planned)
    jw(12, 0, 0, -70); jw(22, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); confirm_target('M', 'T5 Charge')
    until([14]); jw(10); jw(15, 0, 0, 70); jw(25, A); jw(12, 0, 0, -70); h0 = hpd()
    confirm_target('S', 'T5 Nothing CC', planned=True); cc_result('T5', h0); until([13], cap=4000); jw(20)
    # T6: Power Bounce (planned), A in every bounce window
    jw(22, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80)
    ev = confirm_target('K', 'T6 Bounce', planned=True)
    for f in range(1, 240): step(A if f in {47, 74, 102, 130, 158, 186, 214} else 0)
    jw(60); res = {'vf': VF[0], 'result': 'T6', 'hp': hpd(), 'six': hpd()['jr'] <= 0}; events.append(res); print('  RESULT', res, flush=True)
    jw(200)
if __name__ == '__main__': main()
