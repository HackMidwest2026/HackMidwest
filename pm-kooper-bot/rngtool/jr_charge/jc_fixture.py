"""Cases for the page's Jr. Troopa test (../test_jr_plan.js), from the emulator-checked model (jc_model.py; jc_check.py and
jc_check_core.js: every frame of 64 Charge segments). Per case: a random gRandSeed and coin phase at the T1 Charge confirm
(log frame 0), the route's confirm frames with the spacing of the emulator runs plus a random delay on each (T1 Bomb,
T2 Bomb, T2 Whacka, T3 Charge, ...), and for each lever the outcome of confirming it on every log frame of its window:
  T3 Bomb, T4 Maple Syrup, T5 Do Nothing: Close Call ('1' dodge, '0' hit), with every earlier lever on its first dodging
  frame (the route's outcome); T6 Power Bounce: '6' (6+ bounces), '5', '4' (fewer).
Per window also the true state (seed before frame F, next coin frame) on F = 46 frames before it, where the test plans.
Also: what each Charge lock gives the page (the seed and first coin at the rays' frame 0 = confirm + 13), and every coin
draw's frame and whether it shines (for the menus' coin).
usage: python3 jc_fixture.py N OUT.json [seed]"""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import jc_model as JM
N, OUT = int(sys.argv[1]), sys.argv[2]
rnd = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 73)
# spacing (log frames between confirms) as in the emulator runs (jc_render.py, 25 frames on each screen) minus 25, so the
# random delay 0..40 brings it around that
GAP = {'T1 Bomb': 224, 'T2 Bomb': 373, 'T2 Whacka': 240, 'T3 Charge': 351, 'T4 Bomb': 280, 'T5 Charge': 270}
WIN = {'T3 Bomb': (150, 190), 'T4 Syrup': (190, 190), 'T5 Nothing': (120, 190), 'T6 Bounce': (150, 190)}   # (start after the previous confirm, length)
TURN = {'T1 Charge': 'charge', 'T1 Bomb': 'bomb_t1', 'T2 Bomb': 'bomb', 'T2 Whacka': 'whacka', 'T3 Charge': 'charge', 'T3 Bomb': 'bomb_cc',
        'T4 Bomb': 'bomb', 'T4 Syrup': 'syrup_cc', 'T5 Charge': 'charge', 'T5 Nothing': 'nothing_cc', 'T6 Bounce': 'pb'}
def lock_at(m0, c):
    """the Charge lock at confirm c: the seed and the first coin frame (relative) at frame 0 = c + 13"""
    m = m0.copy(); m.run(c, c + 13); return {'seed': '%08x' % m.s, 'q': m.nc - (c + 13)}
def outcome(mD, D, name):
    """mD: the model at the start of frame D (the lever not added yet)"""
    m = mD.copy(); m.add(D, TURN[name]); m.run(D, D + 181)
    if name == 'T6 Bounce': return str(min(6, JM.pb_hits(m.rolls)))
    return '1' if m.rolls['cc'] < 30 else '0'
SEQ = ['T1 Bomb', 'T2 Bomb', 'T2 Whacka', 'T3 Charge', 'T3 Bomb', 'T4 Bomb', 'T4 Syrup', 'T5 Charge', 'T5 Nothing', 'T6 Bounce']
cases = []; tries = 0
while len(cases) < N:
    tries += 1
    s0 = rnd.getrandbits(32); nc0 = rnd.randrange(0, 48)
    m = JM.Sim(s0, nc0); m.add(0, 'charge'); cur = 0; C = {'T1 Charge': 0}; locks = {'T1': lock_at(m, 0)}
    t = 0; ok = True; wins = {}
    for name in SEQ:
        if name in GAP: t += GAP[name] + rnd.randint(0, 40)
        if name in WIN:
            a, n = WIN[name]; a += t
            pl = m.copy(); pl.run(cur, a - 46)        # the true state where the page plans (the screen 46 frames before the window)
            base = m.copy(); base.run(cur, a); cls = ''
            for D in range(a, a + n): cls += outcome(base, D, name); base.frame(D)
            wins[name] = {'from': a, 'cls': cls, 'state': {'s': '%08x' % pl.s, 'nc': pl.nc, 'F': a - 46}}
            if name == 'T6 Bounce': break
            D = next((a + i for i in range(20, n) if cls[i] == '1'), None)   # the route's outcome: the first dodge 20+ frames in
            if D is None: ok = False; break
            t = D
        m.run(cur, t); cur = t; C[name] = t; m.add(t, TURN[name])
        if name.endswith('Charge'): locks[name[:2]] = lock_at(m, t)
    if not ok: continue
    # the coin: every draw (log frame, roll) from the T1 Charge to the end of the T6 window
    mc = JM.Sim(s0, nc0)
    for name, f in C.items(): mc.add(f, TURN[name])
    end = wins['T6 Bounce']['from'] + 190; mc.run(0, end)
    cases.append({'s0': '%08x' % s0, 'nc0': nc0, 'confirms': C, 'locks': locks, 'wins': wins, 'shines': [f for f, v in mc.coins if v >= 70], 'end': end})
json.dump({'clock0': 13, 'cases': cases}, open(OUT, 'w'))
print(len(cases), 'cases ->', OUT, '(%d tried)' % tries)
