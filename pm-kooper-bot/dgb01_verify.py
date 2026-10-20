"""dgb_01: verify mount-map hits with the full mount. Mario placed at (x, 0, z), Laki's speed forced to S until the
mount reads it, then the mount plays out (40 frames); reports Mario's final position and whether he is out of bounds.
usage: dgb01_verify.py STATE 'x,z,S' ..."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/dvf%d' % os.getpid())
e.load(sys.argv[1]); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/dvf%d.st' % os.getpid(); e.save(base)
for spec in sys.argv[2:]:
    x, z, S = (float(v) for v in spec.split(','))
    e.load(base)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    for i in range(3): e.step(0, 0, 0, 2)
    a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
    e.wf32(a + 0x18, S); e.step(0x400, 0, 0, 2)
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: break
        e.wf32(a + 0x18, S); e.step(0, 0, 0, 2)
    t = (e.f32(a + 0x60), e.f32(a + 0x68))
    for i in range(40): e.step(0, 0, 0, 2)
    p = player(e)
    out = abs(p['x']) > 500 or abs(p['z']) > 500
    print('spot (%g, %g) S %g: target (%.0f, %.0f) -> Mario (%.1f, %.1f, %.1f) %s' % (x, z, S, t[0], t[1], p['x'], p['y'], p['z'], 'OUT OF BOUNDS' if out else 'inside'), flush=True)
