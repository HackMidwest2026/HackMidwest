"""(run from bot1/) Idle in the FB2 battle menu (or target screen) and log every non-step draw; screenshots on SHOTS frames.
usage: DISPLAY=:98 M64P_GFX=... M64P_DATA=... M64P_DBG=1 _fbmenu.py STATE N OUTDIR [shot frames comma]"""
import sys, os, subprocess, collections
from emu import *
from pm import *
from rngsim import *
st, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]; os.makedirs(OUT, exist_ok=True)
SH = set(int(x) for x in sys.argv[4].split(',')) if len(sys.argv) > 4 and sys.argv[4] else set()
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbm%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/' + st); e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
cnt = collections.Counter(); L = []; C = []; other = collections.Counter()
for f in range(N):
    e.step(0, 0, 0, 2)
    for x in e.dbg_events():
        ra = x['ra']; cnt[hex(ra)] += 1
        if ra == 0xE00BC194: L.append(f)
        elif ra == 0x80146D54: C.append(f)
        elif ra != 0x800269AC: other[(hex(ra), x['a0'])] += 1
    if f in SH: subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '%s/f%05d.png' % (OUT, f)], check=True)
print('counts', dict(cnt)); print('other', dict(other))
print('LIGHT', L); print('COIN', C[:20])
