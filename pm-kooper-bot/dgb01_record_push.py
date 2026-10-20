"""Record the dgb_01 push + release that gives the highest remount speed (for a video): Laki settled at START, wiggle
until the history ring is full (target frozen), stop-and-go push aimed at Laki steered toward GOAL for NC cycles, then
walk at angle REL and press C-down on release frame F. SHOT=1 screenshots every frame (Xvfb :99 + video plugin).
Writes OUT/log.json (tag, input, Mario/Laki state, Laki speed, distance to the frozen target).
usage: dgb01_record_push.py STATE OUT [START_X START_Z GOAL_X GOAL_Z NC REL F]"""
import json, math, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_place import place
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0, OUT = sys.argv[1], sys.argv[2]
SX, SZ, GX, GZ, NC, REL, F = ([float(v) for v in sys.argv[3:7]] + [int(sys.argv[7]), float(sys.argv[8]), int(sys.argv[9])]) if len(sys.argv) > 9 else (250., 420., 250., -500., 500, 180., 20)
os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/drp%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
log = []; T = [None, None]
def st(b, s, tag, inp):
    e.step(b, *s, 2)
    p, l = player(e), laki()
    d = math.hypot(l['x'] - T[0], l['z'] - T[1]) if T[0] is not None else 0
    log.append({'i': len(log), 'tag': tag, 'inp': inp, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'act': p['action'], 'lx': l['x'], 'lz': l['z'],
                'ls': l['speed'], 'st': e.u16(STATE), 'd': d, 'in': False})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
e.load(st0); e.step(0, 0, 0, 2); place(e, SX, SZ, y=0.0)
for i in range(60): st(0, (0, 0), 'stand: Laki settles next to Mario', '')
k = 0
while k < 400:
    st(0, stick_for(90 if k % 2 == 0 else 270, 25), 'wiggle up/down (small tilt) until the 40-entry history ring is full', 'wiggle')
    k += 1
    if e.u32(IDX) == (e.u32(PTR) - 1) % 40: break
ptr0 = e.u32(PTR); T[0], T[1] = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
for i in range(10): st(0, (0, 0), 'ring full: Laki\'s target is frozen at (%.0f, %.0f)' % tuple(T), '')
for c in range(NC):
    p, l = player(e), laki()
    cur = math.atan2(l['z'] - p['z'], l['x'] - p['x']); want = math.atan2(GZ - l['z'], GX - l['x'])
    dth = (want - cur + math.pi) % (2 * math.pi) - math.pi
    aim = math.degrees(cur + max(-0.7, min(0.7, 0.8 * dth)))
    tag = 'stop-and-go push (go 1, stop 2): Laki stays idle, his target stays frozen'
    st(0, stick_for(aim % 360, 80), tag, 'push')
    st(0, (0, 0), tag, ''); st(0, (0, 0), tag, '')
for i in range(F - 1): st(0, stick_for(REL % 360, 80), 'release: walk away, Laki rushes back toward the frozen target', 'LEFT  frame %d' % (i + 1))
st(0x400, stick_for(REL % 360, 80), 'C-down on release frame %d' % F, 'C-DOWN + LEFT  frame %d' % F)
a = laki()['addr']
for i in range(20):
    st(0, (0, 0), 'mount: speed frozen at %.1f' % e.f32(a + 0x18), '')
for i in range(40): st(0, (0, 0), 'ride Laki', '')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
cd = [l for l in log if l['inp'].startswith('C-DOWN')][-1]
print(len(log), 'frames; push end d %.1f; speed at C-down %.1f; mount speed %.1f' % (log[-1]['d'], cd['ls'], e.f32(a + 0x18)))
