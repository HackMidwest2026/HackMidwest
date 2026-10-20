"""dgb_01 (intact): push Lakilester far from a frozen ("stale") history target, as in the reverse mirror clip, and
measure the remount speed it gives.
1. Mario stands at START with Laki settled; wiggle up/down at low tilt until the 40-entry move history is full (Laki
   stays idle in follow state 5, so the pointer stops and its entry, the target, is frozen near START).
2. Stop-and-go push aimed at Laki (go 1 frame, stop 2), steered toward GOAL; a cycle is kept only while the follow
   state stays 5 and the pointer and target are unchanged. Reports d = distance Laki -> frozen target.
3. Release from the push end: walk at angle REL (or toward START when unset) and press C-down on frame f (1..70);
   the mount speed is Laki's moveSpeed when the mount reads it. Reports the best f and speed.
usage: dgb01_push.py STATE START_X START_Z GOAL_X GOAL_Z [OUT.st]   env: REL (angle), MAXC (push cycles)"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_place import place
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0 = sys.argv[1]; SX, SZ, GX, GZ = (float(v) for v in sys.argv[2:6]); OUT = sys.argv[6] if len(sys.argv) > 6 else None
MAXC = int(os.environ.get('MAXC', '600'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/dpu%d' % os.getpid())
tmp = '/dev/shm/pmbot/dpu%d' % os.getpid()
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load(st0); e.step(0, 0, 0, 2); place(e, SX, SZ, y=0.0)
for i in range(60): e.step(0, 0, 0, 2)
# 1. fill the history ring with small wiggles while Laki idles
for k in range(400):
    e.step(0, *stick_for(90 if k % 2 == 0 else 270, 25), 2)
    if e.u32(IDX) == (e.u32(PTR) - 1) % 40: break
for i in range(10): e.step(0, 0, 0, 2)
ptr0 = e.u32(PTR); st = e.u32(STATE) >> 16
tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
p, l = player(e), laki()
print('ring full after %d wiggle frames: idx %d ptr %d state %d, frozen target (%.1f, %.1f); Mario (%.1f, %.1f) Laki (%.1f, %.1f)' % (k + 1, e.u32(IDX), ptr0, st, tx, tz, p['x'], p['z'], l['x'], l['z']), flush=True)
def intact(): return e.u32(PTR) == ptr0 and (e.u32(STATE) >> 16) == 5 and e.f32(HIST + 16 * ptr0 + 4) == tx and e.f32(HIST + 16 * ptr0 + 12) == tz
# 2. push
e.save(tmp + '.good'); best_d = 0; cyc = 0
for cyc in range(MAXC):
    p, l = player(e), laki()
    cur = math.atan2(l['z'] - p['z'], l['x'] - p['x']); want = math.atan2(GZ - l['z'], GX - l['x'])
    dth = (want - cur + math.pi) % (2 * math.pi) - math.pi
    aim = math.degrees(cur + max(-0.7, min(0.7, 0.8 * dth)))
    e.step(0, *stick_for(aim % 360, 80), 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    if not intact():
        print('push broke at cycle %d' % cyc); e.load(tmp + '.good'); break
    l = laki(); d = math.hypot(l['x'] - tx, l['z'] - tz)
    e.save(tmp + '.good')
    if cyc % 40 == 0: print('  cycle %d Laki (%.0f, %.0f) d %.1f' % (cyc, l['x'], l['z'], d), flush=True)
    if math.hypot(GX - l['x'], GZ - l['z']) < 25: break
p, l = player(e), laki(); d = math.hypot(l['x'] - tx, l['z'] - tz)
print('push end after %d cycles: Mario (%.1f, %.1f) Laki (%.1f, %.1f), d = %.1f -> speed cap about %.0f' % (cyc, p['x'], p['z'], l['x'], l['z'], d, 0.25 * d), flush=True)
if OUT:
    e.step(0, 0, 0, 2); e.save(OUT)        # a save right after another save (or a load) fails without a frame between
# 3. release
e.save(tmp + '.end')
REL = float(os.environ['REL']) if os.environ.get('REL') else math.degrees(math.atan2(tz - p['z'], tx - p['x']))
best = (0, None, None)
for f in range(1, 71):
    e.load(tmp + '.end')
    for i in range(f - 1): e.step(0, *stick_for(REL % 360, 80), 2)
    e.step(0x400, *stick_for(REL % 360, 80), 2)
    a = laki()['addr']
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: break
        e.step(0, 0, 0, 2)
    S = e.f32(a + 0x18); q = player(e)
    if S > best[0]: best = (S, f, (q['x'], q['z']))
print('release walking at %.0f deg: best mount speed %.1f with C-down on frame %s, Mario at %s' % (REL % 360, best[0], best[1], best[2]))
