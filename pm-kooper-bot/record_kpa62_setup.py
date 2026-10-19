"""Record a kpa_62 cardinal-only setup run for a video. Mario is placed with Laki settled (kpa62_place), then the
program runs: segments 'dir:frames' or 'wait:frames' (neutral), then mount (C-down), ride RIDE frames, B, hold down,
C-down on frame T after the B, hold down 30 more, stand 40. SHOT=1 screenshots every frame (Xvfb :99 + video plugin).
Writes OUT/log.json with per-frame tag, input, Mario/Laki state.
usage: record_kpa62_setup.py STATE OUT 'up:120 wait:10 right:30 wait:20 left:12 wait:20 down:12 wait:40' [T=34] [RIDE=40]"""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_place import place
from kpa62_tower import inside_tower
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80), 'wait': (0, 0)}
st0, OUT, PROG = sys.argv[1], sys.argv[2], sys.argv[3]
T = int(sys.argv[4]) if len(sys.argv) > 4 else 34; RIDE = int(sys.argv[5]) if len(sys.argv) > 5 else 40
os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rks%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
log = []
def st(b, s, tag, inp):
    e.step(b, *s, 2)
    p, l = player(e), laki()
    log.append({'i': len(log), 'tag': tag, 'inp': inp, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'act': p['action'],
                'lx': l['x'], 'ly': l['y'], 'lz': l['z'], 'ls': l['speed'], 'st': e.u16(0x8010D188), 'in': inside_tower(p['x'], p['z'])})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
e.load(st0); e.step(0, 0, 0, 2); place(e, -480.0, -100.0)
for seg in PROG.split():
    d, k = seg.split(':'); k = int(k)
    for i in range(k):
        st(0, CARD[d], ('hold %s (%d frames)' % (d.upper(), k)) if d != 'wait' else 'stand', ('%s %d/%d' % (d.upper(), i + 1, k)) if d != 'wait' else '')
st(0x400, (0, 0), 'C-down: mount Laki', 'C-DOWN')
for i in range(RIDE): st(0, (0, 0), 'ride Laki', '')
st(0x40, (0, 0), 'B: dismount (frame 0)', 'B  (frame 0)')
dn = CARD['down']
for fr in range(1, T): st(0, dn, 'hold DOWN, count frames after B', 'DOWN  frame %d' % fr)
st(0x400, dn, 'C-down on frame %d after B (+ DOWN)' % T, 'C-DOWN + DOWN  frame %d' % T)
for i in range(30): st(0, dn, 'remount: Laki carries Mario into the tower', 'DOWN')
for i in range(40): st(0, (0, 0), 'inside the tower' if log[-1]['in'] else 'end', '')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
q = log[-1]; print(len(log), 'frames; end (%.1f %.1f %.1f) inside=%s' % (q['x'], q['y'], q['z'], q['in']))
