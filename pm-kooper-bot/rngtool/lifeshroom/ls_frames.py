"""Render the T3 death + Life Shroom revive (from ls_sweep.py's start state) and save frames, with the coin draws
(0x80146d54) and whether each shone. DIAGNOSTIC: seed written at the start point.
usage: DISPLAY=:97 M64P_GFX=... M64P_DATA=... M64P_DBG=1 python3 ls_frames.py OUTDIR SEEDhex [EVERY]"""
import os, sys, json, subprocess
from PIL import Image
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True); SEED_ = int(sys.argv[2], 16); EVERY = int(sys.argv[3]) if len(sys.argv) > 3 else 6
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from btl import *; from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lf%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
e.load('/dev/shm/pmbot/ls_t3enemy.st'); e.step(0, 0, 0, 2); e.dbg_events()
e.w32(SEED, SEED_); e.w32(SEED2, SEED_); s = SEED_          # DIAGNOSTIC
log = []
def grab(n):
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '640x480!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    Image.frombytes('RGB', (640, 480), raw).save('%s/f%04d.png' % (OUT, n))
for n in range(700):
    prev = e.u32(SEED); e.step(0, 0, 0, 2); cur = e.u32(SEED)
    calls = []
    for ev in e.dbg_events():
        mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        s, v = rand_int(s, mx); calls.append([mx, v, ev['ra']])
    s = cur
    coin = [v for mx, v, ra in calls if ra == 0x80146d54]
    log.append([n, bstate(e), e.s8(PLAYER_DATA + 2), coin])
    if n % EVERY == 0 or coin: grab(n)
json.dump(log, open(OUT + '/log.json', 'w'))
