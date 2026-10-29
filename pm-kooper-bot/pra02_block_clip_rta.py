"""pra_02 REVERSE MIRROR CLIP, RTA-oriented version of pra02_block_clip.py (real inputs, no RAM edits).
From states/pra02_back_left.st:
1. Corner approach (as before): walk to (130,-80), wait 30, hold UP-LEFT 70 frames into the back-left corner, wait 40.
2. Push Lakilester east along the back wall and stop once he is past x 930 (Mario ~926). Stopping anywhere from
   Laki x 915 to 935 works.
3. Hold the stick at one fixed angle, 55 degrees below straight left (stick (-46, -66)); 55-65 all work.
   - Full jump (just hold A; any hold of 6+ frames is the same full jump) on any of frames 2-8 after the push stops
     (measured: 2-8 clip, 0-1 miss the block, 9+ spends too long on the floor).
   - When Mario lands on the floor, stay on the floor for exactly 4 frames, then a SHORT hop: A held exactly 5 frames.
     (A full jump here cannot work: its last height before landing on the block is 16.3, below Laki's 20.5, so his
     speed spikes one frame before Mario lands; the 5-frame hop's last height is 21.0.)
   - Mario lands on the switch block; press C-down on the first frame he stands there. Laki's speed is ~240 that
     frame (the block top needs 220) and the mount carries Mario through the mirror.
Why it works: Laki only races back along Mario's trail on frames where Mario is lower than him (on the floor); while
Mario is in the air above him his speed is capped at 6. The total floor time after he leaves hover has to be exact,
which is why the 4-frame floor pause is fixed while a first jump made before he leaves hover (frame ~8) is free.
usage: pra02_block_clip_rta.py [first_jump_frame] [push_stop_x] [stick_angle]"""
import sys, math
from emu import *
from pm import *
import pra02_block_clip as BC
e = None
def go(*a, **k): return BC.go(*a, **k)
def route(first=3, stop=930, ang=55, pause=4, log=print):
    BC.e = e
    e.load('states/pra02_back_left.st'); e.step(0, 0, 0, 2)
    go(130, -80)
    for i in range(30): e.step(0, 0, 0, 2)
    for i in range(70): e.step(0, -56, 56, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    l = BC.laki(); go(l['x'] - 4, l['z'], 80, 0.3)
    for f in range(1500):
        BC.pstep(4)
        if BC.laki()['x'] > stop: break
    p = player(e); log('push end f%d: Mario (%.1f, %.1f), Laki (%.1f, %.1f)' % (f, p['x'], p['z'], BC.laki()['x'], BC.laki()['z']))
    stick = (int(round(-80 * math.cos(math.radians(ang)))), int(round(-80 * math.sin(math.radians(ang)))))
    jt = None; hops = 0; land = None
    for f in range(120):
        p = player(e); grounded = p['action'] in (0, 1, 2)
        if grounded and p['y'] > 14:
            log('f%d on the switch block (%.1f, %.1f, %.1f)' % (f, p['x'], p['y'], p['z']))
            e.step(D_CBUTTON, *stick, 2); log('f%d C-down: Laki speed %.1f' % (f, BC.spd())); break
        if grounded and hops == 1 and land is None and jt is None: land = f; log('f%d landed on the floor' % f)
        b = 0
        start = (hops == 0 and f >= first) or (hops == 1 and land is not None and f >= land + pause)
        if jt is None and grounded and start: jt = 0; hops += 1; log('f%d %s' % (f, 'full jump' if hops == 1 else 'short hop (A held 5)'))
        if jt is not None:
            b = A if jt < (5 if hops == 2 else 8) else 0; jt += 1
            if jt > 4 and grounded: jt = None
        e.step(b, *stick, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    p = player(e); ok = p['z'] > 1
    log('after the mount: Mario (%.1f, %.1f, %.1f) action %d -> %s' % (p['x'], p['y'], p['z'], p['action'], 'CLIP (front side)' if ok else 'no clip'))
    return ok
if __name__ == '__main__':
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/bcr')
    a = [int(x) for x in sys.argv[1:]]
    route(*a)
