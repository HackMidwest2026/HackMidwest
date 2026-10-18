"""Video of the hold-up ending (rta_holdup.route, T frames of left), stand until X, hold up continuously, C-down
(up still held) on frame c, then 70 frames of the mount. Screenshots every frame to OUT/f%04d.png (video plugin +
DISPLAY) and writes OUT/log.json for make_video.py. usage: record_rta_holdup.py OUT [T X c]"""
import json, os, subprocess, sys
from rta_holdup import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
T, X, c = (int(a) for a in sys.argv[2:5]) if len(sys.argv) > 4 else (5, 114, 128)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rrhu')
log = []
def st(b, s, tag=''):
    e.step(b, *s, 2)
    p, l = player(e), laki(e); ptr = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'act': p['action']})
    if os.environ.get('SHOT'): subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
e.load(os.environ.get('START', 'states/pra01_topright_pa160.st')); e.step(0, 0, 0, 2)
route(e, T, st)
while len(log) < X: st(0, (0, 0), 'stand on step 3 (x 889.2), wait for Laki')
while len(log) < c: st(0, U_, 'hold up: walk into the wall, slide down the riser onto step 2')
st(CD, U_, 'C-down (still holding up) the frame after Mario lands: Laki speed %.2f')
log[-1]['tag'] = log[-1]['tag'] % log[-1]['ls']
ok = log[-1]['ls'] >= 115.75
for i in range(70): st(0, U_ if i < 3 else (0, 0), 'mount -> FRONT side of the mirror' if ok else 'mount: not enough speed')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), 'frames; C-down speed %.2f; end Mario (%.1f, %.1f, %.1f)' % ([l['ls'] for l in log if l['tag'].startswith('C-down')][0], log[-1]['x'], log[-1]['y'], log[-1]['z']))
