"""Video frames of the natural Lakilester stuck/drift trigger (same inputs as laki_ptr0.py): walk right K, stand 40,
wiggle up/down WIG, stand 5, walk left A, stand STAND. SHOT=1 screenshots every frame; writes OUT/log.json.
usage: record_laki_stuck.py STATE OUT K WIG A STAND [MOVE]
MOVE=1 then walks around after the stand to show Laki following again."""
import json, math, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0, OUT = sys.argv[1], sys.argv[2]; K, WIG, A, STAND = map(int, sys.argv[3:7])
os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rls%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
log = []
def st(s, tag):
    e.step(0, *s, 2)
    p, l = player(e), laki(); ptr = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'z': p['z'], 'lx': l['x'], 'lz': l['z'], 'ls': l['speed'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'idx': e.u32(IDX), 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12),
                'hist': [(e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12)) for k in range(40)]})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
e.load(st0); e.step(0, 0, 0, 2)
up, dn = stick_for(270, 30), stick_for(90, 30)
for i in range(K): st(stick_for(0, 80), 'walk right %d frames' % K)
for i in range(40): st((0, 0), 'stand: Laki goes idle')
for f in range(WIG): st(up if f % 2 == 0 else dn, 'wiggle up/down %d frames: history keeps recording until the 40-slot ring is full' % WIG)
for i in range(5): st((0, 0), 'stand')
for i in range(A): st(stick_for(180, 80), 'walk left %d frames, stop just outside the tether radius' % A)
for i in range(STAND): st((0, 0), 'stand still (no input)')
if len(sys.argv) > 7 and sys.argv[7] == '1':
    for d, n, nm in ((180, 20, 'left'), (None, 50, ''), (270, 20, 'up'), (None, 50, ''), (0, 35, 'right'), (None, 50, ''), (90, 20, 'down'), (None, 70, '')):
        for i in range(n): st(stick_for(d, 80) if d is not None else (0, 0), ('after the glitch: walk %s' % nm) if d is not None else 'stand: Laki caught up and idles normally')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), 'frames; end state %d ptr %d idx %d' % (log[-1]['st'], log[-1]['ptr'], log[-1]['idx']))
