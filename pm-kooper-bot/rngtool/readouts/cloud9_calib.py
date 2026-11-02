"""Cloud Nine puff calibration (Hallway Bowser state, same inputs as partner_moves_diff.py MOVE=cloud): for each seed,
record gRandSeed at the end of every frame and screenshot frames LO..HI, so each puff's (RandInt(40), RandInt(30)) is
known exactly and its on-screen birth position can be measured.
DIAGNOSTIC RAM write: gRandSeed set at Mario's first menu (both seed words), nothing else.
run from /tmp/claude-0/pm/bot1:
  DISPLAY=:77 M64P_GFX=.../mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus M64P_DBG=1 \
  PYTHONPATH=. python3 cloud9_calib.py OUTDIR SEED [SEED...]"""
import sys, os, json, subprocess
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
from rngsim import *
OUT = sys.argv[1]; SEEDS = [int(s, 16) for s in sys.argv[2:]]
LO, HI = map(int, os.environ.get('SHOT_RANGE', '224,262').split(','))
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/c9%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
def shot(p): subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', p], check=True)
res = {}
for seed in SEEDS:
    tag = '%08x' % seed
    e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2); e.dbg_events()
    e.w32(SEED, seed); e.w32(SEED2, seed)                    # DIAGNOSTIC
    log = []; seeds = []; fr = [0]; shoot = [False]
    def step(b=0, x=0, y=0):
        e.step(b, x, y, 2)
        log.append([(ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32), hex(ev['ra'])) for ev in e.dbg_events()
                    if ev['ra'] != 0x800269AC])
        seeds.append(e.u32(SEED))
        if shoot[0] and LO <= fr[0] <= HI: shot('%s/%s_%04d.png' % (OUT, tag, fr[0]))
        if shoot[0]: fr[0] += 1
    def w(n, b=0, x=0, y=0):
        for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
    def until(states, cap=4000):
        for f in range(cap):
            if bstate(e) in states: return f
            step()
        raise RuntimeError('state %d' % bstate(e))
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); w(20)
    step(A); until([14]); w(10)
    w(25, A); w(12, 0, 0, -70); w(12, 0, 0, -70)
    i0 = len(log); shoot[0] = True
    w(25, A)
    for k in range(6): step(A)
    for f in range(HI + 5 - 31): step()
    res[tag] = dict(log=log[i0:], seed=seeds[i0:], seed_before=seeds[i0 - 1])
    json.dump(res, open(OUT + '/calib.json', 'w'))
    print(tag, 'done', flush=True)
