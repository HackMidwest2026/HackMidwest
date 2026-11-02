"""Pause screen (Mario/stats tab): log every rand_int call with its roll value (replayed from the frame's start seed),
and screenshot the stats-tab coin every frame to see which rolls show as shines.
DIAGNOSTIC RAM write: gRandSeed set after the state load (setup only).
run from /tmp/claude-0/pm/bot1 with DISPLAY/M64P_GFX/M64P_DATA/M64P_DBG=1 (see seed_diff.py).
usage: pause_coins.py STATE SEEDhex N OUTDIR [START_FRAME] [SHOTS:0/1]"""
import sys, os, subprocess, json
sys.path.insert(0, os.getcwd())
from emu import *
from rngsim import *
st, seed, N, OUT = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), sys.argv[4]
SF = int(sys.argv[5]) if len(sys.argv) > 5 else 10
SHOTS = int(sys.argv[6]) if len(sys.argv) > 6 else 1
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pc%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
e.load('states/' + st); e.step(0, 0, 0, 2); e.dbg_events()
e.w32(SEED, seed); e.w32(SEED2, seed)                          # DIAGNOSTIC
rows = []
for f in range(N):
    prev = e.u32(SEED); e.step(START if f == SF else 0, 0, 0, 2); cur = e.u32(SEED)
    ev = e.dbg_events(); s = prev; calls = []
    for v in ev:
        mx = v['a0'] if v['a0'] < 0x80000000 else v['a0'] - (1 << 32)
        s2, r = rand_int(s, mx); calls.append((hex(v['ra']), mx, r)); s = s2
    rows.append({'f': f, 'ok': s == cur, 'calls': calls})
    if SHOTS and f > SF + 15:
        subprocess.run(['import', '-window', 'root', '-crop', '32x32+394+332', '+repage', '%s/c%05d.png' % (OUT, f)], check=True)
json.dump(rows, open(OUT + '/rows.json', 'w'))
bad = [r['f'] for r in rows if not r['ok']]
coin = [(r['f'], c[2]) for r in rows for c in r['calls'] if c[0] == '0x80146d54']
other = sorted({(c[0], c[1]) for r in rows for c in r['calls'] if c[0] not in ('0x80146d54', '0x800269ac')})
print('replay mismatches:', bad[:10], 'coin draws:', len(coin), 'other callers:', other)
print('coin draws (frame, roll):', coin[:60])
