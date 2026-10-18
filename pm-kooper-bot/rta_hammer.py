"""Simple ending with a hammer at every angle change (RTA: the stick never passes through neutral there):
up 10, B + right (hammer, 10 frames frozen) then hold right into the corner, wait W, down D1, A + down N, release 4,
left until the forced drop, release 8, left T, release 2, hold up (slide into the step-2 corner); at frame h press B
with the final direction D held, keep holding D, C-down (still holding D) on frame c. Scans h and c.
usage: rta_hammer.py [START]"""
import os, sys
from rta_end5 import *
B = 0x40
def base(e, T, W=2, D1=4, N=22):
    e.load(os.environ.get('START', 'states/pra01_topright_pa160.st')); e.step(0, 0, 0, 2); fr = 0
    seq = [(0, U_)] * 10 + [(B, SD['R'])] + [(0, SD['R'])] * 14 + [(0, (0, 0))] * W + [(0, SD['D'])] * D1 + \
          [(0x80 if i < 12 else 0, SD['D']) for i in range(N)] + [(0, (0, 0))] * 4
    for b, s in seq: e.step(b, *s, 2); fr += 1
    while player(e)['action'] != 9: e.step(0, *SD['L'], 2); fr += 1
    for i in range(8): e.step(0, 0, 0, 2); fr += 1
    for i in range(T): e.step(0, *SD['L'], 2); fr += 1
    for i in range(2): e.step(0, 0, 0, 2); fr += 1
    return fr
if __name__ == '__main__':
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rh%d' % os.getpid())
    for T in (5, 6):
        fr0 = base(e, T); e.save('/dev/shm/pmbot/rh_b.st')
        for D in 'LD':
            for h in range(100, 128):
                row = []
                for c in range(h + 9, h + 15):
                    e.load('/dev/shm/pmbot/rh_b.st'); g = fr0
                    while g < h: e.step(0, *U_, 2); g += 1
                    e.step(B, *SD[D], 2); g += 1
                    while g < c: e.step(0, *SD[D], 2); g += 1
                    p = player(e); e.step(CD, *SD[D], 2); spd = laki(e)['speed']
                    if spd < 100: row.append('  .   '); continue
                    for i in range(60): e.step(0, 0, 0, 2)
                    row.append('%s%.1f' % ('Y' if player(e)['z'] > 1 else 'n', spd))
                if any(r.strip() != '.' for r in row):
                    print('T %d B+%s at %d, C-down at h+9..h+14: %s' % (T, D, h, ' '.join(row)), flush=True)
