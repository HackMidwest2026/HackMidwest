"""replay one mirror_local hit and print Mario / Lakilester every frame, through the mount."""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
h = json.load(open(sys.argv[1]))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/trm')
e.load('states/pra02_leftpillar.st')
for c in range(250):
    if player(e)['x'] >= h['start']: break
    e.step(0, 80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
e.step(0, 0, 0, 2)


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


def show(f, tag, st):
    p, l = player(e), laki()
    print('%3d %-5s stick %-10s mario %7.2f %6.2f %7.2f act %2d  laki %7.2f %6.2f %7.2f spd %6.2f' % (
        f, tag, st, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], l['speed']))


show(-1, 'start', '')
seq = h['seq']
for f, (sx, sy) in enumerate(seq):
    last = f == len(seq) - 1
    e.step(CD if last else 0, sx, sy, 2)
    show(f, 'CDOWN' if last else '', (sx, sy))
for i in range(25):
    e.step(0, 0, 0, 2)
    show(len(seq) + i, 'mount', '')
