"""Replay a rev_strip_refine hit from START (pre + tail up to frame k, then C-down with the next stick) and follow the
mount for 60 frames: prints Mario's position each few frames, map, action, and whether he ends on the real side.
usage: verify_hit.py <hits.json> [index]"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
h = json.load(open(sys.argv[1]))[int(sys.argv[2]) if len(sys.argv) > 2 else 0]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/vh')
e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); e.step(0, 0, 0, 2)
for b, sx, sy in h['pre']: e.step(b, sx, sy, 2)
for b, sx, sy in h['tail'][:h['k'] + 1]: e.step(b, sx, sy, 2)
p = player(e); print('before C-down: Mario (%.1f, %.1f, %.1f) act %d' % (p['x'], p['y'], p['z'], p['action']))
nx = h['tail'][h['k'] + 1] if h['k'] + 1 < len(h['tail']) else (0, 0, 0)
e.step(CD, nx[1], nx[2], 2)
for i in range(60):
    l = [n for n in npcs(e) if n['id'] == -4][0]
    if i < 6 or i % 6 == 0:
        p = player(e); print(i, 'Mario (%.1f, %.1f, %.1f) act %d  Laki speed %.1f  map %s' % (p['x'], p['y'], p['z'], p['action'], l['speed'], where(e)[:2]))
    e.step(0, 0, 0, 2)
p = player(e)
print('END Mario (%.1f, %.1f, %.1f) act %d map %s -> %s' % (p['x'], p['y'], p['z'], p['action'], where(e)[:2], 'REAL SIDE (clipped)' if p['z'] > 1 else 'still behind the mirror'))
