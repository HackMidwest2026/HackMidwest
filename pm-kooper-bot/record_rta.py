"""Video of the best simple-input (cardinal only) ending: from the top-right corner state, up 10, right 10, down 6,
A + down 26, left until the forced drop onto step 3 (released during it), left T, stand, hold up from frame X (Mario
slides down the riser into the corner at z -145), C-down with D on frame c, then 70 frames of the mount. Saves one
state per frame into OUT for render_states.py plus OUT/log.json. With SHOT=1 (run with the video plugin and DISPLAY), screenshot each frame
to OUT/f%04d.png during the continuous replay instead, so animations use the real inputs.
usage: record_rta.py OUT [T X c D]"""
import json, os, subprocess, sys
from rta_end2 import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
T, X, c, D = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]) if len(sys.argv) > 5 else (5, 103, 121, 'U')
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rrta')
log = []
def step(b, s, tag):
    e.step(b, *s, 2)
    p, l = player(e), laki(e); ptr = e.u32(PTR)
    log.append({'i': len(log), 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'ls': l['speed'], 'lx': l['x'], 'ly': l['y'], 'lz': l['z'],
                'st': e.u32(STATE) >> 16, 'ptr': ptr, 'tx': e.f32(HIST + 16 * ptr + 4), 'tz': e.f32(HIST + 16 * ptr + 12), 'act': p['action']})
    if os.environ.get('SHOT'):
        subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (len(log) - 1))], check=True)
    else:
        e.save(os.path.join(OUT, 's%04d.st' % (len(log) - 1)))
e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); step(0, (0, 0), 'start: Laki in the top-right corner, stale target at the rock')
for i in range(10): step(0, U_, 'hold up')
for i in range(10): step(0, SD['R'], 'hold right: very top-right corner (987, -212)')
for i in range(6): step(0, SD['D'], 'hold down')
for i in range(26): step(0x80 if i < 12 else 0, SD['D'], 'A + hold down: jump onto the top step, walk down')
for i in range(4): step(0, (0, 0), 'release')
while player(e)['action'] != 9: step(0, SD['L'], 'hold left')
for i in range(8): step(0, (0, 0), 'release during the forced drop: always lands at x 911.9 on step 3')
for i in range(T): step(0, SD['L'], 'left %d frames (x 889.1)' % T)
for i in range(2): step(0, (0, 0), 'stand on step 3, wait for Laki')
while len(log) - 1 < X: step(0, (0, 0), 'stand on step 3, wait for Laki')
while len(log) - 1 < c: step(0, U_, 'hold up: slide down the riser into the step-2 corner (884.3, -145)')
step(CD, SD[D], 'C-down on the spike frame: Laki speed %.2f (needs 115.75)')
log[-1]['tag'] = log[-1]['tag'] % log[-1]['ls']
for i in range(70): step(0, (0, 0), 'mount: not enough speed, Mario stays behind the mirror')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print(len(log), log[-1]['tag'], [round(log[-1][k], 1) for k in ('x', 'y', 'z')], 'C-down speed', [l['ls'] for l in log if l['tag'].startswith('C-down')])
