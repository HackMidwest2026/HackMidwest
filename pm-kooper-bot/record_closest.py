"""render the closest spin-jump landing attempt at the nok_14 north corner as png frames (real video plugin on Xvfb)."""
import os, subprocess, sys, json, math
os.environ.setdefault('ROOM', 'nok14')
from emu import Emu
from pm import *
from corner_sweep import stick_for

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/vid')
win = None

def grab(i):
    global win
    if win is None:
        ids = subprocess.run(['xdotool', 'search', '--name', 'Mupen64Plus'], capture_output=True, text=True).stdout.split()
        win = 'root'
    subprocess.run(['import', '-window', win, os.path.join(OUT, 'f%04d.png' % i)], check=True)

d = json.load(open('/tmp/claude-0/pm/runs/spinland_north/depth.json'))[0]
inp = d['pre']['inputs']
land_deg = d['info']['deg']
print('attempt', inp, 'landing stick', land_deg, 'recorded deepest x', d['x'])

e.load('states/nok14_start_goombario.st')
e.step(0, 0, 0, 2)
e.w8(game_status(e) + 0x74, 1)
sx0, sz0 = inp['start']
e.wf32(PLAYER + PS_POS, sx0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, sz0)
for i in range(6):
    e.step(0, 0, 0, 2)
# give the camera time to catch up after the teleport (mario stands still meanwhile)
for i in range(90):
    e.step(0, 0, 0, 2)
p = player(e)
print('start pos', round(p['x'], 2), round(p['z'], 2))

frames = []
stick = stick_for(inp['spin_deg'], 80)
stick_air = stick_for(inp['air_deg'], 80) if inp['air_deg'] is not None else (0, 0)
k, land_f = inp['jump_frame'], d['pre']['land_f']
seq = []
for f in range(10):                     # 1/3 s standing still before the spin
    seq.append((0, 0, 0, 'stand'))
for f in range(land_f):
    b = 0x20 if f == 0 else (0x80 if f == k else 0)
    st = stick if f <= k else stick_air
    seq.append((b, st[0], st[1], 'spin' if f < k else 'jump'))
ls = stick_for(land_deg, 80)
while len(seq) < 90:
    seq.append((0, ls[0], ls[1], 'land'))
log = []
px = None
for i, (b, x, y, tag) in enumerate(seq):
    e.step(b, x, y, 2)
    p = player(e)
    move = 0 if px is None else math.hypot(p['x'] - px[0], p['z'] - px[1])
    px = (p['x'], p['z'])
    log.append({'i': i, 'tag': tag, 'x': p['x'], 'z': p['z'], 'y': p['y'], 'move': move, 'action': p['action']})
    grab(i)
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
best = max((l for l in log if -100 < l['z'] < -20), key=lambda l: l['x'])
print('deepest x beside the wall in the video:', round(best['x'], 3), 'at frame', best['i'])
print('biggest one-frame move:', max(log, key=lambda l: l['move']))
