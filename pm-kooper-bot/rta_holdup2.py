"""Hold-up ending, one-run version: up 10, right 10 into the corner, release W, down D1 (no hammer near Laki),
A + down N, B+left (hammer), hold left through the forced drop onto step 3 and keep running left; at frame h press
B with up held (the hammer stops Mario), then hold up to the end; C-down (up still held) on frame c.
Scans N, h, c and prints every clip. usage: rta_holdup2.py [N ...]"""
import os, sys
from multiprocessing import Pool
from rta_end5 import *
B = 0x40
def route(e, N, st, W=2, D1=4):
    for i in range(10): st(0, U_, 'hold up')
    for i in range(10): st(0, SD['R'], 'hold right: very top-right corner')
    for i in range(W): st(0, (0, 0), 'release')
    for i in range(D1): st(0, SD['D'], 'hold down')
    for i in range(N): st(0x80 if i < 12 else 0, SD['D'], 'A + hold down: jump onto the top step, walk down')
    st(B, SD['L'], 'hammer (B) with left held')
    for i in range(9): st(0, SD['L'], 'hammer swing, holding left')
def job(N):
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rhv%d' % N)
    e.load(os.environ.get('START', 'states/pra01_topright_pa160.st')); e.step(0, 0, 0, 2)
    fr = [0]
    def st(b, s, tag=''): e.step(b, *s, 2); fr[0] += 1
    route(e, N, st)
    out = []
    # run left; at each frame where Mario is on step 3 with x in 878..892 try the stopping hammer there
    for k in range(60):
        st(0, SD['L']); p = player(e)
        if abs(p['y'] + 10) < 0.01 and 878 <= p['x'] <= 893 and p['action'] in (1, 2):
            h = fr[0]; e.save('/dev/shm/pmbot/rhv%d/h%d.st' % (N, h))
            for c in range(h + 12, h + 45):
                e.load('/dev/shm/pmbot/rhv%d/h%d.st' % (N, h)); g = h
                e.step(B, *U_, 2); g += 1
                while g < c: e.step(0, *U_, 2); g += 1
                q = player(e); e.step(CD, *U_, 2); spd = laki(e)['speed']
                if spd < 115.5 or q['action'] not in (0, 1, 2): continue
                for i in range(60): e.step(0, 0, 0, 2)
                out.append('N %d: B+up at frame %d (Mario x %.2f, z %.2f), C-down frame %d: speed %.2f at (%.2f, %.2f, %.2f) %s' % (N, h, p['x'], p['z'], c, spd, q['x'], q['y'], q['z'], 'CLIP' if player(e)['z'] > 1 else '-'))
            e.load('/dev/shm/pmbot/rhv%d/h%d.st' % (N, h))
        if p['x'] < 878: break
    return out or ['N %d: none' % N]
if __name__ == '__main__':
    Ns = [int(a) for a in sys.argv[1:]] or list(range(16, 46))
    with Pool(4, maxtasksperchild=1) as p:
        for o in p.imap(job, Ns):
            print('\n'.join(o), flush=True)
