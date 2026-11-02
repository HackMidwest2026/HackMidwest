"""kzn_03 (Mt. Lava Lava, Save Block room, 3 Spike Tops + Putrid Piranha + Kolorado): log every rand_int call by caller
while Mario stands still in the field, then while the pause menu (stats tab) is open. Each call is replayed from the frame's start
seed, as in pause_coins.py. Run once per seed (one emulator per process) to see how the field draws vary with the seed.
DIAGNOSTIC RAM write: gRandSeed set after the state load (setup only).
run from /tmp/claude-0/pm/bot1 with M64P_DBG=1. usage: kzn03_draws.py STATE FIELD_FRAMES PAUSE_FRAMES SEEDhex"""
import sys, os, json, collections
sys.path.insert(0, os.getcwd())
from emu import *
from rngsim import *
st, NF, NP = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
COIN = {0x80146d54: 'coin', 0x800269ac: 'frame-step'}   # HUD coin rand_int(100) (status bar / stats tab) and the per-frame rand_int(1)
out = {}
for sh in sys.argv[4:5]:
    seed = int(sh, 16)
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/kd%d' % os.getpid())
    for i in range(60): e.step(0, 0, 0, 2)
    e.bp_add(RAND_INT); e.dbg_log(1)
    e.load('states/' + st); e.step(0, 0, 0, 2); e.dbg_events()
    e.w32(SEED, seed); e.w32(SEED2, seed)                        # DIAGNOSTIC
    rows = []; bad = 0
    for f in range(NF + NP):
        prev = e.u32(SEED); e.step(START if f == NF else 0, 0, 0, 2); cur = e.u32(SEED)
        s = prev; calls = []
        for v in e.dbg_events():
            mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
            s2, r = rand_int(s, mx); n = 0; t = s
            while t != s2: t = adv(t); n += 1
            calls.append((v['ra'], mx, r, n)); s = s2
        k = 0; t = s
        while t != cur and k < 100: t = adv(t); k += 1      # steps not from rand_int (the per-frame advance_rng)
        rows.append((f, calls, k))
    def summary(lo, hi):
        by = collections.Counter(); steps = collections.Counter(); ev = collections.Counter()
        for f, calls, k in rows[lo:hi]:
            for ra, mx, r, n in calls:
                name = COIN.get(ra, '%08x' % ra); by[name] += 1; steps[name] += n; ev[(name, mx)] += 1
            steps['frame step'] += k
        return {'frames': hi - lo, 'calls': dict(by), 'steps': dict(steps), 'by_max': {'%s/%d' % x: c for x, c in ev.items()}}
    fld = summary(0, NF); pause_open = summary(NF, NF + 40); paused = summary(NF + 40, NF + NP)
    # field: steps from non-coin callers in each 60-frame window (variability)
    win = []
    for w in range(0, NF, 60):
        win.append(sum(n for f, calls, k in rows[w:w + 60] for ra, mx, r, n in calls if ra not in COIN))
    ev_frames = [(f, '%08x' % ra, mx) for f, calls, k in rows[:NF] for ra, mx, r, n in calls if ra not in COIN]
    out[sh] = {'enemy_calls': ev_frames, 'field': fld, 'pause_first40': pause_open, 'paused': paused, 'field_noncoin_steps_per_60f': win}
    print(sh, json.dumps({k: v for k, v in out[sh].items() if k != 'enemy_calls'}), flush=True)
    print('  enemy call frames:', [x[0] for x in ev_frames], flush=True)
json.dump(out, open('/dev/shm/pmbot/kzn03_draws_%s.json' % sys.argv[4], 'w'))
