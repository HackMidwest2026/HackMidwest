"""pra_02 REVERSE MIRROR CLIP with real inputs (no RAM edits), from states/pra02_back_left.st:
1. Corner approach: walk to (130,-80), wait 30, hold UP-LEFT 70 frames into the back-left corner, wait 40. Lakilester
   ends facing 315, so his own wall check keeps him 18 units off the back wall and the push carries him past both pillars.
2. Push him east (Mario kept 4 units behind) until he reaches the right wall.
3. Run 10 frames toward the switch block, then chain short jumps (A held 5 frames) aimed at (865,-90) until Mario
   stands on the block (y 15). While Mario is in the air above Lakilester his speed stays capped. On the block the
   return spike (~240) lands on a frame where Mario is already standing, so C-down starts the mount with that speed.
4. C-down on that frame (f37 after the push): Mario rides through the mirror to the front side (z > 1).
The block top needs a speed of 220 (see pra02_clip_map.html). usage: pra02_block_clip.py [press_frame]"""
import sys, math
from emu import *
from pm import *
e = None
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
spd = lambda: e.f32(laki()['addr'] + 0x18)
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
def pstep(gap):
    p = player(e); l = laki(); tx, tz = l['x'] - gap, l['z']
    d = math.hypot(tx - p['x'], tz - p['z'])
    s_ = st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
    e.step(0, *s_, 2)
def go(tx, tz, maxf=250, tol=0.5):
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < tol: return
        mag = max(14, min(80, int(d * 10)))
        e.step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)), 2)
def route(press=37, k=10, ha=5, tgt=(865, -90), log=print):
    e.load('states/pra02_back_left.st'); e.step(0, 0, 0, 2)
    go(130, -80)
    for i in range(30): e.step(0, 0, 0, 2)
    for i in range(70): e.step(0, -56, 56, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    l = laki(); go(l['x'] - 4, l['z'], 80, 0.3)
    for f in range(1500):
        pstep(4)
        if laki()['x'] > 975: break
    p = player(e); log('push end f%d: Mario (%.1f, %.1f), Laki (%.1f, %.1f)' % (f, p['x'], p['z'], laki()['x'], laki()['z']))
    jt = None; onblk = None
    for f in range(press + 1):
        p = player(e); grounded = p['action'] in (0, 1, 2)
        if grounded and p['y'] > 14 and onblk is None: onblk = f; log('f%d on the switch block (%.1f, %.1f, %.1f)' % (f, p['x'], p['y'], p['z']))
        dx, dz = tgt[0] - p['x'], tgt[1] - p['z']; d = math.hypot(dx, dz)
        stick = (0, 0) if (onblk is not None or d < 3) else (int(80 * dx / d), int(-80 * dz / d))
        b = 0
        if onblk is None and f >= k:
            if jt is None and grounded: jt = 0
            if jt is not None:
                b = A if jt < ha else 0; jt += 1
                if jt > 4 and grounded: jt = None
        if f == press: b = D_CBUTTON
        e.step(b, *stick, 2)
    log('f%d C-down: Laki speed %.1f' % (press, spd()))
    for i in range(40): e.step(0, 0, 0, 2)
    p = player(e); log('after the mount: Mario (%.1f, %.1f, %.1f) action %d room %s -> %s' % (p['x'], p['y'], p['z'], p['action'], where(e)[:2], 'CLIP (front side)' if p['z'] > 1 else 'no clip'))
    return p['z'] > 1
if __name__ == '__main__':
    e = Emu('pm-jp.z64', '/dev/shm/pmbot/bc')
    route(int(sys.argv[1]) if len(sys.argv) > 1 else 37)
