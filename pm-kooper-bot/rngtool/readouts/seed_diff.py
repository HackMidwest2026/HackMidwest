"""Find RNG-driven visuals: run the same inputs from one savestate with two different seeds and diff the frames.
Also logs every rand_int caller (ra) per frame and the RNG steps per frame.
DIAGNOSTIC RAM write: gRandSeed is overwritten right after the state load (setup only).
run from /tmp/claude-0/pm/bot1:
  DISPLAY=:88 M64P_GFX=/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus \
  M64P_DBG=1 PYTHONPATH=. python3 seed_diff.py STATE N OUTDIR "f:btn[:x:y],..." [SEED_A SEED_B] [SHOT_EVERY]"""
import sys, os, subprocess, collections, json
sys.path.insert(0, os.getcwd())
from emu import *
from rngsim import *
from PIL import Image, ImageChops
st, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
inp = {}
for tok in (sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] else []):
    p = tok.split(':'); f = int(p[0]); inp[f] = (eval(p[1]), int(p[2]) if len(p) > 2 else 0, int(p[3]) if len(p) > 3 else 0)
SA = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0x12345678
SB = int(sys.argv[6], 16) if len(sys.argv) > 6 else 0x9ABCDEF1
EVERY = int(sys.argv[7]) if len(sys.argv) > 7 else 1
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rd%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
def shot(path):
    subprocess.run(['import', '-window', 'root', '-crop', '640x456+80+60', '+repage', path], check=True)
log = {}
for tag, seed in (('a', SA), ('b', SB)):
    e.load('states/' + st if not st.startswith('/') else st); e.step(0, 0, 0, 2); e.dbg_events()
    e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC
    rows = []
    for f in range(N):
        b, x, y = inp.get(f, (0, 0, 0))
        prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
        k = 0; t = prev
        while t != cur and k < 20000: t = adv(t); k += 1
        ev = e.dbg_events()
        rows.append((k, collections.Counter(hex(v['ra']) for v in ev)))
        if f % EVERY == 0: shot('%s/%s%05d.png' % (OUT, tag, f))
    log[tag] = rows
# per-frame summary of callers (seed a) and image diffs
callers = collections.Counter(); steps = collections.Counter()
for k, c in log['a']: callers.update(c); steps[k] += 1
print('steps/frame histogram (a):', dict(sorted(steps.items())[:20]))
print('callers (a) total over', N, 'frames:', dict(callers))
diffs = []
for f in range(0, N, EVERY):
    A = Image.open('%s/a%05d.png' % (OUT, f)).convert('RGB'); B = Image.open('%s/b%05d.png' % (OUT, f)).convert('RGB')
    d = ImageChops.difference(A, B).convert('L').point(lambda v: 255 if v > 24 else 0)
    bb = d.getbbox(); n = sum(1 for v in d.getdata() if v) if bb else 0
    diffs.append((f, bb, n))
json.dump({'diffs': diffs, 'steps_a': [r[0] for r in log['a']], 'callers_a': [dict(r[1]) for r in log['a']],
           'callers_b': [dict(r[1]) for r in log['b']]}, open(OUT + '/summary.json', 'w'))
agg = collections.Counter()
for f, bb, n in diffs:
    if bb: agg[(bb[0] // 40 * 40, bb[1] // 40 * 40, bb[2] // 40 * 40, bb[3] // 40 * 40)] += 1
print('frames with diff:', sum(1 for d in diffs if d[1]), 'of', len(diffs))
print('diff bbox clusters (40px grid):', agg.most_common(12))
