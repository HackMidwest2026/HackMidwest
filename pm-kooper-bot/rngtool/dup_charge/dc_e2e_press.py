"""Emulator check of a page plan (../test_dup_page.js): play the Duplighost T1 as rendered for the page (Mario's Super
Charge confirmed DELAY frames after the target screen opens, no popup A), Bombette: Strategies -> Do Nothing, and confirm
Do Nothing on the page's planned clock frame T (+ each OFFSET: a press a frame early / late). Clock frame 0 = the rays'
frame 0 = the Charge confirm + 13 (the first energy_in_out creation). Prints, per offset, the copy rolls (frame from
Do Nothing, value) and the copies (RandInt(1000) < 600), and the seed at clock frame 0 (the lock's truth).
Runs ../jr_charge/jc_probe.py (no screenshots) in the emulator dir (/tmp/claude-0/pm/bot1, debug core, M64P_DBG=1).
usage: python3 dc_e2e_press.py SEEDHEX DELAY T [OFFSETS=-1,0,1]
DIAGNOSTIC RAM write (in jc_probe): gRandSeed = SEEDHEX at the state load (stands for an unknown run)."""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
seed, delay, T = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
offs = [int(x) for x in (sys.argv[4] if len(sys.argv) > 4 else '-1,0,1').split(',')]
conf = 60 + 22 + 15 + 15 + 20 + delay          # the Charge confirm (log frame)
menu = conf + 154                               # Bombette's menu with no popup A, as dc_turns.py counts it (+154)
ready = menu + 10 + 15 + 25 + 12                # stick down, Strategies, stick up: the hand on Do Nothing
out = {}
for o in offs:
    X = conf + 13 + T + o
    if X < ready + 2: out[o] = {'error': 'Do Nothing frame %d before the hand is on it (%d)' % (X, ready + 2)}; continue
    inp = '60,22:A,15::0:-70,15::0:-70,20:A,%d,1:A,%d,15::0:70,25:A,12::0:-70,%d,1:A' % (delay, menu + 10 - conf - 1, X - ready)
    N = X + 13 + 97 * 3 + 40; log = '/dev/shm/dup/press_%s_%d_%d.json' % (seed, T, o)
    env = dict(os.environ, M64P_DBG='1', PYTHONPATH='.'); env.pop('M64P_GFX', None)
    r = subprocess.run(['python3', os.path.join(HERE, '..', 'jr_charge', 'jc_probe.py'), 'states/boss_2402_dchg_menu.st', seed, inp, str(N), log],
                       cwd='/tmp/claude-0/pm/bot1', env=env, capture_output=True, text=True)
    L = json.load(open(log)); os.remove(log)
    c = next(f for f, fr in enumerate(L) if any(x[0] == '0xe00d6160' for x in fr['calls']))
    dn = next((f for f in range(len(L)) if L[f]['in'][0] and f > ready - 3), None)
    rolls = [(f - X, x[2]) for f, fr in enumerate(L) for x in fr['calls'] if x[0] == '0x802d46e0']
    out[o] = {'creation': c, 'truth': '%08x' % L[c]['s0'], 'bs_menu': L[menu]['bs'], 'dn': X, 'dnInput': dn, 'rolls': rolls[:4], 'copies': sum(1 for f, v in rolls[:4] if v < 600)}
print(json.dumps(out))
