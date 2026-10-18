"""Video of the best pra_02 back-side attempt (what-if): states/pra02_wi_farleft.st (frozen target at the far left,
Laki placed idle at the right pillar in RAM), hold right N1 frames then down, C-down on frame C, then 70 frames.
SHOT=1 screenshots every frame (video plugin + DISPLAY); writes OUT/log.json for make_video.py.
usage: record_pra02_best.py OUT [N1 C]"""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x400
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
N1, C = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (16, 24)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rp2b')
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
log = []
def st(b, s, tag):
    e.step(b, *s, 2)
    p, l = player(e), laki(); ptr = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'act': p['action']})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
e.load('states/pra02_wi_farleft.st')
st(0, (0, 0), 'what-if: Laki idle at the right pillar, frozen target at the far left (x 49)')
for f in range(C):
    st(0, stick_for(0, 80) if f < N1 else stick_for(90, 80), ('hold right %d frames' % N1) if f < N1 else 'hold down: Laki flies back to his target and turns around')
st(CD, stick_for(90, 80), 'C-down on the spike frame: Laki speed %.2f (needs 240 here)')
log[-1]['tag'] = log[-1]['tag'] % log[-1]['ls']
for i in range(70): st(0, (0, 0), 'mount: stays behind the mirror (no clip)' if True else '')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), 'frames; C-down speed %.2f; end Mario (%.1f, %.1f, %.1f)' % ([l['ls'] for l in log if l['tag'].startswith('C-down')][0], log[-1]['x'], log[-1]['y'], log[-1]['z']))
