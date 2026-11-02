"""Hallway Bowser T1 (Mario: Charge; Lakilester: Spiny Surge or Cloud Nine): same inputs, two seeds, screenshot
the partner move and diff, logging every rand_int (max, caller) per frame.
DIAGNOSTIC RAM write: gRandSeed set at Mario's first menu (both seed words), nothing else.
run from /tmp/claude-0/pm/bot1 (glide64mk2 for video, or no GFX for logs only):
  DISPLAY=:93 M64P_GFX=.../mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus M64P_DBG=1 \
  MOVE=surge|cloud PYTHONPATH=. python3 partner_moves_diff.py OUTDIR [SEEDA SEEDB]"""
import sys, os, json, subprocess, collections
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
from rngsim import *
OUT = sys.argv[1]; SA = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x12345678; SB = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x9ABCDEF1
MOVE = os.environ.get('MOVE', 'surge'); SHOTS = bool(os.environ.get('M64P_GFX'))
TAGS = os.environ.get('TAGS', 'ab')                      # e.g. TAGS=b to redo one seed
LO, HI = map(int, os.environ.get('SHOT_RANGE', '0,99999').split(','))   # screenshot only these frames (disk)
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pmd%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
def shot(p): subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', p], check=True)
res = {}
for tag, seed in [t for t in (('a', SA), ('b', SB)) if t[0] in TAGS]:
    e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2); e.dbg_events()
    e.w32(SEED, seed); e.w32(SEED2, seed)                    # DIAGNOSTIC
    log = []; fr = [0]; shoot = [False]
    def step(b=0, x=0, y=0):
        e.step(b, x, y, 2)
        log.append([(ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32), hex(ev['ra'])) for ev in e.dbg_events()
                    if ev['ra'] != 0x800269AC])
        if shoot[0] and SHOTS and LO <= fr[0] <= HI: shot('%s/%s%04d.png' % (OUT, tag, fr[0]))
        if shoot[0]: fr[0] += 1
    def w(n, b=0, x=0, y=0):
        for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
    def until(states, cap=4000):
        for f in range(cap):
            if bstate(e) in states: return f
            step()
        raise RuntimeError('state %d' % bstate(e))
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); w(20)   # Mario: Charge (as spinyflip_diff.py)
    step(A); until([14]); w(10)
    w(25, A)                                                          # Abilities
    w(12, 0, 0, -70)                                                  # down: Spiny Surge
    if MOVE == 'cloud': w(12, 0, 0, -70)                              # down: Cloud Nine
    if SHOTS: shot('%s/%s_menu.png' % (OUT, tag))
    i0 = len(log); shoot[0] = True
    w(25, A)                                                          # pick the move
    for k in range(6): step(A)                                        # confirm any target prompt
    if MOVE == 'surge':
        for f in range(170): step(0, -80 if (f // 3) % 2 == 0 else 0, 0)   # flick left / release (AC needs neutral between)
        for f in range(230): step()
    else:
        for f in range(420): step()
    shoot[0] = False
    res[tag] = log[i0:]
json.dump(res, open(OUT + '/log_%s.json' % TAGS, 'w'))
if TAGS != 'ab': sys.exit(0)
rows = []
if SHOTS:
    from PIL import Image, ImageChops
    nf = min(len(res['a']), len(res['b']))
    for f in range(nf):
        pa, pb = '%s/a%04d.png' % (OUT, f), '%s/b%04d.png' % (OUT, f)
        if not (os.path.exists(pa) and os.path.exists(pb)): continue
        d = ImageChops.difference(Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')).convert('L').point(lambda v: 255 if v > 24 else 0)
        bb = d.getbbox(); n = sum(1 for v in d.getdata() if v) if bb else 0
        rows.append((f, bb, n))
    json.dump(rows, open(OUT + '/diff.json', 'w'))
for tag in 'ab':
    c = collections.Counter(t for fr_ in res[tag] for t in fr_)
    print(tag, sum(c.values()), c.most_common(12))
for f in range(len(res['a'])):
    if res['a'][f]: print(f, collections.Counter(res['a'][f]).most_common(5), (rows[f][2] if f < len(rows) else ''))
