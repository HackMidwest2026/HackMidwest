"""Video of the hammer version of the simple ending (rta_hammer2.route): hammer (B with the new direction held) at
every 90-degree stick change, final up -> down flick (G neutral frames, P frames of down) with C-down on frame c,
then 70 frames of the mount. Screenshots every frame to OUT/f%04d.png (run with the video plugin and DISPLAY) and
writes OUT/log.json for make_video.py. usage: record_rta_hammer.py OUT [T c G P]"""
import json, os, subprocess, sys
from rta_hammer2 import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
T, c, G, P = (int(a) for a in sys.argv[2:6]) if len(sys.argv) > 5 else (5, 138, 2, 1)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rrh')
log = []
def rec(b, s, tag):
    p, l = player(e), laki(e); ptr = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'act': p['action']})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
def st(b, s, tag):
    e.step(b, *s, 2); rec(b, s, tag)
fr = route(e, T, 22, 4, 10, 1, 1, rec)
while fr < c - P - G: st(0, U_, 'hold up: slide down the riser into the step-2 corner, wait for Laki'); fr += 1
for i in range(G): st(0, (0, 0), 'flick the stick from up to down (passes through neutral)'); fr += 1
for i in range(P): st(0, SD['D'], 'down'); fr += 1
st(CD, SD['D'], 'C-down on the spike frame (holding down): Laki speed %.2f')
log[-1]['tag'] = log[-1]['tag'] % log[-1]['ls']
ok = log[-1]['ls'] >= 115.75
for i in range(70): st(0, (0, 0), 'mount -> FRONT side of the mirror' if ok else 'mount: not enough speed')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), 'frames; C-down speed %.2f; end Mario (%.1f, %.1f, %.1f)' % ([l['ls'] for l in log if l['tag'].startswith('C-down')][0], log[-1]['x'], log[-1]['y'], log[-1]['z']))
