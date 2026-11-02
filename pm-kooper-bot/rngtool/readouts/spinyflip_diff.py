"""Hallway Bowser T1 (Charge; Lakilester Spiny Flip): same inputs, two seeds, screenshot the Spiny Flip and diff,
logging every rand_int (caller, max) per frame. DIAGNOSTIC RAM write: gRandSeed set at Mario's first menu.
run from /tmp/claude-0/pm/bot1 (glide64mk2 for video):
  DISPLAY=:93 M64P_GFX=.../mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus M64P_DBG=1 \
  PYTHONPATH=. python3 spinyflip_diff.py OUTDIR [SEEDA SEEDB]"""
import sys, os, json, subprocess, collections
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
from rngsim import *
from PIL import Image, ImageChops
OUT = sys.argv[1]; SA = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x12345678; SB = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x9ABCDEF1
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sfd%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
def shot(p): subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', p], check=True)
res = {}
for tag, seed in (('a', SA), ('b', SB)):
    e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2); e.dbg_events()
    e.w32(SEED, seed); e.w32(SEED2, seed)                    # DIAGNOSTIC
    log = []; fr = [0]; shoot = [False]
    def step(b=0, x=0, y=0):
        e.step(b, x, y, 2)
        log.append([(ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32), hex(ev['ra'])) for ev in e.dbg_events()
                    if ev['ra'] != 0x800269AC])
        if shoot[0]: shot('%s/%s%04d.png' % (OUT, tag, fr[0])); fr[0] += 1
    def w(n, b=0, x=0, y=0):
        for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
    def until(states, cap=4000):
        for f in range(cap):
            if bstate(e) in states: return f
            step()
        raise RuntimeError('state %d' % bstate(e))
    CH = os.environ.get('SHOOT') == 'charge'
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); w(20)
    if CH:                                          # SHOOT=charge: screenshot Mario's Charge instead
        i0 = len(log); shoot[0] = True; step(A)
        for f in range(80): step()
        shoot[0] = False
    else:
        step(A); until([14]); w(10)
        w(25, A); w(25, A); until([17], cap=80); w(20)
        i0 = len(log); shoot[0] = True; step(A)
        for f in range(44): step()
        for f in range(12): step(0, 70, 0)
        for f in range(150): step()
        shoot[0] = False
    res[tag] = log[i0:]
nf = min(len(res['a']), len(res['b']))
rows = []
for f in range(0, nf):
    pa, pb = '%s/a%04d.png' % (OUT, f), '%s/b%04d.png' % (OUT, f)
    if not (os.path.exists(pa) and os.path.exists(pb)): continue
    d = ImageChops.difference(Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')).convert('L').point(lambda v: 255 if v > 24 else 0)
    bb = d.getbbox(); n = sum(1 for v in d.getdata() if v) if bb else 0
    rows.append((f, bb, n, [t for t in res['a'][f]], [t for t in res['b'][f]]))
json.dump(rows, open(OUT + '/diff.json', 'w'))
for f, bb, n, la, lb in rows:
    if bb or la: print(f, bb, n, collections.Counter(la).most_common(4))
