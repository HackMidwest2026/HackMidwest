"""Collect per-frame draw logs for T6 (Super Charge confirm -> popup dismissed with A at confirm+K -> Bowser's turn ->
T7 menu -> 20 idle frames -> Power Bounce menu inputs, target-screen A after D more idle frames), for fitting / checking t6model.py.
DIAGNOSTIC: gRandSeed written at the T6 menu (setup only).  Run from bot1 with M64P_DBG=1:
  PYTHONPATH=. python3 t6_collect.py BUILD SEEDS KS DS OUT.json [STATE=t6_menu.st]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route import *
from t6_study import bowser_turn

build, seeds, Ks, Ds, out = sys.argv[1], [int(x, 16) for x in sys.argv[2].split(',')], \
    [int(x) for x in sys.argv[3].split(',')], [int(x) for x in sys.argv[4].split(',')] if sys.argv[4] != '-' else [], sys.argv[5]
state = sys.argv[6] if len(sys.argv) > 6 else 't6_menu.st'
r = Run('tc'); runs = []
for sd in seeds:
    for K in Ks:
        r.load(build + '/' + state); r.seed(sd)                  # DIAGNOSTIC: gRandSeed at the T6 menu
        r.charge(0, wheel=-2, sub=2); c0 = r.marks['charge']
        bowser_turn(r, 'at:%d' % K if K >= 0 else 'none', c0)
        menu = r.f
        r.idle(20)                     # the menu ignores inputs for a few frames after opening
        hp = r.e.s8(PLAYER_DATA + 2)
        tmp = '/dev/shm/fb2r/tc_%d.st' % os.getpid(); r.e.save(tmp)
        base = [dict(f=x['f'] - c0, s0=x['s0'], d=x['d'], bs=x['bs']) for x in r.rows[c0:]]
        pbs = []
        for D in Ds:
            r.load(tmp); r.power_bounce(D, wheel=0, sub=1); dc = r.marks['pb']
            for i in range(27 * 14 + 100):
                k = r.f - dc; r.step(A if k >= 44 and (k - 44) % 27 == 0 else 0)
            pbs.append(dict(D=D, dconf=dc, rows=[dict(f=x['f'], s0=x['s0'], d=x['d']) for x in r.rows], bowser=r.bowser_hp()))
        runs.append(dict(seed='%08x' % sd, K=K, c0=c0, menu=menu - c0, pbbase=menu - c0 + 20, hp=hp, rows=base, pb=pbs))
        print('%08x K %d menu +%d hp %d' % (sd, K, menu - c0, hp), flush=True)
json.dump(runs, open(out, 'w'))
